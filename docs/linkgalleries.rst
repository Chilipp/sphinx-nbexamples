.. _linking-galleries:

Linking to other galleries
==========================
You can insert the links to the example galleries in other projects using the
:rst:dir:`linkgalleries` directive. This will insert all the thumbnails and the
titles of the examples in a list. You can find an example
:ref:`below <linked-gallery-example>`.


.. rst:directive:: linkgalleries

    Insert links to other example galleries generated with the
    sphinx-nbexamples extension.

    The directive takes no arguments and the options are the same as for the
    :dudir:`figure` directive. By default, we use a width of 160px and the
    ``align`` parameter is set to ``'left'``.

    Each line of the content for this package must be the name of a package as
    it is registered in the :confval:`intersphinx_mapping` configuration value
    by the :mod:`sphinx.ext.intersphinx` extension. Optionally you can also
    provide the folder for the examples.

    .. warning::

        This directive only works well for examples that have a thumbnail
        associated with them, i.e. not with code examples
        (see :ref:`thumbnails`).

    .. rubric:: Examples

    To insert links to the examples of the
    :ref:`sphinx-nbexamples gallery <gallery_examples>` you can either
    use

    .. code-block:: rst

        .. linkgalleries::

            sphinx_nbexamples

    or more explicit

    .. code-block:: rst

        .. linkgalleries::

            sphinx_nbexamples examples


.. _linked-gallery-example:

Linked gallery example
----------------------

The outputs of

.. code-block:: rst

    .. linkgalleries::

        psyplot

are links to the examples in
:ref:`psyplots example gallery <psyplot:gallery_examples>`.

This then transforms to

.. linkgalleries::

    psyplot

In the ``conf.py`` script, the :confval:`intersphinx_mapping` configuration
value then looks like

.. code-block:: python

    intersphinx_mapping = {
        'psyplot': ('http://psyplot.readthedocs.io/en/latest/', None),
        }

We can also insert links into the library of the current project by just
inserting the name of the project.

In our case (``sphinx-nbexamples``) this then looks like

.. linkgalleries::

    sphinx-nbexamples

The :rst:dir:`linkgalleries` directive also accepts multiple packages, e.g.

.. code-block:: rst

    .. linkgalleries::

        psyplot
        sphinx-nbexamples
