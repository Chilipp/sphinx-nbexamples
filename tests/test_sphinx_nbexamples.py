import os
import re
import os.path as osp
import unittest
from tempfile import mkdtemp
from sphinx.application import Sphinx
import sphinx
import glob
import shutil
import six
try:
    import pathlib
except ImportError:
    pathlib = None


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


class BaseTest(unittest.TestCase):

    def setUp(self):
        self.src_dir = mkdtemp(prefix='tmp_nbexamples_')
        os.rmdir(self.src_dir)
        self.out_dir = osp.join(self.src_dir, 'build', 'html')
        shutil.copytree(sphinx_supp, self.src_dir)
        self.app = Sphinx(
            srcdir=self.src_dir, confdir=self.src_dir, outdir=self.out_dir,
            doctreedir=osp.join(self.src_dir, 'build', 'doctrees'),
            buildername='html')
        self.app.build()

    def tearDown(self):
        shutil.rmtree(self.src_dir)


class TestGallery(BaseTest):

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
        base = osp.join(self.src_dir, 'examples', 'example_mpl_test.ipynb')
        outdir = self.out_dir
        thumb = osp.join(self.src_dir, 'examples', 'images', 'thumb',
                         'gallery_' + base.replace(os.path.sep, '_').lower() +
                         '_thumb.png')
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

    def test_tag_removal(self):
        """Test whether the tagged cell has been removed correctly"""
        base = 'example_tag_removal'
        rst_path = osp.join(self.src_dir, 'examples', base) + '.rst'
        py_path = osp.join(self.src_dir, 'examples', base) + '.py'
        with open(rst_path) as f:
            self.assertNotIn('This should be removed!', f.read())
        with open(py_path) as f:
            self.assertIn('This should be removed!', f.read())

    def test_supplementary_files(self):
        """Test whether the supplementary files are inserted corretly"""
        rst_copy = osp.join(self.src_dir, 'examples', 'sub', 'test.txt')
        self.assertTrue(
            osp.exists(rst_copy), msg=rst_copy + ' is missing')
        if sphinx.__version__ < '1.8.0':
            html_download = osp.join(self.out_dir, '_downloads', 'test.txt')
        else:
            html_download = osp.join(
                self.out_dir, '_downloads', '*', 'test.txt')
        self.assertTrue(
            glob.glob(html_download), msg=html_download + ' is missing')
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
        self.assertIn('example_failure.ipynb_thumb.png', html,
                      msg=('The wrong picture has been chosen for '
                           'example_failure.ipynb'))
        self.assertIn('example_mpl_test_figure_chosen.ipynb_thumb.png', html,
                      msg=('The wrong picture has been chosen for '
                           'example_mpl_test_figure_chosen.ipynb'))


@unittest.skipIf(pathlib is None, 'The pathlib package is required!')
class TestLinkGalleries(BaseTest):

    def tearDown(self):
        shutil.rmtree(self.src_dir2)
        super(TestLinkGalleries, self).tearDown()

    def test_linkgalleries(self):
        """Test the directive"""
        self.src_dir2 = self.src_dir
        self.out_dir2 = self.out_dir
        os.environ['LINKGALLERYTO'] = self.out_dir
        fname = osp.join(
            self.out_dir, 'examples', 'example_mpl_test.html')
        self.assertTrue(osp.exists(fname), msg=fname + ' is missing!')
        thumbnail = osp.join(
            self.out_dir, '_images',
            'gallery_' + self.src_dir.replace(os.path.sep, '_').lower() +
            '_examples_example_mpl_test.ipynb_thumb.png')
        self.assertTrue(osp.exists(thumbnail), msg=thumbnail + ' is missing!')
        # create a setup with the links
        self.setUp()
        self.assertTrue
        html_path = osp.join(self.out_dir, 'index.html')
        self.assertTrue(osp.exists(html_path),
                        msg=html_path + ' is missing!')
        with open(html_path) as f:
            html = f.read()
        self.assertIn(osp.basename(thumbnail), html)

        # test with new thumbnail to test the linkgalleries with it's own
        # project
        thumbnails = glob.glob(osp.join(
            self.out_dir, '_images',
            'gallery_' + self.src_dir.replace(os.path.sep, '_').lower() +
            '_examples_example_mpl_test.ipynb_thumb*.png'))
        self.assertTrue(thumbnails)  # check that some thumbnails are found
        self.assertTrue(any(osp.relpath(f, self.out_dir) in html
                            for f in thumbnails),
                        msg='None of %s found in %s' % (thumbnails, html))


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
