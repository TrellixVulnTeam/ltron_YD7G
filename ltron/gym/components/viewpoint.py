import math
import random

import numpy

from gym.spaces import Dict, Discrete
from ltron.gym.spaces import SingleSE3Space

import splendor.camera as camera

from ltron.gym.components.ltron_gym_component import LtronGymComponent

class ControlledAzimuthalViewpointComponent(LtronGymComponent):
    def __init__(self,
        scene_component,
        azimuth_steps,
        elevation_range,
        elevation_steps,
        distance_range,
        distance_steps,
        field_of_view=math.radians(60.),
        aspect_ratio=1.,
        near_clip=1.,
        far_clip=5000.,
        start_position='uniform',
        observe_camera_parameters=True,
        observe_view_matrix=False,
        scene_min=-1000,
        scene_max=1000,
    ):
        
        self.scene_component = scene_component
        self.azimuth_steps = azimuth_steps
        self.elevation_range = elevation_range
        self.elevation_steps = elevation_steps
        self.distance_range = distance_range
        self.distance_steps = distance_steps
        self.field_of_view = field_of_view
        self.aspect_ratio = aspect_ratio
        self.near_clip = near_clip
        self.far_clip = far_clip
        self.start_position = start_position
        self.observe_camera_parameters = observe_camera_parameters
        self.observe_view_matrix = observe_view_matrix
        
        observation_space = {}
        if self.observe_camera_parameters:
            observation_space['azimuth'] = Discrete(azimuth_steps)
            observation_space['elevation'] = Discrete(elevation_steps)
            observation_space['distance'] = Discrete(distance_steps)
        if self.observe_view_matrix:
            observation_space['view_matrix'] = SingleSE3Space(
                scene_min, scene_max)
        if len(observation_space):
            self.observation_space = Dict(observation_space)
        
        self.action_space = Discrete(7)
        self.num_locations = azimuth_steps * elevation_steps * distance_steps
        self.location = None
        
        self.azimuth_spacing = math.pi * 2 / azimuth_steps
        self.elevation_spacing = (
                elevation_range[1] - elevation_range[0]) / (elevation_steps-1)
        self.distance_spacing = (
                distance_range[1] - distance_range[0]) / (distance_steps-1)
    
    def compute_observation(self):
        self.observation = {}
        if self.observe_camera_parameters:
            self.observation['azimuth'] = self.position[0]
            self.observation['elevation'] = self.position[1]
            self.observation['distance'] = self.position[2]
        if self.observe_view_matrix:
            self.observation['view_matrix'] = self.view_matrix
        
        if not len(self.observation):
            self.observation = None
    
    def reset(self):
        if self.start_position == 'uniform':
            self.position = [
                    random.randint(0, self.azimuth_steps-1),
                    random.randint(0, self.elevation_steps-1),
                    random.randint(0, self.distance_steps-1)]
        else:
            self.position = list(self.start_position)
        self.set_camera()
        
        self.compute_observation()
        return self.observation
    
    def step(self, action):
        if action == 0:
            pass
        elif action == 1:
            self.position[0] -= 1
            self.position[0] = self.position[0] % self.azimuth_steps
        elif action == 2:
            self.position[0] += 1
            self.position[0] = self.position[0] % self.azimuth_steps
        elif action == 3:
            self.position[1] -= 1
            self.position[1] = max(0, self.position[1])
        elif action == 4:
            self.position[1] += 1
            self.position[1] = min(self.elevation_steps-1, self.position[1])
        elif action == 5:
            self.position[2] -= 1
            self.position[2] = max(0, self.position[2])
        elif action == 6:
            self.position[2] += 1
            self.position[2] = min(self.distance_steps-1, self.position[2])
        
        self.set_camera()
        
        #tmp_reward = self.position[1] + self.position[2]
        self.compute_observation()
        return self.observation, 0., False, None
    
    def set_camera(self):
        scene = self.scene_component.brick_scene
        azimuth = self.position[0] * self.azimuth_spacing
        elevation = (self.position[1] * self.elevation_spacing +
                self.elevation_range[0])
        field_of_view = self.field_of_view
        distance = (self.position[2] * self.distance_spacing +
                self.distance_range[0])
        
        # projection
        self.projection = camera.projection_matrix(
                self.field_of_view,
                self.aspect_ratio,
                self.near_clip,
                self.far_clip)
        scene.set_projection(self.projection)
        
        # pose
        bbox = scene.get_instance_center_bbox()
        bbox_min, bbox_max = bbox
        bbox_range = numpy.array(bbox_max) - numpy.array(bbox_min)
        center = bbox_min + bbox_range * 0.5
        self.view_matrix = numpy.linalg.inv(
            camera.azimuthal_parameters_to_matrix(
                azimuth, elevation, 0, distance, 0.0, 0.0, *center)
        )
        scene.set_view_matrix(self.view_matrix)

