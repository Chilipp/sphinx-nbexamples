"""Create an example gallery out of a bunch of ipython notebooks

This sphinx extension extracts the ipython notebooks in a given folder to
create an example gallery. It provides the follwing configuration values
for you sphinx configuration file ``'conf.py'``:

.. autosummary::

    process_examples
    gallery_config

The package requires the style sheet ``'example_gallery_styles.css'`` which
you can find in the ``'_static'`` directory belonging to this file, copied
into the ``'_static'`` directory of you docs.

Notes
-----
This module was motivated by the
`sphinx-gallery <http://sphinx-gallery.readthedocs.org/en/latest/>` module
0.1.1 by Oscar Najera and in fact uses it's html containers for creating the
thumbnails and the download containers"""
from __future__ import division
import datetime as dt
import os
import re
import six
from collections import defaultdict
from itertools import chain
import nbconvert
import nbformat
from shutil import copyfile
from psyplot.compat.pycompat import map, OrderedDict
import logging
import subprocess as spr

__version__ = '0.0.0.dev0'

__author__ = "Philipp Sommer"

logger = logging.getLogger(__name__)


def create_dirs(*dirs):
    for d in dirs:
        if os.path.exists(d) and not os.path.isdir(d):
            raise IOError("Could not create directory %s because an "
                          "ordinary file with that name exists already!")
        elif not os.path.exists(d):
            os.makedirs(d)


NOIMAGE = os.path.join(os.path.dirname(__file__), '_static', 'no_image.png')


