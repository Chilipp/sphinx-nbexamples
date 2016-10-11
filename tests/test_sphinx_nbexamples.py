import os
import re
import os.path as osp
import unittest
from tempfile import mkdtemp
from sphinx.application import Sphinx
import glob
import shutil
import six


if six.PY2:
    sphinx_supp = osp.abspath(osp.join(osp.dirname(__file__),
                                       'sphinx_supp_py2'))
else:
    sphinx_supp = osp.abspath(osp.join(osp.dirname(__file__),
                                       'sphinx_supp_py3'))


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
        raw_dir = osp.join(self.src_dir, 'raw_examples')
        for f in find_files(raw_dir,
                            'example_*.ipynb'):
            base = osp.splitext(f)[0].replace(
                raw_dir, osp.join(self.src_dir, 'examples'))
            self.assertTrue(osp.exists(base + '.ipynb'),
                            msg=base + '.ipynb is missing')
            self.assertTrue(osp.exists(base + '.rst'),
                            msg=base + '.rst is missing')
            self.assertTrue(osp.exists(base + '.py'),
                            msg=base + '.py is missing')
            html = osp.splitext(
                f.replace(raw_dir, osp.join(
                    self.out_dir, 'examples')))[0] + '.html'
            self.assertTrue(osp.exists(html), msg=html + ' is missing!')

    def test_thumbnail(self):
        """Test if the thumbnail has been inserted correctly"""
        base = 'example_mpl_test'
        outdir = self.out_dir
        thumb = osp.join(self.src_dir, 'examples', 'images', 'thumb',
                         'example_glr_' + base + '_1_thumb.png')
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

    def test_magics(self):
        """Test whether ipython magics are removed correctly"""
        base = 'example_magics'
        rst_path = osp.join(self.src_dir, 'examples', base) + '.rst'
        with open(rst_path) as f:
            rst = f.read()
        # test if both '%magic okay' statements are still in the file
        self.assertIsNotNone(
            re.search(r'\(.%magic okay.\)', rst),
            msg="Print command 'print('%%magic okay')' not found in \n%s!" % (
                rst))
        self.assertIsNotNone(
            re.search(r'(?<!\(.)%magic okay(?!.\))', rst),
            msg="Print output '%%magic okay' not found in \n%s!" % rst)
        self.assertNotIn('%matplotlib inline', rst)
        # test if a single magic command is removed
        self.assertNotIn('%cd', rst)
        # test if magic inside a markdown works
        self.assertIn('%test', rst)
        # test if magic inside a python code works
        self.assertIsNotNone(
            re.search(r'print\(.+%magic like.+\)', rst),
            msg="Print command 'print('%%magic like')' not found in \n%s!" % (
                rst))
        self.assertIsNotNone(
            re.search(r'(?<!print\(.)Something %magic like.+(?!\))', rst),
            msg="Print output '%%magic like' not found in \n%s!" % rst)

    def test_supplementary_files(self):
        """Test whether the supplementary files are inserted corretly"""
        rst_copy = osp.join(self.src_dir, 'examples', 'sub', 'test.txt')
        self.assertTrue(
            osp.exists(rst_copy), msg=rst_copy + ' is missing')
        html_download = osp.join(self.out_dir, '_downloads', 'test.txt')
        self.assertTrue(
            osp.exists(html_download), msg=html_download + ' is missing')
        rst_path = osp.join(self.src_dir, 'examples', 'sub',
                            'example_supplementary_files.rst')
        with open(rst_path) as f:
            self.assertIsNotNone(
                re.search(r'Download supplementary data.+test.txt', f.read()),
                msg='Download for supplementary data not found in %s' % (
                    rst_path))
        rst_path = osp.join(self.src_dir, 'examples',
                            'example_hello_world.rst')
        with open(rst_path) as f:
            self.assertIsNotNone(
                re.search(r'Download supplementary data.+test2.txt', f.read()),
                msg='Download for supplementary data not found in %s' % (
                    rst_path))

    def test_code_div(self):
        """Test whether the code example is inserted correctly in the gallery
        """
        html_path = osp.join(self.out_dir, 'examples', 'index.html')
        self.assertTrue(osp.exists(html_path),
                        msg=html_path + ' is missing!')
        with open(html_path) as f:
            html = f.read()
        self.assertIn('somecode', html)
        self.assertIn('someothercode', html)

    def test_given_thumb(self):
        """Test whether the code example is inserted correctly in the gallery
        """
        html_path = osp.join(self.out_dir, 'examples', 'index.html')
        self.assertTrue(osp.exists(html_path),
                        msg=html_path + ' is missing!')
        with open(html_path) as f:
            html = f.read()
        self.assertIn('test_image', html,
                      msg=('The wrong picture has been chosen for '
                           'example_failure.ipynb'))
        self.assertIn('example_mpl_test_figure_chosen_0', html,
                      msg=('The wrong picture has been chosen for '
                           'example_mpl_test_figure_chosen.ipynb'))


def _test_url(url, *args, **kwargs):
    if six.PY3:
        from urllib import request
        request.urlopen(url, *args, **kwargs)
    else:
        import urllib
        urllib.urlopen(url, *args, **kwargs)

# check if we are online by trying to connect to google
try:
    _test_url('https://www.google.de')
    online = True
except:
    online = False


if __name__ == '__main__':
    unittest.main()
