#!/usr/bin/env python
#import brick_gym.torch.train.graph_d as graph_d
import brick_gym.torch.train.test_graph as test_graph

#run = 'Jan24_01-28-20_mechagodzilla'
#epoch = 200
run = 'Feb01_22-37-07_gpu1'
epoch = 440

if __name__ == '__main__':
    test_graph.test_checkpoint(
            # load checkpoints
            step_checkpoint = './checkpoint/%s/step_model_%04i.pt'%(run, epoch),
            edge_checkpoint = './checkpoint/%s/edge_model_%04i.pt'%(run, epoch),
            
            # dataset settings
            dataset = 'tiny_turbos2',
            num_processes = 8,
            test_split = 'train',
            test_subset = None,
            
            # model settings
            step_model_name='nth_try',
            segment_id_matching=True)
