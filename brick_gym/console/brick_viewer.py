#!/usr/bin/env python
import argparse

import brick_gym.visualization.brick_viewer as brick_viewer

def run():
    parser = argparse.ArgumentParser()

    parser.add_argument('file_path', type=str)
    # parser.add_argument('--subdocument', type=str, default=None)
    parser.add_argument('--resolution', type=str, default='512x512')
    parser.add_argument('--image-light', type=str, default='grey_cube')
    parser.add_argument('--poll-frequency', type=int, default=1024)
    parser.add_argument('--fps', action='store_true')

    args = parser.parse_args()

    width, height = args.resolution.lower().split('x')
    width = int(width)
    height = int(height)
    brick_viewer.start_viewer(
            args.file_path,
            #args.subdocument,
            width,
            height,
            args.image_light,
            args.poll_frequency,
            print_fps = args.fps)
