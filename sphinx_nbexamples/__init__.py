"""Create an example gallery out of a bunch of ipython notebooks

This sphinx extension extracts the ipython notebooks in a given folder to
create an example gallery. It provides the follwing configuration values
for you sphinx configuration file ``'conf.py'``:

.. autosummary::

    process_examples
    gallery_config

Notes
-----
This module was motivated by the
`sphinx-gallery <http://sphinx-gallery.readthedocs.org/en/latest/>`__ module
by Oscar Najera and in fact uses parts of it's html template for including the
thumbnails and the download containers"""
from __future__ import division
import datetime as dt
import os
import os.path as osp
import re
import six
from itertools import chain
import nbconvert
import nbformat
from shutil import copyfile
from copy import deepcopy
try:
    from sphinx.util import logging
    logger = logging.getLogger(__name__)
except (ImportError, AttributeError):
    import logging
    logger = logging.getLogger(__name__)

try:
    warn = logger.warn
except AttributeError:  # necessary for python 2.7
    warn = logger.warning

import subprocess as spr
from docutils.parsers.rst import Directive
from docutils.parsers.rst import directives
from docutils.statemachine import ViewList
from docutils import nodes

if six.PY2:
    from itertools import imap as map


try:
    from cyordereddict import OrderedDict
except ImportError:
    try:
        from collections import OrderedDict
    except ImportError:
        from ordereddict import OrderedDict


__version__ = '0.3.2'

__author__ = "Philipp Sommer"

if nbconvert.__version__ < '5.0':
    code_blocks = re.compile(r'\.\. code:: python\n(?s)(.+?)(?=\n\S+|$)')
    inner_code_blocks = re.compile(
        r'(?<=.. code:: python\n)(?s)(.+?)(?=\n\S+|$)')
else:
    code_blocks = re.compile(r'\.\. code:: ipython\d\n(?s)(.+?)(?=\n\S+|$)')
    inner_code_blocks = re.compile(
        r'(?<=.. code:: ipython\d\n)(?s)(.+?)(?=\n\S+|$)')
magic_patt = re.compile(r'(?m)^(\s+)(%.*\n)')


def isstring(s):
    return isinstance(s, six.string_types)


def create_dirs(*dirs):
    for d in dirs:
        if os.path.exists(d) and not os.path.isdir(d):
            raise IOError("Could not create directory %s because an "
                          "ordinary file with that name exists already!")
        elif not os.path.exists(d):
            os.makedirs(d)


def nbviewer_link(url):
    """Return the link to the Jupyter nbviewer for the given notebook url"""
    if six.PY2:
        from urlparse import urlparse as urlsplit
    else:
        from urllib.parse import urlsplit
    info = urlsplit(url)
    domain = info.netloc
    url_type = 'github' if domain == 'github.com' else 'url'
    return 'https://nbviewer.jupyter.org/%s%s' % (url_type, info.path)


NOIMAGE = os.path.join(os.path.dirname(__file__), '_static', 'no_image.png')