class NotebookProcessor(object):
    """Class to run process one ipython notebook and create the necessary files
    """

    #: base string for downloading the python file and ipython notebook
    CODE_DOWNLOAD = """

.. only:: html

    .. container:: sphx-glr-download

        **Download python file:** :download:`%s`

        **Download IPython notebook:** :download:`%s`
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
    def reference(self):
        """The rst label of this example"""
        return 'gallery_' + self.outfile.replace(os.path.sep, '_')

    def __init__(self, infile, outfile, disable_warnings=True,
                 preprocess=True, clear=True):
        """
        Parameters
        ----------
        infile: str
            path to the existing notebook
        outfile: str
            path to the new notebook
        disable_warnings: bool
            Boolean to control whether warnings shall be included in the rst
            file or not"""
        self.infile = infile
        self.outfile = outfile
        self.preprocess = preprocess
        self.clear = clear
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
            timeout=300, kernel_name='python2')
        cp = nbconvert.preprocessors.ClearOutputPreprocessor(
            timeout=300, kernel_name='python2')

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
                logging.getLogger(__name__).critical(
                    'Error while processing %s!', self.infile, exc_info=True)
            else:
                logger.info('Done. Seconds needed: %i',
                            (dt.datetime.now() - t).seconds)
            if disable_warnings:
                nb.cells.pop(i)

        self.py_file = self.get_out_file('py')

        self.create_rst(nb, in_dir, odir)

        if self.clear:
            cp.preprocess(nb, {'metadata': {'path': in_dir}})
        # write notebook file
        nbformat.write(nb, outfile)
        self.create_py(nb)

    def create_rst(self, nb, in_dir, odir):
        """Create the rst file from the notebook node"""
        rst_content, resources = nbconvert.export_rst(nb)
        # remove ipython magics
        rst_content = re.sub('^\s+%.*\n', '', rst_content, flags=re.MULTILINE)
        rst_content = '.. _%s:\n\n' % self.reference + \
            rst_content
        rst_content += self.CODE_DOWNLOAD % (
            os.path.basename(self.py_file), os.path.basename(self.outfile))
        if hasattr(nb.metadata, 'supplementary_files'):
            for f in nb.metadata.supplementary_files:
                if not os.path.exists(os.path.join(odir, f)):
                    copyfile(os.path.join(in_dir, f), os.path.join(odir, f))
            rst_content += self.data_download(nb.metadata.supplementary_files)

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
        spr.call(['jupyter', 'nbconvert', '--to=python',
                  '--output=' + py_file, '--log-level=%s' % logger.level,
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
        base_image_name = os.path.splitext(os.path.basename(image_path))[0]
        thumb_dir = os.path.join(os.path.dirname(image_path), 'thumb')
        create_dirs(thumb_dir)

        thumb_file = os.path.join(thumb_dir,
                                  'sphx_glr_%s_thumb.png' % base_image_name)
        if os.path.exists(image_path):
            self.scale_image(image_path, thumb_file, 400, 280)
        self.thumb_file = thumb_file

    def get_thumb_path(self, base_dir):
        """Get the relative path to the thumb nail of this notebook"""
        return os.path.relpath(self.thumb_file, base_dir)


class Gallery(object):
    """Class to create one or more example gallerys"""

    def __init__(self, examples_dirs=['../examples'], gallery_dirs=None,
                 pattern='example_.+.ipynb', disable_warnings=True,
                 dont_preprocess=[], preprocess=True, clear=True,
                 dont_clear=[]):
        """
        Parameters
        ----------
        examples_dirs
            list containing the directories to loop through. Default:
            ``['../examples']``
        gallerys_dirs
            None or list of directories where the rst files shall be created.
            If None, the current working directory and the name of the
            corresponding directory in the `examples_dirs` is used. Default:
            ``None``
        pattern
            str. The pattern to use to find the ipython  notebooks.
            Default: ``'example_.+.ipynb'``
        disable_warnings
            Boolean controlling whether warnings shall be disabled when
            processing the examples. Defaultt: True
        preprocess
            If True, all examples (except those specified in the
            `dont_preprocess` item) will be preprocessed when creating the rst
            files. Otherwise it might be a list of files that shall be
            preprocessed.
        dont_preprocess
            If True, no example will be preprocessed when creating the rst
            files. Otherwise it might be a list of files that shall not be
            preprocessed
        clear
            If True, the output in all notebooks to download will be cleared.
            Otherwise it might be a list of notebook files of whom to clear the
            output
        dont_clear
            If True, the output in all notebooks to download will not be
            cleared. Otherwise it might be a list of notebook files  of whom
            not to clear the output"""

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

    def get_files(self, pattern):
        """Get input and output notebooks

        This method gets the files from the input directory that matches
        `pattern` and returns both, input files and output files

        Parameters
        ----------
        pattern: str or re pattern
            The pattern that has to match the filenames

        Returns
        -------
        dict
            A mapping from filenames in the :attr:`in_dir` to the corresponding
            filenames in the :attr:`out_dir`"""
        def get_ofile(odir, indir, infile):
            return infile.replace(indir, odir)
        if isinstance(pattern, six.string_types):
            pattern = re.compile(pattern)
        ret = defaultdict(dict)
        for indir, odir, paths in zip(self.in_dir, self.out_dir,
                                      map(os.walk, self.in_dir)):
            found = False
            for file_dir, dirs, files in paths:
                if 'README.rst' not in files:
                    continue
                foutdir = file_dir.replace(indir, odir + os.path.sep)
                for f in filter(pattern.match, files):
                    ret[(file_dir, foutdir)][os.path.join(file_dir, f)] = \
                        os.path.join(foutdir, f)
                found = True
            if not found:
                logger.warning('Could not find any notebook in %s!', indir)
        return ret

    def process_directories(self):
        """Create the rst files from the input directories in the
        :attr:`in_dir` attribute"""
        for base_dir, target_dir, paths in zip(self.in_dir, self.out_dir, map(
                os.walk, self.in_dir)):
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
                           (self.dont_clear is True or f in self.dont_clear)))
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
                s += nbp.thumbnail_div + '\n'
        s += "\n.. raw:: html\n\n    <div style='clear:both'></div>\n"
        for label, nbps in labels.items():
            s += '\n.. only:: html\n\n    .. rubric:: :ref:`%s`\n\n' % (
                label)
            for nbp in nbps:
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
        if not app.config.process_examples:
            return
        cls(**app.config.example_gallery_config).process_directories()


"""dictionary containing the configuration of the example gallery

Possible keys for the dictionary are the initialization keys of the
:class:`Gallery` class"""
gallery_config = {
    'examples_dirs': ['../examples'],
    'gallery_dirs': None,
    'pattern': 'example_.+.ipynb',
    'disable_warnings': True,
    'preprocess': True,
    'dont_preprocess': [],
    'clear': True,
    'dont_clear': []}


#: Boolean controlling whether the rst files shall created and examples
#: processed
process_examples = True


def setup(app):
    app.add_config_value('process_examples', process_examples, 'html')

    app.add_config_value('example_gallery_config', gallery_config, 'html')
    app.add_stylesheet('example_gallery_styles.css')

    app.connect('builder-inited', Gallery.from_sphinx)
