#!/usr/bin/env python
import os
import json
import argparse

import brick_gym.dataset.metadata as metadata

def run():
    parser = argparse.ArgumentParser()
    parser.add_argument('dataset', type=str)
    parser.add_argument('--split', type=str, default='all_mpd')
    args = parser.parse_args()

    metadata.make_dataset_metadata(args.dataset, args.split)
