#!/usr/bin/env python
#import brick_gym.torch.train.graph_d as graph_d
import brick_gym.torch.train.test_noninteractive_graph as test_graph

#run = 'Jan24_01-28-20_mechagodzilla'
#epoch = 200
#run = 'Feb10_11-50-54_gpu3'
#run = 'Feb23_00-57-59_mechagodzilla' #'Feb17_22-57-19_gpu3'
#run = 'Mar05_21-48-25_mechagodzilla'
run = 'Mar09_13-54-18_mechagodzilla'
epoch = 10

if __name__ == '__main__':
    test_graph.test_checkpoint(
            # load checkpoints
            step_checkpoint = './checkpoint/%s/step_model_%04i.pt'%(run, epoch),
            edge_checkpoint = './checkpoint/%s/edge_model_%04i.pt'%(run, epoch),
            
            # dataset settings
            dataset = 'tiny_turbos2',
            num_processes = 4,
            test_split = 'train',
            test_subset = 4,
            
            # model settings
            step_model_name='nth_try',
            decoder_channels=512,
            step_model_backbone='simple',
            use_ground_truth_segmentation=True,
            
            # output settings
            dump_debug=True)
