import math

import numpy

from scipy.ndimage import binary_erosion

from splendor.frame_buffer import FrameBufferWrapper
from splendor.camera import orthographic_matrix
from splendor.image import save_image, save_depth
from splendor.masks import color_byte_to_index

from ltron.geometry.utils import unscale_transform, default_allclose

from ltron.exceptions import ThisShouldNeverHappen

PIXELS_PER_LDU = 1.

def make_collision_frame_buffer(resolution):
    frame_buffer = FrameBufferWrapper(
        resolution[0],
        resolution[1],
        anti_alias=False,
    )
    
    return frame_buffer

class CollisionChecker:
    def __init__(
        self,
        scene,
        #resolution=(128,128),
        max_intersection=1, #=4
    ):
        self.scene = scene
        #self.frame_buffer = make_collision_frame_buffer(resolution)
        self.frame_buffers = {}
        self.max_intersection = max_intersection
    
    def check_collision(
        self,
        target_instances,
        render_transform,
        scene_instances=None,
        **kwargs,
    ):
        return check_collision(
            self.scene,
            target_instances,
            render_transform,
            frame_buffers=self.frame_buffers,
            update_frame_buffers=True,
            max_intersection=self.max_intersection,
            **kwargs,
        )
    
    def check_snap_collision(
        self,
        target_instances,
        snap,
        **kwargs,
    ):
        return check_snap_collision(
            self.scene,
            target_instances,
            snap,
            frame_buffers=self.frame_buffers,
            update_frame_buffers=True,
            max_intersection=self.max_intersection,
            **kwargs,
        )

def check_snap_collision(
    scene,
    target_instances,
    snap,
    *args,
    return_colliding_instances=False,
    **kwargs,
):
    
    if return_colliding_instances:
        min_num_collisions = float('inf')
        min_collision = None
    for render_transform in snap.collision_direction_transforms:
        collision = check_collision(
            scene,
            target_instances,
            render_transform,
            *args,
            return_colliding_instances=return_colliding_instances,
            **kwargs,
        )
        if not collision:
            return collision
        elif return_colliding_instances:
            num_collision = len(collision)
            if num_collision < min_num_collisions:
                min_num_collisions = num_collision
                min_collision = collision
    
    if return_colliding_instances:
        return min_collision
    else:
        return True
    
    '''
    if return_colliding_instances:
        all_collisions = [
            check_collision(
                scene,
                target_instances,
                render_transform,
                *args,
                return_colliding_instances=return_colliding_instances,
                **kwargs,
            )
            for render_transform in snap.collision_direction_transforms
        ]
        len_collisions = [(len(c), c) for c in all_collisions]
        return min(len_collisions)[1]
    
    else:
        collision = all(
            check_collision(
                scene,
                target_instances,
                render_transform,
                *args,
                return_colliding_instances=return_colliding_instances,
                **kwargs,
            )
            for render_transform in snap.collision_direction_transforms
        )
    
    return collision
    '''

