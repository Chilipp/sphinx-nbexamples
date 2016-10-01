# -*- coding: utf-8 -*-
import os.path as osp

dirname = osp.dirname(__file__)

master_doc = 'index'

extensions = ['sphinx_nbexamples']

example_gallery_config = {
    'examples_dirs': osp.join(dirname, 'raw_examples'),
    'gallery_dirs': osp.join(dirname,  'examples'),
    'code_examples': {osp.join(dirname, 'raw_examples',
                               'example_hello_world.ipynb'): 'someothercode'},
    'thumbnail_figures': {
        osp.join(dirname, 'raw_examples',
                 'example_mpl_test_figure_chosen.ipynb'): 0},
    'supplementary_files': {
        osp.join(dirname, 'raw_examples',
                 'example_hello_world.ipynb'): ['test2.txt']}}

exclude_patterns = ['raw_examples']
