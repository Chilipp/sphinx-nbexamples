import sys
import os
import os.path as osp
import unittest
from tempfile import mkdtemp
from itertools import chain
from sphinx.application import Sphinx
import glob
import shutil


sphinx_supp = osp.abspath(osp.join(osp.dirname(__file__), 'sphinx_supp'))


def find_files(src_dir, pattern, skip_private=True):
    """Find all files recursively contained in `src_dir`

    Parameters
    ----------
    src_dir: str
        The toplevel directory
    pattern: str
        A file pattern suitable for glob
    skip_private: bool
        If True, directories with starting with single ``'.'`` are ignored"""
    for root, dirs, files in os.walk(src_dir):
        dirname = osp.basename(root)
        if skip_private and dirname != '.' and dirname.startswith('.'):
            continue
        for f in glob.fnmatch.filter(files, pattern):
            yield osp.join(root, f)


class TestGallery(unittest.TestCase):

    @classmethod
    def setUp(cls):
        cls.src_dir = mkdtemp(prefix='tmp_nbexamples_')
        os.rmdir(cls.src_dir)
        cls.out_dir = osp.join(cls.src_dir, 'build', 'html')
        shutil.copytree(sphinx_supp, cls.src_dir)
        cls.app = Sphinx(
            srcdir=cls.src_dir, confdir=cls.src_dir, outdir=cls.out_dir,
            doctreedir=osp.join(cls.src_dir, 'build', 'doctrees'),
            buildername='html')
        cls.app.build()
        cls.srcdir = sphinx_supp

    @classmethod
    def tearDown(cls):
        shutil.rmtree(cls.src_dir)

    def test_files_exist(self):
        """Test if all notebooks are processed correctly"""
        for f in find_files(osp.join(self.src_dir, 'raw_examples'),
                            'example_*.ipynb'):
            base = osp.join(self.src_dir, 'examples',
                            osp.splitext(osp.basename(f))[0])
            self.assertTrue(osp.exists(base + '.ipynb'),
                            msg=base + '.ipynb is missing')
            self.assertTrue(osp.exists(base + '.rst'),
                            msg=base + '.rst is missing')
            self.assertTrue(osp.exists(base + '.py'),
                            msg=base + '.py is missing')
            html = osp.join(self.out_dir, 'examples',
                            osp.splitext(osp.basename(f))[0] + '.html')
            self.assertTrue(osp.exists(html), msg=html + ' is missing!')

    def test_thumbnail(self):
        """Test if the thumbnail has been inserted correctly"""
        base = 'example_mpl_test'
        outdir = self.out_dir
        thumb = osp.join(self.src_dir, 'examples', 'images', 'thumb',
                         'sphx_glr_' + base + '_0_thumb.png')
        self.assertTrue(osp.exists(thumb), msg=thumb + ' is missing!')
        with open(osp.join(outdir, 'examples', 'index.html')) as f:
            index_html = f.read()
        self.assertIn(osp.basename(thumb), index_html)

    def test_failure(self):
        """Test if a failed notebook is anyway existent"""
        base = 'example_failure'
        html_path = osp.join(self.out_dir, 'examples', base) + '.html'
        self.assertTrue(osp.exists(html_path),
                        msg=html_path + ' is missing!')
        with open(html_path) as f:
            html = f.read()
        self.assertIn('AssertionError', html)

if __name__ == '__main__':
    unittest.main()
