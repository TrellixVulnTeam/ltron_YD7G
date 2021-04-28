import math

import renderpy.contexts.egl as drpy_egl
import renderpy.contexts.glut as drpy_glut
from renderpy.core import Renderpy
import renderpy.camera as camera
import renderpy.masks as masks
import renderpy.assets as drpy_assets

import ltron.settings as settings

default_projection = camera.projection_matrix(
    math.radians(60.),
    aspect_ratio=1.,
    near_clip=10,
    far_clip=50000,
)

default_asset_paths = '%s:%s'%(
    settings.paths['renderpy_assets_cfg'],
    drpy_assets.default_assets_path,
)

class RenderEnvironment:
    
    # initialization ===========================================================
    
    def __init__(self,
        asset_paths=default_asset_paths,
        opengl_mode='egl',
        egl_device=None,
        window_width=128,
        window_height=128,
        window_visible=True,
        window_anti_alias=True,
        window_anti_alias_samples=8,
        load_scene=None,
    ):
        if opengl_mode == 'egl':
            drpy_egl.initialize_plugin()
            drpy_egl.initialize_device(device=egl_device)
        
        elif opengl_mode == 'glut':
            drpy_glut.initialize()
            self.window = drpy_glut.GlutWindowWrapper(
                    'LTRON',
                    width = window_width,
                    height = window_height,
                    anti_alias = window_anti_alias,
                    anti_alias_samples = window_anti_alias_samples)
            if window_visible:
                self.window.show_window()
            else:
                self.window.hide_window()
        else:
            raise Exception(
                    'Unknown opengl_mode: %s (expected "egl" or "glut")')
        
        self.renderer = Renderpy(
                asset_paths,
                default_camera_projection=default_projection,
        )
        self.load_scene = load_scene
        if self.load_scene is not None:
            self.renderer.load_scene(self.load_scene)
        self.make_snap_materials()
    
    # materials ================================================================
    
    def make_snap_materials(self):
        self.renderer.load_material(
                'snap+',
                flat_color = (0, 0, 1),
                ambient = 1.0,
                metal = 0.0,
                rough = 0.0,
                base_reflect = 0.0)
        self.renderer.load_material(
                'snap-',
                flat_color = (1, 0, 0),
                ambient = 1.0,
                metal = 0.0,
                rough = 0.0,
                base_reflect = 0.0)
    
    def load_color_material(self, color):
        if not self.renderer.material_exists(color.material_name):
            self.renderer.load_material(
                color.material_name,
                **color.renderpy_material_args(),
            )
    
    def clear_materials(self):
        self.renderer.clear_materials()
        self.make_snap_materials()
    
    # meshes ===================================================================
    
    def load_brick_mesh(self, brick_type):
        if not self.renderer.mesh_exists(brick_type.mesh_name):
            self.renderer.load_mesh(
                brick_type.mesh_name,
                **brick_type.renderpy_mesh_args(),
            )    
    
    # instances ================================================================
    
    def add_instance(self, brick_instance):
        # load mesh if necessary
        self.load_brick_mesh(brick_instance.brick_type)
        
        # load the color material if necessary
        self.load_color_material(brick_instance.color)
        
        # add the renderpy instance
        self.renderer.add_instance(
            brick_instance.instance_name,
            **brick_instance.renderpy_instance_args(),
        )
        
        # add the snap instances
        for i, snap in enumerate(brick_instance.get_snaps()):
            self.add_snap_instance(brick_instance.instance_id, i, snap)
    
    def add_snap_instance(self, instance_id, snap_id, snap):
        # create the mesh if it doesn't exist
        if not self.renderer.mesh_exists(snap.subtype_id):
            self.renderer.load_mesh(
                snap.subtype_id,
                mesh_data=snap.get_snap_mesh(),
                color_mode='flat_color',
            )
        
        # add the renderpy instance
        snap_name = '%s_%i'%(instance_id, snap_id)
        self.renderer.add_instance(
            snap_name,
            mesh_name=snap.subtype_id,
            material_name='snap%s'%snap.polarity,
            transform=snap.transform,
            mask_color=(0,0,0),
            hidden=True,
        )
    
    def remove_instance(self, brick_instance):
        # remove the instance
        instance_name = brick_instance.instance_id
        self.renderer.remove_instance(str(instance_name))
        
        # remove all snap instances
        for i, snap in enumerate(brick_instance.get_snaps()):
            self.renderer.remove_instance('%s_%i'%(instance_name, i))
    
    def update_instance(self, brick_instance):
        self.renderer.set_instance_transform(
            str(brick_instance.instance_id),
            brick_instance.transform,
        )
        self.renderer.set_instance_material(
            str(brick_instance.instance_id),
            brick_instance.color.material_name,
        )
        self.renderer.set_instance_mesh(
            str(brick_instance.instance_id),
            brick_instance.brick_type.mesh_name,
        )
        for i, snap in enumerate(brick_instance.get_snaps()):
            self.renderer.set_instance_transform(
                '%s_%i'%(brick_instance.instance_id, i),
                snap.transform,
            )
    
    def instance_hidden(self, brick_instance):
        return self.renderer.instance_hidden(str(brick_instance))
    
    def get_all_brick_instances(self):
        return [
            instance for instance in self.renderer.list_instances()
            if '_' not in instance
        ]
    
    def get_all_snap_instances(self):
        return [
            instance for instance in self.renderer.list_instances()
            if '_' in instance
        ]
    
    def hide_all_brick_instances(self):
        brick_instances = self.get_all_brick_instances()
        for brick_instance in brick_instances:
            self.renderer.hide_instance(brick_instance)
    
    def show_all_brick_instances(self):
        brick_instances = self.get_all_brick_instances()
        for brick_instance in brick_instances:
            self.renderer.show_instance(brick_instance)
    
    def hide_all_snap_instances(self):
        snap_instances = self.get_all_snap_instances()
        for snap_instance in snap_instances:
            self.renderer.hide_instance(snap_instance)
    
    def show_all_snap_instances(self):
        snap_instances = self.get_all_snap_instances()
        for snap_instance in snap_instances:
            self.renderer.show_instance(snap_instance)
    
    def hide_snap_instance(self, instance_id, snap_id):
        snap_name = '%s_%i'%(instance_id, snap_id)
        self.hide_instance(snap_name)
    
    def show_snap_instance(self, instance_id, snap_id):
        snap_name = '%s_%i'%(instance_id, snap_id)
    
    def __getattr__(self, attr):
        try:
            return getattr(self.renderer, attr)
        except AttributeError:
            raise AttributeError(
                "'{}' object has no attribute '{}'".format(
                    type(self).__name__, attr
                )
            )