.. getting_started:

Getting started
===============

The module provides 2 additional configuration values.

.. confval:: process_examples

    If ``True``, (the default), then the notebook files are converted to rst.


.. confval:: example_gallery_config

    A dictionary with the parameters of the :class:`~sphinx_nbexamples.Gallery`
    class


By default, the sphinx-nbexamples package converts your jupyter notebook in a
specific directory into rst files to include it into your documentation. The
:confval:`process_examples` configuration value controls this conversion. If
switched off, no new files will be created.

The second configuration value, :confval:`example_gallery_config`, can be used
to control which examples are converted and how. They are simply the keyword
arguments for the :class:`~sphinx_nbexamples.Gallery` class, but we will go in
more detail in the next sections. But look into the :ref:`gallery_examples`
section to see the outcome of the gallery.


.. _nbstructure:

Structure of the notebooks
--------------------------
You are free to format your notebooks however you want. There are only 2
important features since we convert the notebook to a single html page:

1. The first cell must be a Markdown cell containing a title
2. The first cell should include a short summary which will then be shown as
   the tooltip in the summary


.. _basic_settings:

Choosing the examples
---------------------
The three keywords ``'examples_dirs', 'gallery_dirs'``, and ``'pattern'`` can
be used to select which notebooks shall be converted. The value for
``'example_dirs'`` is the path to the directory where your raw jupyter
notebooks are located. The ``'gallery_dirs'`` key on the other hand will point
to the directories where the converted notebooks will be. You can also provide
a list of example directories to create multiple galleries.

Finally the ``'pattern'`` corresponds to the filename pattern for the example
notebooks. Using the default pattern (``'example_.+.ipynb'``) implies, that
all your notebooks in the ``'example_dirs'`` starts with ``'example_'``


.. _preprocessing:

Preprocessing the examples or not
---------------------------------
When converting the examples, the default behaviour is to process the examples
as well. This is a good possibility if you have an automatic building of the
docs (e.g. using readthedocs.org_) to check that all your examples really work.
However, you might not want this for all your notebooks, because it eventually
takes a lot of time to process all the notebooks or it requires additional
libraries. Therefore you can use the ``'preprocess'`` and ``'dont_preprocess'``
keys so select which examples are processed.


.. _thumbnails:

Choosing the thumbnail
----------------------
As you see in our :ref:`example gallery <gallery_examples>`, little thumbnails
are created for each notebook. They can be chosen via

1. the ``'code_examples'`` key in the :confval:`example_gallery_config`
2. the ``'code_example'`` key in the meta data of the notebook
3. the ``'thumbnail_figures'`` key in the :confval:`example_gallery_config`
4. the key ``'thumbnail_figures'`` in the meta data of the notebook
5. automatically from the last matplotlib figure in the example notebook

Hence, if you do not specify either ``'code_examples'`` nor
``'thumbnail_figure'`` (which is the default), it looks for a matplotlib
plot in the notebook and uses this one.

Otherwise, you have the possibility to give a small code sample via the
``'code_examples'``  or use the ``'thumbnail_figure'``. The latter can
be the path to a picture (relative to the notebook) or a number to specify
which figure of the matplotlib figures to use.


.. _supp:

Providing supplementary files
-----------------------------
Sphinx-nbexamples automatically inserts links to download the jupyter notebook
and the converted python file. However, often your example requires additional
data files, etc. Here, you have two possibilities:

1. Specify the external data in the metadata of your notebook (see the
   :ref:`gallery_examples_example_basic.ipynb`)
2. Specify the external data in the ``'supplementary_files'`` key of your
   :confval:`example_gallery_config` specific for each notebook


.. _nbviewer:

Including a link to the nbviewer
--------------------------------
If your notebooks are also published online, you can embed a link to the
wonderful `jupyter nbviewer`_ in the documentation. You have multiple options
here
1. You can either specify the url for each notebook separately providing a
   mapping from notebook file to url in the ``'urls'`` keyword
2. Include a url key in the metadata of your notebook
3. specify one single url in the ``'urls'`` keyword for each example directory
   from the ``'example_dirs'`` keyword if you have all the example directories
   available online.

.. _jupyter nbviewer: https://nbviewer.jupyter.org


.. _bokeh:

Including bokeh
---------------
Note that bokeh needs a special treatment, especially when using the scheme
from readthedocs.org_, because it requires additional style sheets and javascript
files. So, if you have bokeh plots in your documentation, we recommend to

1. use the :func:`bokeh.io.output_notebook` function in your examples
2. disable the preprocessing for this notebook using the ``'dont_preprocess'``
   keyword
3. Give the bokeh version via the ``'insert_bokeh'`` keyword

If you furthermore use widgets from bokeh, use the ``'insert_bokeh_widgets'``
keyword, too.

.. note::

    We cannot extract a thumbnail figure for bokeh notebooks. Hence, you should
    provide it by yourself (see :ref:`thumbnails`).

Usage on readthedocs.org_
---------------------
When building your documentation on readthedocs.org_, you can either disable
the preprocessing of the notebooks via the :confval:`process_examples`
configuration value, e.g. via::

    on_rtd = os.environ.get('READTHEDOCS', None) == 'True'
    process_examples = not on_rtd

or::

    example_gallery_config['dont_preprocess'] = on_rtd

or you make sure that the virtual environment installs ipykernel and all the
other necessary packages for your examples and include::

    on_rtd = os.environ.get('READTHEDOCS', None) == 'True'
    if on_rtd:
        import subprocess as spr
        spr.call([sys.executable] +
                 ('-m ipykernel install --user --name python3 '
                  '--display-name python3').split())

in your ``'conf.py'`` of your sphinx documentation. Change ``'python3'`` to
the kernel name you are using in your examples.

.. _readthedocs.org: http://readthedocs.org