class RandomizedAzimuthalViewpointComponent(LtronGymComponent):
    def __init__(self,
        scene_component,
        azimuth = (0, math.pi*2),
        elevation = (math.radians(-15), math.radians(-45)),
        tilt = (math.radians(-45.), math.radians(45.)),
        field_of_view = (math.radians(60.), math.radians(60.)),
        distance = (0.8, 1.2),
        aspect_ratio = 1.,
        near_clip = 1.,
        far_clip = 5000.,
        bbox_distance_scale = 3.,
        randomize_frequency = 'reset',
        observe_view_matrix=False,
        scene_min=-1000,
        scene_max=1000,
    ):
        
        self.scene_component = scene_component
        self.scene_component.brick_scene.make_renderable()
        self.azimuth = azimuth
        self.elevation = elevation
        self.tilt = tilt
        self.field_of_view = field_of_view
        self.distance = distance
        self.aspect_ratio = aspect_ratio
        self.near_clip = near_clip
        self.far_clip = far_clip
        self.bbox_distance_scale = bbox_distance_scale
        self.randomize_frequency = randomize_frequency
        self.observe_view_matrix = observe_view_matrix
        
        observation_space = {}
        if self.observe_view_matrix:
            observation_space['view_matrix'] = SingleSE3Space(
                scene_min, scene_max)
        if len(observation_space):
            self.observation_space = Dict(observation_space)
        
        self.set_camera()
    
    def set_camera(self):
        # projection
        scene = self.scene_component.brick_scene
        azimuth = random.uniform(*self.azimuth)
        elevation = random.uniform(*self.elevation)
        tilt = random.uniform(*self.tilt)
        field_of_view = random.uniform(*self.field_of_view)
        distance_scale = random.uniform(*self.distance)
        
        self.projection = camera.projection_matrix(
                field_of_view,
                self.aspect_ratio,
                self.near_clip,
                self.far_clip)
        scene.set_projection(self.projection)
        
        # pose
        bbox = scene.get_instance_center_bbox()
        bbox_min, bbox_max = bbox
        bbox_range = numpy.array(bbox_max) - numpy.array(bbox_min)
        center = bbox_min + bbox_range * 0.5
        distance = distance_scale * camera.framing_distance_for_bbox(
                bbox, self.projection, self.bbox_distance_scale)
        self.view_matrix = numpy.linalg.inv(
            camera.azimuthal_parameters_to_matrix(
                azimuth, elevation, tilt, distance, 0.0, 0.0, *center)
        )
        scene.set_view_matrix(self.view_matrix)
    
    def compute_observation(self):
        if self.observe_view_matrix:
            self.observation = {'view_matrix':self.view_matrix}
        else:
            self.observation = None
    
    def reset(self):
        self.set_camera()
        self.compute_observation()
        return self.observation
    
    def step(self, action):
        if self.randomize_frequency == 'step':
            self.set_camera()
        self.compute_observation()
        return self.observation, 0., False, None
    
    def set_state(self, state):
        self.set_camera()

class FixedAzimuthalViewpointComponent(RandomizedAzimuthalViewpointComponent):
    def __init__(self,
            scene_component,
            azimuth,
            elevation,
            tilt = 0.,
            field_of_view = math.radians(60.),
            *args, **kwargs):
        
        super(FixedAzimuthalViewpointComponent, self).__init__(
                scene_component,
                (azimuth, azimuth),
                (elevation, elevation),
                (tilt, tilt),
                (field_of_view, field_of_view),
                *args, **kwargs)

class CopyViewpointComponent(LtronGymComponent):
    def __init__(self, from_scene_component, to_scene_component):
        self.from_scene_component = from_scene_component
        self.to_scene_component = to_scene_component
    
    def copy_camera(self):
        view_matrix = self.from_scene_component.brick_scene.get_view_matrix()
        projection = self.from_scene_component.brick_scene.get_projection()
        self.to_scene_component.brick_scene.set_view_matrix(view_matrix)
        self.to_scene_component.brick_scene.set_projection(projection)
    
    def reset(self):
        self.copy_camera()
        return None
    
    def step(self, action):
        self.copy_camera()
        return None, 0, False, None
