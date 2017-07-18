# -*- coding: utf-8 -*-
import os
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


try:
    import pathlib

    def file2html(fname):
        return pathlib.Path(fname).as_uri()

except ImportError:
    pathlib = None


_link_dir = os.getenv('LINKGALLERYTO')
if _link_dir:
    extensions.append('sphinx.ext.intersphinx')
    intersphinx_mapping = {'sphinx_nbexamples': (
        file2html(_link_dir), osp.join(_link_dir, 'objects.inv'))}
