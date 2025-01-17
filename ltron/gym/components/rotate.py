import numpy
from ltron.gym.components.ltron_gym_component import LtronGymComponent
from gym.spaces import (
    Discrete,
    Tuple,
    Dict,
    MultiDiscrete
)
from ltron.geometry.collision import check_collision
import math

class CursorRotateAboutSnap(LtronGymComponent):
    def __init__(
        self,
        scene_component,
        cursor_component,
        check_collision,
        rotation_steps = 4,
        allow_snap_flip = False,
    ):
        self.scene_component = scene_component
        self.cursor_component = cursor_component
        self.check_collision = check_collision
        self.rotation_steps = rotation_steps
        self.allow_snap_flip = allow_snap_flip
        #self.action_space = Dict({
            #'activate':Discrete(2),
        #    'rotation':Discrete(self.rotation_steps),
        #})
        if allow_snap_flip:
            self.action_space = Discrete(self.rotation_steps*2)
        else:
            self.action_space = Discrete(self.rotation_steps)

        self.observation_space = Dict({'success': Discrete(2)})

    def reset(self):
        return {'success':0}

    def step(self, action):
        
        if not action:
            return {'success' : 0}, 0, False, None

        #activate = action['activate']
        #if not activate:
        #    return {'success':0}, 0, False, None
        
        #discrete_rotate = action['rotation']
        a = action % self.rotation_steps
        degree = a * math.pi * 2 / self.rotation_steps
        flip = action // self.rotation_steps
        
        trans = numpy.eye(4)
        #rotate_x = numpy.copy(trans)
        #rotate_x[1,1] = math.cos(degree)
        #rotate_x[1,2] = -math.sin(degree)
        #rotate_x[2:1] = math.sin(degree)
        #rotate_x[2:2] = math.cos(degree)
        
        rotate_y = numpy.copy(trans)
        rotate_y[0,0] = math.cos(degree)
        rotate_y[0,2] = math.sin(degree)
        rotate_y[2,0] = -math.sin(degree)
        rotate_y[2,2] = math.cos(degree)
        
        if flip:
            flip_transform = numpy.array([
                [-1, 0, 0, 0],
                [ 0,-1, 0, 0],
                [ 0, 0, 1, 0],
                [ 0, 0, 0, 1]
            ])
            rotate_y = rotate_y @ flip_transform
        
        #rotate_z = numpy.copy(trans)
        #rotate_z[0,0] = math.cos(degree)
        #rotate_z[0,1] = -math.sin(degree)
        #rotate_z[1,0] = math.sin(degree)
        #rotate_z[1,1] = math.cos(degree)
        
        instance_id = self.cursor_component.instance_id
        snap_id = self.cursor_component.snap_id
        if instance_id == 0:
            return {'success' : 0}, 0, False, None
        
        scene = self.scene_component.brick_scene
        instance = scene.instances[instance_id]
        original_instance_transform = instance.transform
        snap = instance.snaps[snap_id]
        scene.transform_about_snap([instance], snap, rotate_y)
        
        if self.check_collision:
            transform = instance.transform
            snap = instance.snaps[snap_id]
            collision = self.scene_component.brick_scene.check_snap_collision(
                target_instances=[instance], snap=snap)
            if collision:
                self.scene_component.brick_scene.move_instance(
                    instance, original_instance_transform)
                return {'success' : 0}, 0, False, None
        
        return {'success' : 1}, 0, False, None
    
    def no_op_action(self):
        return 0

class RotateAboutSnap(LtronGymComponent):
    def __init__(
        self,
        scene_components,
        cursor_component,
        check_collision,
        rotation_steps = 4,
        allow_snap_flip = False,
    ):
        self.scene_components = scene_components
        self.cursor_component = cursor_component
        self.check_collision = check_collision
        self.rotation_steps = rotation_steps
        self.allow_snap_flip = allow_snap_flip
        #self.action_space = Dict({
            #'activate':Discrete(2),
        #    'rotation':Discrete(self.rotation_steps),
        #})
        if allow_snap_flip:
            self.action_space = Discrete(self.rotation_steps*2)
        else:
            self.action_space = Discrete(self.rotation_steps)

        #self.observation_space = Dict({'success': Discrete(2)})
    
    #def reset(self):
    #    return {'success':0}
    
    def step(self, action):
        #failure = {'success' : 0}, 0, False, None
        if not action:
            #return failure
            return None, 0., False, {}
        
        a = action % self.rotation_steps
        degree = a * math.pi * 2 / self.rotation_steps
        flip = action // self.rotation_steps
        
        trans = numpy.eye(4)
        
        rotate_y = numpy.copy(trans)
        rotate_y[0,0] = math.cos(degree)
        rotate_y[0,2] = math.sin(degree)
        rotate_y[2,0] = -math.sin(degree)
        rotate_y[2,2] = math.cos(degree)
        
        if flip:
            flip_transform = numpy.array([
                [-1, 0, 0, 0],
                [ 0,-1, 0, 0],
                [ 0, 0, 1, 0],
                [ 0, 0, 0, 1]
            ])
            rotate_y = rotate_y @ flip_transform
        
        n, i, s = self.cursor_component.get_selected_snap()
        if i == 0:
            #return failure
            return None, 0., False, {}
        
        scene_component = self.scene_components[n]
        scene = scene_component.brick_scene
        instance = scene.instances[i]
        if s >= len(instance.snaps):
            #return failure
            return None, 0., False, {}
        original_instance_transform = instance.transform
        snap = instance.snaps[s]
        scene.transform_about_snap([instance], snap, rotate_y)
        
        if self.check_collision:
            transform = instance.transform
            snap = instance.snaps[s]
            collision = scene_component.brick_scene.check_snap_collision(
                target_instances=[instance], snap=snap)
            if collision:
                scene_component.brick_scene.move_instance(
                    instance, original_instance_transform)
                #return {'success' : 0}, 0, False, None
                return None, 0., False, {}
        
        #return {'success' : 1}, 0, False, None
        return None, 0., False, {}
    
    def no_op_action(self):
        return 0