def check_collision(
    scene,
    target_instances,
    render_transform,
    scene_instances=None,
    frame_buffers=None,
    update_frame_buffers=False,
    max_intersection=1, #=4
    erosion=1,
    required_clearance=24,
    tolerance_spacing=8,
    dump_images=None,
    return_colliding_instances=False,
):
    
    # setup ====================================================================
    # make sure the scene is renderable
    assert scene.renderable
    
    # get a list of the names of the target and scene instances
    target_instance_names = set(
        str(target_instance) for target_instance in target_instances)
    if scene_instances is None:
        scene_instance_names = set(
            scene.get_all_brick_instances()) - target_instance_names
    else:
        scene_instance_names = set(
            str(scene_instance) for scene_instance in scene_instances)
    
    # initialize frame_buffers if necessary
    if frame_buffers is None:
        frame_buffers = {}
    
    # store the camera info and which bricks are hidden
    original_view_matrix = scene.get_view_matrix()
    original_projection = scene.get_projection()
    
    # render the scene depth map ===============================================
    # setup the camera
    camera_transform = unscale_transform(render_transform)
    render_axis = camera_transform[:3,2]
    
    # compute the extents of the tarrget instance in camera space
    local_target_vertices = []
    inv_camera_transform = numpy.linalg.inv(camera_transform)
    for target_instance in target_instances:
        vertices = target_instance.brick_shape.bbox_vertices
        transform = inv_camera_transform @ target_instance.transform
        local_target_vertices.append(transform @ vertices)
    local_target_vertices = numpy.concatenate(local_target_vertices, axis=1)
    box_min = numpy.min(local_target_vertices, axis=1)
    box_max = numpy.max(local_target_vertices, axis=1)
    width = box_max[0] - box_min[0]
    height = box_max[1] - box_min[1]
    max_dim = max(width, height)
    thickness = box_max[2] - box_min[2]
    
    # compute clipping
    camera_distance = thickness + required_clearance + 2 * tolerance_spacing
    near_clip = 1 * tolerance_spacing
    far_clip = thickness * 2 + required_clearance + 3 * tolerance_spacing
    
    # compute orthographic bounds
    required_resolution = max_dim * PIXELS_PER_LDU
    required_power = math.ceil(math.log(required_resolution, 2))
    resolution = 2**required_power
    if resolution in frame_buffers:
        frame_buffer = frame_buffers[resolution]
    else:
        frame_buffer = make_collision_frame_buffer((resolution, resolution))
        if update_frame_buffers:
            frame_buffers[resolution] = frame_buffer
    extra_width = (resolution - (width * PIXELS_PER_LDU)) / PIXELS_PER_LDU
    extra_height = (resolution - (height * PIXELS_PER_LDU)) / PIXELS_PER_LDU
    l = box_max[0] + extra_width
    r = box_min[0]
    b = -(box_max[1] + extra_height)
    t = - box_min[1]
    
    # build the camera transform and orthographic projection
    camera_transform[:3,3] += render_axis * camera_distance
    scene.set_view_matrix(numpy.linalg.inv(camera_transform))
    orthographic_projection = orthographic_matrix(
        l=l, r=r, b=b, t=t, n=near_clip, f=far_clip)
    scene.set_projection(orthographic_projection)
    
    # render
    frame_buffer.enable()
    scene.mask_render(instances=scene_instance_names, ignore_hidden=True)
    if dump_images or return_colliding_instances:
        scene_mask = frame_buffer.read_pixels()
    scene_depth_map = frame_buffer.read_pixels(
            read_depth=True, projection=orthographic_projection)
    
    # render the target depth map ==============================================
    # setup the camera
    camera_transform = unscale_transform(render_transform)
    camera_transform[:3,3] -= render_axis * camera_distance
    axis_flip = numpy.array([
        [ 1, 0, 0, 0],
        [ 0, 1, 0, 0],
        [ 0, 0,-1, 0],
        [ 0, 0, 0, 1]
    ])
    camera_transform = numpy.dot(camera_transform, axis_flip)
    scene.set_view_matrix(numpy.linalg.inv(camera_transform))
    scene.set_projection(orthographic_projection)
    
    # render -------------------------------------------------------------------
    frame_buffer.enable()
    scene.mask_render(instances=target_instance_names, ignore_hidden=True)
    target_mask = frame_buffer.read_pixels()
    target_depth_map = frame_buffer.read_pixels(
            read_depth=True, projection=orthographic_projection)
    
    # restore the previous camera ==============================================
    scene.set_view_matrix(original_view_matrix)
    scene.set_projection(original_projection)
    
    # check collision ==========================================================
    valid_pixels = numpy.sum(target_mask != 0, axis=-1) != 0
    
    scene_depth_map -= camera_distance
    scene_depth_map *= -1.
    target_depth_map -= camera_distance
    offset = (scene_depth_map - target_depth_map).reshape(valid_pixels.shape)
    offset *= valid_pixels
    
    # dump images ==============================================================
    if dump_images is not None:
        save_image(scene_mask, './%s_scene_mask.png'%dump_images)
        save_image(target_mask, './%s_target_mask.png'%dump_images)
        save_depth(scene_depth_map, './%s_scene_depth.npy'%dump_images)
        save_depth(target_depth_map, './%s_target_depth.npy'%dump_images)
        
        min_scene_depth = numpy.min(scene_depth_map)
        max_scene_depth = numpy.max(scene_depth_map)
        scene_range = max_scene_depth - min_scene_depth
        scene_depth_image = (
            (scene_depth_map - min_scene_depth) / scene_range) * 255
        scene_depth_image = scene_depth_image.astype(numpy.uint8).squeeze(-1)
        save_image(scene_depth_image, './%s_scene_depth_image.png'%dump_images)
        
        min_target_depth = numpy.min(target_depth_map)
        max_target_depth = numpy.max(target_depth_map)
        target_range = max_target_depth - min_target_depth
        target_depth_image = (
            (target_depth_map - min_target_depth) / target_range) * 255
        target_depth_image = target_depth_image.astype(numpy.uint8).squeeze(-1)
        save_image(
            target_depth_image, './%s_target_depth_image.png'%dump_images)
        
        collision_pixels = (offset > max_intersection).astype(numpy.uint8)
        collision_pixels = collision_pixels * 255
        save_image(collision_pixels, './%s_collision.png'%dump_images)
        
        scene.export_ldraw('./%s_scene.ldr'%dump_images)
    
    if erosion or return_colliding_instances:
        collision = offset > max_intersection
        if erosion:
            collision = binary_erosion(collision, iterations=erosion)
    
    if return_colliding_instances:
        colliding_y, colliding_x = numpy.where(collision)
        colliding_colors = scene_mask[colliding_y, colliding_x]
        colliding_bricks = numpy.unique(color_byte_to_index(colliding_colors))
        return colliding_bricks
    
    else:
        if erosion:
            collision = numpy.any(collision)
        else:
            collision = numpy.max(offset) > max_intersection
        
        return collision

