.. _install:

Installation
============

How to install
--------------

Installation using pip
^^^^^^^^^^^^^^^^^^^^^^
If you do not want to use conda for managing your python packages, you can also
use the python package manager ``pip`` and install via::

    $ pip install sphinx-nbexamples

If you want to preprocess your notebooks before including them in the
documentation, you might also have to install the ipykernel module via::

    $ pip install ipykernel

and register the kernel depending on the kernel name in your notebooks via::

    $ python -m ipykernel install --user --name <kernel-name> --display-name <kernel-name>

where the ``<kernel-name>`` should be replaced by the kernel name as it is used
in the examples.

.. note::

    If your examples require additional packages, you of course have to install
    them by yourself

Installation from source
^^^^^^^^^^^^^^^^^^^^^^^^
You can as well install the package from the github_ via::

    $ python setup.py install


Usage on readthedocs.org_
-------------------------
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


Running the tests
-----------------
We use pytest_ for our testing, so simply install it and run::

    $ py.test

or in the downloaded directory from github_ run

    $ python setup.py pytest

Building the docs
-----------------
To build the docs, check out the github_ repository and install the
requirements in ``'docs/environment.yml'``. The easiest way to do this is via
anaconda by typing::

    $ conda env create -f docs/environment.yml
    $ source activate sphinx_nbexamples_docs
    $ conda install ipykernel sphinx_rtd_theme

Then build the docs via::

    $ cd docs
    $ make html

.. _github: https://github.com/Chilipp/sphinx-nbexamples
.. _pytest: https://pytest.org/latest/contents.html
