import numpy

import brick_gym.gym.spaces as bg_spaces
from brick_gym.gym.components.brick_env_component import BrickEnvComponent

class VisibilityComponent(BrickEnvComponent):
    def __init__(self,
                scene_component,
                terminate_when_all_hidden=False):
        self.scene_component = scene_component
        self.terminate_when_all_hidden = terminate_when_all_hidden
    
    def hide_instance(self, instance_index):
        if instance_index != 0:
            scene = self.scene_component.brick_scene
            scene.hide_instance(instance_index)
    
    def check_terminal(self):
        if self.terminate_when_all_hidden:
            scene = self.scene_component.brick_scene
            all_hidden = all(scene.instance_hidden(instance)
                    for instance in scene.instances)
            return all_hidden
            
        else:
            return False
    
    def get_state(self):
        scene = self.scene_component.brick_scene
        return {str(instance):scene.instance_hidden(instance)
                for instance in scene.instances}
    
    def set_state(self, state):
        scene = self.scene_component.brick_scene
        for instance, hide in state.items():
            if hide:
                scene.hide_instance(instance)
            else:
                scene.show_instance(instance)

class InstanceVisibilityComponent(VisibilityComponent):
    def __init__(self,
            max_instances,
            scene_component,
            multi=False,
            terminate_when_all_hidden=False):
        
        super(InstanceVisibilityComponent, self).__init__(
                scene_component = scene_component,
                terminate_when_all_hidden = terminate_when_all_hidden)
        self.max_instances = max_instances
        self.multi = multi
        
        if multi:
            self.action_space = bg_spaces.MultiInstanceSelectionSpace(
                    self.max_instances)
        else:
            self.action_space = bg_spaces.SingleInstanceIndexSpace(
                    self.max_instances)
    
    def step(self, action):
        if self.multi:
            for instance in numpy.nonzero(action)[0]:
                if instance != 0:
                    self.hide_instance(instance)
        else:
            self.hide_instance(action)
        
        return None, 0., self.check_terminal(), None

class InstanceRemovabilityComponent(BrickEnvComponent):
    def __init__(self,
            max_instances,
            scene_component):
        
        self.max_instances = max_instances
        self.scene_component = scene_component
        self.observation_space = bg_spaces.MultiInstanceSelectionSpace(
                self.max_instances)
    
    def compute_observation(self):
        scene = self.scene_component.brick_scene
        observation = numpy.zeros(self.max_instances+1, dtype=numpy.bool)
        for instance_id, instance in scene.instances.items():
            removable, direction = scene.is_instance_removable(instance)
            if removable:
                observation[int(instance_id)] = True
        
        return observation
    
    def reset(self):
        return self.compute_observation()
    
    def step(self, action):
        return self.compute_observation(), 0, False, None

class PixelVisibilityComponent(VisibilityComponent):
    def __init__(self,
            width,
            height,
            scene_component,
            segmentation_component,
            terminate_when_all_hidden=False):
        
        super(PixelVisibilityComponent, self).__init__(
                scene_component = scene_component,
                terminate_when_all_hidden = terminate_when_all_hidden)
        self.width = width
        self.height = height
        self.segmentation_component = segmentation_component
        
        self.action_space = bg_spaces.PixelSelectionSpace(
                self.width, self.height)
    
    def step(self, action):
        x, y = action[self.pixel_key]
        instance_map = self.mask_render_component.segmentation
        instance_index = instance_map[y,x]
        self.hide_instance(instance_index)
        
        return None, 0., self.check_terminal(), None
