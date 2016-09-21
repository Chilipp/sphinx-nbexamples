# -*- coding: utf-8 -*-
import os.path as osp

dirname = osp.dirname(__file__)

master_doc = 'index'

extensions = ['sphinx_nbexamples']

example_gallery_config = {
    'examples_dirs': [osp.join(dirname, 'raw_examples')],
    'gallery_dirs': [osp.join(dirname,  'examples')]}