def build_collision_map(
    scene,
    target_instances=None,
    scene_instances=None,
    frame_buffer=None,
    resolution=(128,128),
    *args,
    **kwargs,
):
    
    if target_instances is None:
        target_instances = set(int(i) for i in scene.instances)
    
    if scene_instances is None:
        scene_instances = set(int(i) for i in scene.instances)
    else:
        scene_instances = set(
            int(scene_instance) for scene_instance in scene_instances)
    
    edges = scene.get_assembly_edges(unidirectional=False)
    collision_map = {}
    for instance in target_instances:
        instance = scene.instances[instance]
        instance_id = instance.instance_id
        instance_name = instance.instance_name
        collision_map[instance_id] = {}
        source_edges = edges[0] == instance_id
        snaps_to_check = edges[2, source_edges]
        snap_groups = {}
        for snap_id in snaps_to_check:
            snap = instance.snaps[snap_id]
            axis = snap.transform[:3,1]
            if snap.polarity == '-':
                axis *= -1
            feature = (tuple(axis) + (snap.polarity == '+',))
            for key in snap_groups:
                if default_allclose(key, feature):
                    snap_groups[key].append(snap_id)
                    break
            else:
                snap_groups[feature] = [snap_id]
        
        for feature, snap_ids in snap_groups.items():
            snap_id = snap_ids[0]
            snap = instance.snaps[snap_id]
            map_key = (feature[:3], feature[3], tuple(snap_ids))
            collision_map[instance_id][map_key] = set()
            current_scene_instances = scene_instances - set([instance_id])
            k = 0
            while current_scene_instances:
                k += 1
                colliders = scene.check_snap_collision(
                    [instance],
                    snap,
                    scene_instances=current_scene_instances,
                    return_colliding_instances=True,
                    *args,
                    **kwargs,
                )
                if len(colliders):
                    colliders = set(int(i) for i in colliders)
                    if 0 in colliders:
                        raise ThisShouldNeverHappen
                    collision_map[instance_id][map_key] |= colliders
                    current_scene_instances -= colliders
                else:
                    break
    
    return collision_map

