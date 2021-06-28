=============================================================
Create an examples gallery with sphinx from Jupyter Notebooks
=============================================================

.. image:: http://unmaintained.tech/badge.svg
    :target: http://unmaintained.tech/
    :alt: No Maintenance Intended

**This module is not maintained. Please use** nbsphinx_ **instead!**

.. _nbsphinx: https://nbsphinx.readthedocs.io

.. start-badges
.. only:: html and not epub

    .. list-table::
        :stub-columns: 1
        :widths: 10 90

        * - docs
          - |docs|
        * - tests
          - |travis| |requires| |coveralls|
        * - package
          - |version| |conda| |github|
        * - implementations
          - |supported-versions| |supported-implementations|

    .. |docs| image:: https://readthedocs.org/projects/sphinx-nbexamples/badge/?version=latest
        :alt: Documentation Status
        :target: http://sphinx-nbexamples.readthedocs.io/en/latest/?badge=latest

    .. |travis| image:: https://travis-ci.org/Chilipp/sphinx-nbexamples.svg?branch=master
        :alt: Travis
        :target: https://travis-ci.org/Chilipp/sphinx-nbexamples

    .. |coveralls| image:: https://coveralls.io/repos/github/Chilipp/sphinx-nbexamples/badge.svg?branch=master
        :alt: Coverage
        :target: https://coveralls.io/github/Chilipp/sphinx-nbexamples?branch=master

    .. |requires| image:: https://requires.io/github/Chilipp/sphinx-nbexamples/requirements.svg?branch=master
        :alt: Requirements Status
        :target: https://requires.io/github/Chilipp/sphinx-nbexamples/requirements/?branch=master

    .. |version| image:: https://img.shields.io/pypi/v/sphinx-nbexamples.svg?style=flat
        :alt: PyPI Package latest release
        :target: https://pypi.org/project/sphinx-nbexamples/

    .. |conda| image:: https://anaconda.org/conda-forge/sphinx-nbexamples/badges/version.svg
        :alt: conda
        :target: https://anaconda.org/conda-forge/sphinx-nbexamples

    .. |github| image:: https://img.shields.io/github/release/Chilipp/sphinx-nbexamples.svg
        :target: https://github.com/Chilipp/sphinx-nbexamples/releases/latest
        :alt: Latest github release

    .. |supported-versions| image:: https://img.shields.io/pypi/pyversions/sphinx-nbexamples.svg?style=flat
        :alt: Supported versions
        :target: https://pypi.org/project/sphinx-nbexamples/

    .. |supported-implementations| image:: https://img.shields.io/pypi/implementation/sphinx-nbexamples.svg?style=flat
        :alt: Supported implementations
        :target: https://pypi.org/project/sphinx-nbexamples/


.. end-badges

Welcome! Similarly to Oscar Najeras sphinx-gallery_ module, this module intends
to create an example gallery for your documentation. However, we don't use
python scripts, instead we create the example gallery out of a bunch of jupyter
notebooks using nbconvert.

This package can be used to

1. Put all the examples you prepared in different notebooks in an pictured
   gallery
2. use the same html (sphinx) scheme for your examples that you are using for
   your documentation
3. Include the example notebooks in an offline (pdf) documentation
4. Include not only the code, but also the link to required supplementary files
5. Include a link to the `Jupyter nbviewer`_

.. _Jupyter nbviewer: https://nbviewer.jupyter.org
.. _sphinx-gallery: http://sphinx-gallery.readthedocs.org/en/latest/


Content
-------

.. toctree::
    :maxdepth: 1

    installing
    getting_started
    linkgalleries
    examples/index
    api/sphinx_nbexamples
    changelog


Installation
============
Simply install it via ``pip``::

    $ pip install sphinx-nbexamples

Or you install it via::

    $ python setup.py install

from the `source on GitHub`_.


.. _source on GitHub: https://github.com/Chilipp/sphinx-nbexamples


Requirements
============
The package requires

- Sphinx_>=1.3: The python library for generating automated documentation
- jupyter_: The jupyter framework for jupyter notebooks. sphinx-nbexamples
  explicitly depends on

  - nbconvert_: For converting jupyter notebooks to RST
  - jupyter_client_: For managing the kernels
  - ipykernel_: For installing an ipython kernel and run the notebooks


.. _Sphinx: http://www.sphinx-doc.org/en/stable
.. _jupyter: http://jupyter.org/
.. _nbconvert: https://nbconvert.readthedocs.io
.. _jupyter_client: https://jupyter-client.readthedocs.io
.. _ipykernel: https://ipykernel.readthedocs.io



Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
