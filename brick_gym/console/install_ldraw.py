#!/usr/bin/env python
import os
import requests
import zipfile

import brick_gym.config as config


def run():
    if not os.path.isdir(config.paths['data']):
        print('making data directory: %s'%config.paths['data'])
        os.makedirs(config.paths['data'])
    else:
        print('data directory already exists: %s'%config.paths['data'])

    complete_zip_path = os.path.join(config.paths['data'], 'complete.zip')
    if os.path.exists(complete_zip_path):
        print('ldraw complete.zip already downloaded: %s'%complete_zip_path)
    else:
        print('downloading ldraw complete.zip to: %s'%complete_zip_path)
        ldraw_url = str(config.urls['ldraw_complete_zip'])
        r = requests.get(ldraw_url, allow_redirects=True)
        open(complete_zip_path, 'wb').write(r.content)

    if os.path.exists(config.paths['ldraw']):
        print('ldraw already extracted: %s'%config.paths['ldraw'])
    else:
        print('extracting LDraw contents to: %s'%config.paths['ldraw'])
        with zipfile.ZipFile(complete_zip_path, 'r') as z:
            z.extractall(config.paths['data'])
