import sys
import traceback
import multiprocessing

import gym
from gym.vector.async_vector_env import AsyncVectorEnv
from gym.vector.sync_vector_env import SyncVectorEnv
from gym import spaces

from ltron.bricks.brick_scene import BrickScene

def traceback_decorator(f):
    def wrapper(self, *args, **kwargs):
        try:
            return f(self, *args, **kwargs)
        except:
            if hasattr(self, 'print_traceback') and self.print_traceback:
                exc_class, exc, exc_traceback = sys.exc_info()
                print(''.join(traceback.format_tb(exc_traceback)))
            raise
    
    return wrapper

class LtronEnv(gym.Env):
    @traceback_decorator
    def __init__(self, components, print_traceback=False):
        self.print_traceback = print_traceback
        self.components = components
        
        observation_space = {}
        action_space = {}
        for component_name, component in self.components.items():
            if hasattr(component, 'observation_space'):
                observation_space[component_name] = (
                        component.observation_space)
            if hasattr(component, 'action_space'):
                action_space[component_name] = component.action_space
        self.observation_space = spaces.Dict(observation_space)
        self.action_space = spaces.Dict(action_space)
    
    @traceback_decorator
    def reset(self):
        observation = {}
        for component_name, component in self.components.items():
            component_observation = component.reset()
            if component_name in self.observation_space.spaces:
                observation[component_name] = component_observation
        return observation
    
    @traceback_decorator
    def check_action(self, action):
        for key in self.action_space:
            if key not in action:
                raise KeyError('Expected key "%s" in action'%key)
    
    @traceback_decorator
    def step(self, action):
        self.check_action(action)
        observation = {}
        reward = 0.
        terminal = False
        info = {}
        for component_name, component in self.components.items():
            if component_name in self.action_space.spaces:
                component_action = action[component_name]
            else:
                component_action = None
            o,r,t,i = component.step(component_action)
            if component_name in self.observation_space.spaces:
                observation[component_name] = o
            reward += r
            terminal |= t
            if i is not None:
                info[component_name] = i
        
        return observation, reward, terminal, info
    
    @traceback_decorator
    def render(self, mode='human', close=False):
        for component in self.components.values():
            component.render(self.state)
    
    @traceback_decorator
    def get_state(self):
        state = {}
        for component_name, component in self.components.items():
            s = component.get_state()
            #if s is not None:
            state[component_name] = s
        
        return state
    
    @traceback_decorator
    def set_state(self, state):
        observation = {}
        for component_name, component_state in state.items():
            o = self.components[component_name].set_state(component_state)
            if component_name in self.observation_space.spaces:
                observation[component_name] = o
        
        return observation
    
    @traceback_decorator
    def close(self):
        for component in self.components.values():
            component.close()

def async_ltron(num_processes, env_constructor, *args, **kwargs):
    def constructor_wrapper(i):
        def constructor():
            env = env_constructor(
                *args, rank=i, size=num_processes, **kwargs)
            return env
        return constructor
    constructors = [constructor_wrapper(i) for i in range(num_processes)]
    vector_env = AsyncVectorEnv(constructors, context='spawn')
    
    return vector_env

def sync_ltron(num_processes, env_constructor, *args, **kwargs):
    def constructor_wrapper(i):
        def constructor():
            env = env_constructor(
                *args, rank=1, size=num_processes, **kwargs)
            return env
        return constructor
    constructors = [constructor_wrapper(i) for i in range(num_processes)]
    vector_env = SyncVectorEnv(constructors)
    
    return vector_env