class NotebookProcessor(object):
    """Class to run process one ipython notebook and create the necessary files
    """

    #: base string for downloading the python file and ipython notebook
    CODE_DOWNLOAD = """

.. only:: html

    .. container:: sphx-glr-download

        **Download python file:** :download:`{pyfile}`

        **Download IPython notebook:** :download:`{nbfile}`
"""

    #: base string for viewing the notebook in the jupyter nbviewer
    CODE_DOWNLOAD_NBVIEWER = CODE_DOWNLOAD + """
        **View the notebook in the** `Jupyter nbviewer <{url}>`__
"""

    #: base string for downloading supplementary data
    DATA_DOWNLOAD = """

.. only:: html

    .. container:: sphx-glr-download

        **Download supplementary data:** %s
"""

    #: base string for creating the thumbnail
    THUMBNAIL_TEMPLATE = """
.. raw:: html

    <div class="sphx-glr-thumbContainer" tooltip="{snippet}">

.. only:: html

    .. figure:: /{thumbnail}

        :ref:`{ref_name}`

.. raw:: html

    </div>
"""

    CODE_TEMPLATE = """
.. raw:: html

    <div class="sphx-glr-thumbContainer" tooltip="{snippet}">

.. only:: html

    .. code:: python

        {code}

    :ref:`{ref_name}`

.. raw:: html

    </div>
"""

    BOKEH_STYLE_SHEET = (
        "http://cdn.pydata.org/bokeh/release/bokeh-{version}.min.css")

    BOKEH_JS = (
        "http://cdn.pydata.org/bokeh/release/bokeh-{version}.min.js")

    _BOKEH_TEMPLATE = """
.. raw:: html
    <link
        href="%s"
        rel="stylesheet" type="text/css">

    <script src="%s"></script>
"""
    BOKEH_TEMPLATE = _BOKEH_TEMPLATE % (BOKEH_STYLE_SHEET, BOKEH_JS)

    BOKEH_WIDGETS_STYLE_SHEET = (
        "http://cdn.pydata.org/bokeh/release/bokeh-{version}.min.css")

    BOKEH_WIDGETS_JS = (
        "http://cdn.pydata.org/bokeh/release/bokeh-{version}.min.js")

    BOKEH_WIDGETS_TEMPLATE = _BOKEH_TEMPLATE % (BOKEH_WIDGETS_STYLE_SHEET,
                                                BOKEH_WIDGETS_JS)

    #: Path to the thumbnail image
    thumb_file = NOIMAGE

    #: Paths to the pictures of this notebook
    pictures = []

    @property
    def thumbnail_div(self):
        """The string for creating the thumbnail of this example"""
        return self.THUMBNAIL_TEMPLATE.format(
            snippet=self.get_description()[1], thumbnail=self.thumb_file,
            ref_name=self.reference)

    @property
    def code_div(self):
        """The string for creating a code example for the gallery"""
        code_example = self.code_example
        if code_example is None:
            return None
        return self.CODE_TEMPLATE.format(
            snippet=self.get_description()[1], code=code_example,
            ref_name=self.reference)

    @property
    def code_example(self):
        """The code example out of the notebook metadata"""
        if self._code_example is not None:
            return self._code_example
        return getattr(self.nb.metadata, 'code_example', None)

    @property
    def supplementary_files(self):
        """The supplementary files of this notebook"""
        if self._supplementary_files is not None:
            return self._supplementary_files
        return getattr(self.nb.metadata, 'supplementary_files', None)

    @property
    def other_supplementary_files(self):
        """The supplementary files of this notebook"""
        if self._other_supplementary_files is not None:
            return self._other_supplementary_files
        return getattr(self.nb.metadata, 'other_supplementary_files', None)

    @property
    def reference(self):
        """The rst label of this example"""
        return 'gallery_' + self.outfile.replace(os.path.sep, '_').lower()

    @property
    def url(self):
        """The url on jupyter nbviewer for this notebook or None if unknown"""
        if self._url is not None:
            url = self._url
        else:
            url = getattr(self.nb.metadata, 'url', None)
        if url is not None:
            return nbviewer_link(url)

    @property
    def remove_tags(self):
        return any(self.tag_options.values())

    def __init__(self, infile, outfile, disable_warnings=True,
                 preprocess=True, clear=True, code_example=None,
                 supplementary_files=None, other_supplementary_files=None,
                 thumbnail_figure=None, url=None, insert_bokeh=False,
                 insert_bokeh_widgets=False, tag_options={}):
        """
        Parameters
        ----------
        infile: str
            path to the existing notebook
        outfile: str
            path to the new notebook
        disable_warnings: bool
            Boolean to control whether warnings shall be included in the rst
            file or not
        preprocess: bool
            If True, the notebook is processed when generating the rst file
        clear: bool
            If True, the output in the download notebook is cleared
        code_example: str
            A python code sample that shall be used instead of a thumbnail
            figure in the gallery. Note that you can also include a
            ``'code_example'`` key in the metadata of the notebook
        supplementary_files: list of str
            Supplementary data files that shall be copied to the output
            directory and inserted in the rst file for download
        other_supplementary_files: list of str
            Other supplementary data files that shall be copied but not
            inserted for download
        thumbnail_figure: int
            The number of the figure that shall be used for download or a path
            to a file
        url: str
            The url where to download the notebook
        insert_bokeh: False or str
            The version string for bokeh to use for the style sheet
        insert_bokeh_widgets: bool or str
            The version string for bokeh to use for the widgets style sheet
        tag_options: dict
            A dictionary with traitlets for the
            :class:`nbconvert.preprocessors.TagRemovePreprocessor`"""
        self.infile = infile
        self.outfile = outfile
        self.preprocess = preprocess
        self.clear = clear
        self._code_example = code_example
        self._supplementary_files = supplementary_files
        self._other_supplementary_files = other_supplementary_files
        self._thumbnail_figure = thumbnail_figure
        self._url = url
        self.insert_bokeh = insert_bokeh
        self.insert_bokeh_widgets = insert_bokeh_widgets
        self.tag_options = tag_options
        self.process_notebook(disable_warnings)
        self.create_thumb()

    def get_out_file(self, ending='rst'):
        """get the output file with the specified `ending`"""
        return os.path.splitext(self.outfile)[0] + os.path.extsep + ending

    def process_notebook(self, disable_warnings=True):
        """Process the notebook and create all the pictures and files

        This method runs the notebook using the :mod:`nbconvert` and
        :mod:`nbformat` modules. It creates the :attr:`outfile` notebook,
        a python and a rst file"""
        infile = self.infile
        outfile = self.outfile
        in_dir = os.path.dirname(infile) + os.path.sep
        odir = os.path.dirname(outfile) + os.path.sep
        create_dirs(os.path.join(odir, 'images'))
        ep = nbconvert.preprocessors.ExecutePreprocessor(
            timeout=300)
        cp = nbconvert.preprocessors.ClearOutputPreprocessor(
            timeout=300)

        self.nb = nb = nbformat.read(infile, nbformat.current_nbformat)
        # disable warnings in the rst file
        if disable_warnings:
            for i, cell in enumerate(nb.cells):
                if cell['cell_type'] == 'code':
                    cell = cell.copy()
                    break
            cell = cell.copy()
            cell.source = """
import logging
logging.captureWarnings(True)
logging.getLogger('py.warnings').setLevel(logging.ERROR)
"""
            nb.cells.insert(i, cell)
        # write and process rst_file
        if self.preprocess:
            t = dt.datetime.now()
            logger.info('Processing %s', self.infile)
            try:
                ep.preprocess(nb, {'metadata': {'path': in_dir}})
            except nbconvert.preprocessors.execute.CellExecutionError:
                logger.critical(
                    'Error while processing %s!', self.infile, exc_info=True)
            else:
                logger.info('Done. Seconds needed: %i',
                            (dt.datetime.now() - t).seconds)
            if disable_warnings:
                nb.cells.pop(i)

        self.py_file = self.get_out_file('py')

        if self.remove_tags:
            tp = nbconvert.preprocessors.TagRemovePreprocessor(timeout=300)
            for key, val in self.tag_options.items():
                setattr(tp, key, set(val))
            nb4rst = deepcopy(nb)
            tp.preprocess(nb4rst, {'metadata': {'path': in_dir}})
        else:
            nb4rst = nb

        self.create_rst(nb4rst, in_dir, odir)

        if self.clear:
            cp.preprocess(nb, {'metadata': {'path': in_dir}})
        # write notebook file
        nbformat.write(nb, outfile)
        self.create_py(nb)

    def create_rst(self, nb, in_dir, odir):
        """Create the rst file from the notebook node"""
        exporter = nbconvert.RSTExporter()
        raw_rst, resources = exporter.from_notebook_node(nb)
        # remove ipython magics
        rst_content = ''
        i0 = 0
        m = None
        # HACK: we insert the bokeh style sheets here as well, since for some
        # themes (e.g. the sphinx_rtd_theme) it is not sufficient to include
        # the style sheets only via app.add_stylesheet
        bokeh_str = ''
        if 'bokeh' in raw_rst and self.insert_bokeh:
            bokeh_str += self.BOKEH_TEMPLATE.format(
                version=self.insert_bokeh)
        if 'bokeh' in raw_rst and self.insert_bokeh_widgets:
            bokeh_str += self.BOKEH_WIDGETS_TEMPLATE.format(
                version=self.insert_bokeh_widgets)
        for m in code_blocks.finditer(raw_rst):
            lines = m.group().splitlines(True)
            header, content = lines[0], ''.join(lines[1:])
            no_magics = magic_patt.sub('\g<1>', content)
            # if the code cell only contained magic commands, we skip it
            if no_magics.strip():
                rst_content += (
                    raw_rst[i0:m.start()] + bokeh_str + header + no_magics)
                bokeh_str = ''
                i0 = m.end()
            else:
                rst_content += raw_rst[i0:m.start()]
                i0 = m.end()
        if m is not None:
            rst_content += bokeh_str + raw_rst[m.end():]
        else:
            rst_content = raw_rst
        rst_content = '.. _%s:\n\n' % self.reference + \
            rst_content
        url = self.url
        if url is not None:
            rst_content += self.CODE_DOWNLOAD_NBVIEWER.format(
                pyfile=os.path.basename(self.py_file),
                nbfile=os.path.basename(self.outfile),
                url=url)
        else:
            rst_content += self.CODE_DOWNLOAD.format(
                pyfile=os.path.basename(self.py_file),
                nbfile=os.path.basename(self.outfile))
        supplementary_files = self.supplementary_files
        other_supplementary_files = self.other_supplementary_files
        if supplementary_files or other_supplementary_files:
            for f in (supplementary_files or []) + (
                    other_supplementary_files or []):
                if not os.path.exists(os.path.join(odir, f)):
                    copyfile(os.path.join(in_dir, f), os.path.join(odir, f))
        if supplementary_files:
            rst_content += self.data_download(supplementary_files)

        rst_file = self.get_out_file()
        outputs = sorted(resources['outputs'], key=rst_content.find)
        base = os.path.join('images', os.path.splitext(
            os.path.basename(self.infile))[0] + '_%i.png')
        out_map = {os.path.basename(original): base % i
                   for i, original in enumerate(outputs)}
        for original, final in six.iteritems(out_map):
            rst_content = rst_content.replace(original, final)
        with open(rst_file, 'w') \
                as f:
            f.write(rst_content.rstrip() + '\n')
        pictures = []
        for original in outputs:
            fname = os.path.join(odir, out_map[os.path.basename(original)])
            pictures.append(fname)
            if six.PY3:
                f = open(fname, 'w+b')
            else:
                f = open(fname, 'w')
            f.write(resources['outputs'][original])
            f.close()
        self.pictures = pictures

    def create_py(self, nb, force=False):
        """Create the python script from the notebook node"""
        # Although we would love to simply use ``nbconvert.export_python(nb)``
        # this causes troubles in other cells processed by the ipython
        # directive. Instead of getting something like ``Out [5]:``, we get
        # some weird like '[0;31mOut[[1;31m5[0;31m]: [0m' which look like
        # color information if we allow the call of nbconvert.export_python
        if list(map(int, re.findall('\d+', nbconvert.__version__))) >= [4, 2]:
            py_file = os.path.basename(self.py_file)
        else:
            py_file = self.py_file
        try:
            level = logger.logger.level
        except AttributeError:
            level = logger.level
        spr.call(['jupyter', 'nbconvert', '--to=python',
                  '--output=' + py_file, '--log-level=%s' % level,
                  self.outfile])
        with open(self.py_file) as f:
            py_content = f.read()
        # comment out ipython magics
        py_content = re.sub('^\s*get_ipython\(\).magic.*', '# \g<0>',
                            py_content, flags=re.MULTILINE)
        with open(self.py_file, 'w') as f:
            f.write(py_content)

    def data_download(self, files):
        """Create the rst string to download supplementary data"""
        if len(files) > 1:
            return self.DATA_DOWNLOAD % (
                ('\n\n' + ' '*8) + ('\n' + ' '*8).join(
                    '* :download:`%s`' % f for f in files))
        return self.DATA_DOWNLOAD % ':download:`%s`' % files[0]

    def create_thumb(self):
        """Create the thumbnail for html output"""
        thumbnail_figure = self.copy_thumbnail_figure()
        if thumbnail_figure is not None:
            if isinstance(thumbnail_figure, six.string_types):
                pic = thumbnail_figure
            else:
                pic = self.pictures[thumbnail_figure]
            self.save_thumbnail(pic)
        else:
            for pic in self.pictures[::-1]:
                if pic.endswith('png'):
                    self.save_thumbnail(pic)
                    return

    def get_description(self):
        """Get summary and description of this notebook"""
        def split_header(s, get_header=True):
            s = s.lstrip().rstrip()
            parts = s.splitlines()
            if parts[0].startswith('#'):
                if get_header:
                    header = re.sub('#+\s*', '', parts.pop(0))
                    if not parts:
                        return header, ''
                else:
                    header = ''
                rest = '\n'.join(parts).lstrip().split('\n\n')
                desc = rest[0].replace('\n', ' ')
                return header, desc
            else:
                if get_header:
                    if parts[0].startswith(('=', '-')):
                        parts = parts[1:]
                    header = parts.pop(0)
                    if parts and parts[0].startswith(('=', '-')):
                        parts.pop(0)
                    if not parts:
                        return header, ''
                else:
                    header = ''
                rest = '\n'.join(parts).lstrip().split('\n\n')
                desc = rest[0].replace('\n', ' ')
                return header, desc

        first_cell = self.nb['cells'][0]

        if not first_cell['cell_type'] == 'markdown':
            return '', ''
        header, desc = split_header(first_cell['source'])
        if not desc and len(self.nb['cells']) > 1:
            second_cell = self.nb['cells'][1]
            if second_cell['cell_type'] == 'markdown':
                _, desc = split_header(second_cell['source'], False)
        return header, desc

    def scale_image(self, in_fname, out_fname, max_width, max_height):
        """Scales an image with the same aspect ratio centered in an
           image with a given max_width and max_height
           if in_fname == out_fname the image can only be scaled down
        """
        # local import to avoid testing dependency on PIL:
        try:
            from PIL import Image
        except ImportError:
            import Image
        img = Image.open(in_fname)
        width_in, height_in = img.size
        scale_w = max_width / float(width_in)
        scale_h = max_height / float(height_in)

        if height_in * scale_w <= max_height:
            scale = scale_w
        else:
            scale = scale_h

        if scale >= 1.0 and in_fname == out_fname:
            return

        width_sc = int(round(scale * width_in))
        height_sc = int(round(scale * height_in))

        # resize the image
        img.thumbnail((width_sc, height_sc), Image.ANTIALIAS)

        # insert centered
        thumb = Image.new('RGB', (max_width, max_height), (255, 255, 255))
        pos_insert = (
            (max_width - width_sc) // 2, (max_height - height_sc) // 2)
        thumb.paste(img, pos_insert)

        thumb.save(out_fname)

    def save_thumbnail(self, image_path):
        """Save the thumbnail image"""
        thumb_dir = os.path.join(os.path.dirname(image_path), 'thumb')
        create_dirs(thumb_dir)

        thumb_file = os.path.join(thumb_dir,
                                  '%s_thumb.png' % self.reference)
        if os.path.exists(image_path):
            logger.info('Scaling %s to thumbnail %s', image_path, thumb_file)
            self.scale_image(image_path, thumb_file, 400, 280)
        self.thumb_file = thumb_file

    def get_thumb_path(self, base_dir):
        """Get the relative path to the thumb nail of this notebook"""
        return os.path.relpath(self.thumb_file, base_dir)

    def copy_thumbnail_figure(self):
        """The integer of the thumbnail figure"""
        ret = None
        if self._thumbnail_figure is not None:
            if not isstring(self._thumbnail_figure):
                ret = self._thumbnail_figure
            else:
                ret = osp.join(osp.dirname(self.outfile),
                               osp.basename(self._thumbnail_figure))
                copyfile(self._thumbnail_figure, ret)
                return ret
        elif hasattr(self.nb.metadata, 'thumbnail_figure'):
            if not isstring(self.nb.metadata.thumbnail_figure):
                ret = self.nb.metadata.thumbnail_figure
            else:
                ret = osp.join(osp.dirname(self.outfile), 'images',
                               osp.basename(self.nb.metadata.thumbnail_figure))
                copyfile(osp.join(osp.dirname(self.infile),
                                  self.nb.metadata.thumbnail_figure),
                         ret)
        return ret


class Gallery(object):
    """Class to create one or more example gallerys"""

    #: The input directories
    in_dir = []

    #: The output directories
    out_dir = []

    @property
    def urls(self):
        return self._all_urls[self._in_dir_count]

    def __init__(self, examples_dirs=['../examples'], gallery_dirs=None,
                 pattern='example_.+.ipynb', disable_warnings=True,
                 dont_preprocess=[], preprocess=True, clear=True,
                 dont_clear=[], code_examples={}, supplementary_files={},
                 other_supplementary_files={}, thumbnail_figures={},
                 urls=None, insert_bokeh=False, insert_bokeh_widgets=False,
                 remove_all_outputs_tags=set(), remove_cell_tags=set(),
                 remove_input_tags=set(), remove_single_output_tags=set()):
        """
        Parameters
        ----------
        examples_dirs: list of str
            list containing the directories to loop through. Default:
            ``['../examples']``
        gallerys_dirs: list of str
            None or list of directories where the rst files shall be created.
            If None, the current working directory and the name of the
            corresponding directory in the `examples_dirs` is used. Default:
            ``None``
        pattern: list of str
            str. The pattern to use to find the ipython  notebooks.
            Default: ``'example_.+.ipynb'``
        disable_warnings: bool
            Boolean controlling whether warnings shall be disabled when
            processing the examples. Defaultt: True
        preprocess: bool or list of str
            If True, all examples (except those specified in the
            `dont_preprocess` item) will be preprocessed when creating the rst
            files. Otherwise it might be a list of files that shall be
            preprocessed.
        dont_preprocess: bool or list of str
            If True, no example will be preprocessed when creating the rst
            files. Otherwise it might be a list of files that shall not be
            preprocessed
        clear: bool or list of str
            If True, the output in all notebooks to download will be cleared.
            Otherwise it might be a list of notebook files of whom to clear the
            output
        dont_clear: bool or list of str
            If True, the output in all notebooks to download will not be
            cleared. Otherwise it might be a list of notebook files  of whom
            not to clear the output
        code_examples: dict
            A mapping from filename to code samples that shall be used instead
            of a thumbnail figure in the gallery. Note that you can also
            include a  ``'code_example'`` key in the metadata of the notebook
        supplementary_files: dict
            A mapping from filename to a list of supplementary data files that
            shall copied to the documentation directory and can be downloaded.
            Note that you can also include a  ``'supplementary_files'`` key in
            the metadata of the notebook
        other_supplementary_files: dict
            A mapping from filename to a list of other supplementary data files
            that shall copied to the documentation directory but can not be
            downloaded (e.g. pictures).
            Note that you can also include a  ``'other_supplementary_files'``
            key in the metadata of the notebook
        thumbnail_figures: dict
            A mapping from filename to an integer or the path of a file to use
            for the thumbnail
        urls: str or dict
            The urls where to download the notebook. Necessary to provide a
            link to the jupyter nbviewer. If string, the path to the notebook
            will be appended for each example notebook. Otherwise it should be
            a dictionary with links for the given notebook
        insert_bokeh: bool or str
            If True, the bokeh js [1]_ and the stylesheet [2]_ are inserted in
            the notebooks that have bokeh loaded (using the installed or
            specified bokeh version)
        insert_bokeh_widgets: bool or str
            If True, the bokeh widget js [3]_ is inserted in the notebooks that
            have bokeh loaded (using the installed or specified bokeh version)
        remove_all_outputs_tags: set
            Tags indicating cells for which the outputs are to be removed,
            matches tags in cell.metadata.tags.
        remove_cell_tags: set
            Tags indicating which cells are to be removed, matches tags in
            cell.metadata.tags.
        remove_input_tags: set
            Tags indicating cells for which input is to be removed,
            matches tags in cell.metadata.tags.
        remove_single_output_tags: set
            Tags indicating which individual outputs are to be removed, matches
            output i tags in cell.outputs[i].metadata.tags.

        References
        ----------
        .. [1] http://cdn.pydata.org/bokeh/release/bokeh-0.12.0.min.js
        .. [2] http://cdn.pydata.org/bokeh/release/bokeh-0.12.0.min.css
        .. [3] http://cdn.pydata.org/bokeh/release/bokeh-widgets-0.12.0.min.js
        """
        if isinstance(examples_dirs, six.string_types):
            examples_dirs = [examples_dirs]
        if gallery_dirs is None:
            gallery_dirs = list(map(os.path.basename, examples_dirs))
        if isinstance(gallery_dirs, six.string_types):
            gallery_dirs = [gallery_dirs]

        for i, s in enumerate(examples_dirs):
            if not s.endswith(os.path.sep):
                examples_dirs[i] += os.path.sep

        for i, s in enumerate(gallery_dirs):
            if not s.endswith(os.path.sep):
                gallery_dirs[i] += os.path.sep

        self.in_dir = examples_dirs
        self.out_dir = gallery_dirs

        if isinstance(pattern, six.string_types):
            pattern = re.compile(pattern)
        self.pattern = pattern
        self.disable_warnings = disable_warnings
        self.dont_preprocess = dont_preprocess
        self.preprocess = preprocess
        self.clear = clear
        self.dont_clear = dont_clear
        self.code_examples = code_examples
        self.supplementary_files = supplementary_files
        self.osf = other_supplementary_files
        self.thumbnail_figures = thumbnail_figures
        if urls is None or isinstance(urls, (dict, six.string_types)):
            urls = [urls] * len(self.in_dir)
        self._all_urls = urls
        if insert_bokeh and not isstring(insert_bokeh):
            import bokeh
            insert_bokeh = bokeh.__version__
        if insert_bokeh_widgets and not isstring(insert_bokeh_widgets):
            import bokeh
            insert_bokeh_widgets = bokeh.__version__
        tag_options = {
            'remove_all_outputs_tags': remove_all_outputs_tags,
            'remove_cell_tags': remove_cell_tags,
            'remove_input_tags': remove_input_tags,
            'remove_single_output_tags': remove_single_output_tags}
        self._nbp_kws = {'insert_bokeh': insert_bokeh,
                         'insert_bokeh_widgets': insert_bokeh_widgets,
                         'tag_options': tag_options}

    def process_directories(self):
        """Create the rst files from the input directories in the
        :attr:`in_dir` attribute"""
        for i, (base_dir, target_dir, paths) in enumerate(zip(
                self.in_dir, self.out_dir, map(os.walk, self.in_dir))):
            self._in_dir_count = i
            self.recursive_processing(base_dir, target_dir, paths)

    def recursive_processing(self, base_dir, target_dir, it):
        """Method to recursivly process the notebooks in the `base_dir`

        Parameters
        ----------
        base_dir: str
            Path to the base example directory (see the `examples_dir`
            parameter for the :class:`Gallery` class)
        target_dir: str
            Path to the output directory for the rst files (see the
            `gallery_dirs` parameter for the :class:`Gallery` class)
        it: iterable
            The iterator over the subdirectories and files in `base_dir`
            generated by the :func:`os.walk` function"""
        try:
            file_dir, dirs, files = next(it)
        except StopIteration:
            return '', []
        readme_files = {'README.md', 'README.rst', 'README.txt'}
        if readme_files.intersection(files):
            foutdir = file_dir.replace(base_dir, target_dir)
            create_dirs(foutdir)
            this_nbps = [
                NotebookProcessor(
                    infile=f,
                    outfile=os.path.join(foutdir, os.path.basename(f)),
                    disable_warnings=self.disable_warnings,
                    preprocess=(
                        (self.preprocess is True or f in self.preprocess) and
                        not (self.dont_preprocess is True or
                             f in self.dont_preprocess)),
                    clear=((self.clear is True or f in self.clear) and not
                           (self.dont_clear is True or f in self.dont_clear)),
                    code_example=self.code_examples.get(f),
                    supplementary_files=self.supplementary_files.get(f),
                    other_supplementary_files=self.osf.get(f),
                    thumbnail_figure=self.thumbnail_figures.get(f),
                    url=self.get_url(f.replace(base_dir, '')),
                    **self._nbp_kws)
                for f in map(lambda f: os.path.join(file_dir, f),
                             filter(self.pattern.match, files))]
            readme_file = next(iter(readme_files.intersection(files)))
        else:
            return '', []
        labels = OrderedDict()
        this_label = 'gallery_' + foutdir.replace(os.path.sep, '_')
        if this_label.endswith('_'):
            this_label = this_label[:-1]
        for d in dirs:
            label, nbps = self.recursive_processing(
                base_dir, target_dir, it)
            if label:
                labels[label] = nbps
        s = ".. _%s:\n\n" % this_label
        with open(os.path.join(file_dir, readme_file)) as f:
            s += f.read().rstrip() + '\n\n'

        s += "\n\n.. toctree::\n\n"
        s += ''.join('    %s\n' % os.path.splitext(os.path.basename(
            nbp.get_out_file()))[0] for nbp in this_nbps)
        for d in dirs:
            findex = os.path.join(d, 'index.rst')
            if os.path.exists(os.path.join(foutdir, findex)):
                s += '    %s\n' % os.path.splitext(findex)[0]

        s += '\n'

        for nbp in this_nbps:
            code_div = nbp.code_div
            if code_div is not None:
                s += code_div + '\n'
            else:
                s += nbp.thumbnail_div + '\n'
        s += "\n.. raw:: html\n\n    <div style='clear:both'></div>\n"
        for label, nbps in labels.items():
            s += '\n.. only:: html\n\n    .. rubric:: :ref:`%s`\n\n' % (
                label)
            for nbp in nbps:
                code_div = nbp.code_div
                if code_div is not None:
                    s += code_div + '\n'
                else:
                    s += nbp.thumbnail_div + '\n'
            s += "\n.. raw:: html\n\n    <div style='clear:both'></div>\n"

        s += '\n'

        with open(os.path.join(foutdir, 'index.rst'), 'w') as f:
            f.write(s)
        return this_label, list(chain(this_nbps, *labels.values()))

    @classmethod
    def from_sphinx(cls, app):
        """Class method to create a :class:`Gallery` instance from the
        configuration of a sphinx application"""
        app.config.html_static_path.append(os.path.join(
            os.path.dirname(__file__), '_static'))
        config = app.config.example_gallery_config

        insert_bokeh = config.get('insert_bokeh')
        if insert_bokeh:
            if not isstring(insert_bokeh):
                import bokeh
                insert_bokeh = bokeh.__version__
            app.add_stylesheet(
                NotebookProcessor.BOKEH_STYLE_SHEET.format(
                    version=insert_bokeh))
            app.add_javascript(
                NotebookProcessor.BOKEH_JS.format(version=insert_bokeh))

        insert_bokeh_widgets = config.get('insert_bokeh_widgets')
        if insert_bokeh_widgets:
            if not isstring(insert_bokeh_widgets):
                import bokeh
                insert_bokeh_widgets = bokeh.__version__
            app.add_stylesheet(
                NotebookProcessor.BOKEH_WIDGETS_STYLE_SHEET.format(
                    version=insert_bokeh_widgets))
            app.add_javascript(
                NotebookProcessor.BOKEH_WIDGETS_JS.format(
                    version=insert_bokeh_widgets))

        if not app.config.process_examples:
            return
        cls(**app.config.example_gallery_config).process_directories()

    def get_url(self, nbfile):
        """Return the url corresponding to the given notebook file

        Parameters
        ----------
        nbfile: str
            The path of the notebook relative to the corresponding
            :attr:``in_dir``

        Returns
        -------
        str or None
            The url or None if no url has been specified
        """
        urls = self.urls
        if isinstance(urls, dict):
            return urls.get(nbfile)
        elif isstring(urls):
            if not urls.endswith('/'):
                urls += '/'
            return urls + nbfile


def align(argument):
    """Conversion function for the "align" option."""
    return directives.choice(argument, ('left', 'center', 'right'))


class LinkGalleriesDirective(Directive):

    has_content = True

    if hasattr(directives, 'images'):
        option_spec = directives.images.Figure.option_spec
    else:
        option_spec = {'alt': directives.unchanged,
                       'height': directives.nonnegative_int,
                       'width': directives.nonnegative_int,
                       'scale': directives.nonnegative_int,
                       'align': align
                       }

    def create_image_nodes(self, header, thumb_url, key, link_url=None):
        options = {'target': link_url} if link_url else {}
        options.update(self.options)
        d1 = directives.misc.Raw(
            'raw', ['html'], {}, ViewList([
                '<div class="sphx-glr-thumbContainer">']
                ),
            self.lineno, self.content_offset, self.block_text, self.state,
            self.state_machine)
        d = directives.images.Figure(
            'image', [thumb_url], options, ViewList([':ref:`%s`' % key]),
            self.lineno, self.content_offset, self.block_text, self.state,
            self.state_machine)
        d2 = directives.misc.Raw(
            'raw', ['html'], {}, ViewList(['</div>']),
            self.lineno, self.content_offset, self.block_text, self.state,
            self.state_machine)
        return list(chain(d1.run(), d.run(), d2.run()))

    def get_outdirs(self):
        conf = self.env.config.example_gallery_config
        gallery_dirs = conf.get('gallery_dirs')
        if not gallery_dirs:
            examples_dirs = conf.get('example_dirs', ['../examples'])
            if isinstance(examples_dirs, six.string_types):
                examples_dirs = [examples_dirs]
            gallery_dirs = list(map(osp.basename, examples_dirs))
        if isinstance(gallery_dirs, six.string_types):
            gallery_dirs = [gallery_dirs]
        for i, s in enumerate(gallery_dirs):
            if not s.endswith(os.path.sep):
                gallery_dirs[i] += os.path.sep
        return gallery_dirs

    def run(self):
        self.env = self.state.document.settings.env
        conf = self.env.config
        ret = nodes.paragraph()
        try:
            inventory = self.env.intersphinx_named_inventory
        except AttributeError:
            warn('The %s directive requires the sphinx.ext.intersphinx '
                 'extension!', self.name)
            return [ret]
        for pkg_str in self.content:
            try:
                pkg, directory = pkg_str.split()
            except ValueError:
                pkg, directory = pkg_str, ''
            directory_ = directory.replace('/', '_').lower()
            if pkg == conf.project:
                pass
                if not directory:
                    directories = self.get_outdirs()
                else:
                    directories = [directory]
                for directory in directories:
                    for file_dir, dirs, files in os.walk(directory):
                        if not file_dir.endswith(osp.sep):
                            file_dir += osp.sep
                        file_dir_ = file_dir.replace(osp.sep, '_').lower()
                        if 'index.rst' in files:
                            for f in files:
                                if f.endswith('.ipynb'):
                                    ref = 'gallery_' + file_dir_ + f
                                    thumb = osp.join(
                                        file_dir, 'images', 'thumb',
                                        ref + '_thumb.png')
                                    if osp.isabs(thumb):
                                        thumb = osp.relpath(thumb,
                                                            self.env.srcdir)
                                    header = ':ref:`%s`' % (ref, )
                                    ret.extend(self.create_image_nodes(
                                        header, thumb, ref))
            else:
                try:
                    refs = inventory[pkg]['std:label']
                except KeyError:
                    warn('Could not load the inventory of %s!', pkg)
                    continue
                base_url = self.env.config.intersphinx_mapping[pkg][0]
                if not base_url.endswith('/'):
                    base_url += '/'
                for key, val in refs.items():
                    if (key.startswith('gallery_' + directory_) and
                            key.endswith('.ipynb')):
                        link_url = val[2]
                        header = val[3]
                        thumb_url = base_url + '_images/%s_thumb.png' % key
                        ret.extend(self.create_image_nodes(
                            header, thumb_url, '%s:%s' % (pkg, key),
                            link_url))
        ret.extend(directives.misc.Raw(
            'raw', ['html'], {}, ViewList(["<div style='clear:both'></div>"]),
            self.lineno, self.content_offset, self.block_text, self.state,
            self.state_machine).run())
        return [ret]


#: dictionary containing the configuration of the example gallery.
#:
#: Possible keys for the dictionary are the initialization keys of the
#: :class:`Gallery` class
gallery_config = {
    'examples_dirs': ['../examples'],
    'gallery_dirs': None,
    'pattern': 'example_.+.ipynb',
    'disable_warnings': True,
    'preprocess': True,
    'dont_preprocess': [],
    'clear': True,
    'dont_clear': [],
    'code_examples': {},
    'supplementary_files': {},
    'insert_bokeh': False,
    'insert_bokeh_widgets': False}


#: Boolean controlling whether the rst files shall created and examples
#: processed
process_examples = True


def setup(app):
    app.add_config_value('process_examples', process_examples, 'html')

    app.add_config_value('example_gallery_config', gallery_config, 'html')

    app.add_stylesheet('example_gallery_styles.css')

    app.add_directive('linkgalleries', LinkGalleriesDirective)

    app.connect('builder-inited', Gallery.from_sphinx)
