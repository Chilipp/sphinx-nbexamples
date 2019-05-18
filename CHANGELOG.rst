v0.4.0
======
This release adds support for non-python notebooks and the possibility to
include links to binderhub-services (e.g. https://mybinder.org) in the docs.

Added
-----
- Thanks to the efforts of `@effigies <https://github.com/effigies>`_ in
  `#3 <https://github.com/Chilipp/sphinx-nbexamples/issues/3>`_,
  `#4 <https://github.com/Chilipp/sphinx-nbexamples/issues/4>`_,
  `#5 <https://github.com/Chilipp/sphinx-nbexamples/issues/5>`_,
  `#6 <https://github.com/Chilipp/sphinx-nbexamples/pull/6>`_,
  `#7 <https://github.com/Chilipp/sphinx-nbexamples/pull/7>`_,
  `#8 <https://github.com/Chilipp/sphinx-nbexamples/pull/8>`_, and
  `#9 <https://github.com/Chilipp/sphinx-nbexamples/pull/9>`_, we now support
  ``README.md`` files and non-python notebooks (see
  `the bash example in the docs <https://sphinx-nbexamples.readthedocs.io/en/latest/examples/example_bash.html#gallery-examples-example-bash-ipynb>`_)
- sphinx-nbexamples now supports including a link to binder services with
  buttons like |binder| in the converted notebook. See the `docs on including a link to binder <https://sphinx-nbexamples.readthedocs.io/en/latest/getting_started.html#including-a-link-to-the-binder>`_

.. |binder| image:: https://mybinder.org/badge_logo.svg
    :target: https://mybinder.org/v2/gh/Chilipp/sphinx-nbexamples/master

Changed
-------
- Bokeh has been marked as not working in the conversion of notebooks (see `#10 <https://github.com/Chilipp/sphinx-nbexamples/issues/10>`_)
- a bug with the thumbnails in the linkgalleries directive for sphinx>1.8.5 has
  been resolved (see `cc402b2 <https://github.com/Chilipp/sphinx-nbexamples/commit/cc402b2be3ac765a68bac76f1682a854c580fdb7>`_)

v0.3.2
======
Fixed compatibility with nbconvert 5.5

v0.3.1
======
This patch fixes some minor logging issues with sphinx >1.7.6

Changed
-------
* Minor compatibility fix for using the logger with Sphinx
* Corrected typos `see PR #1 <https://github.com/Chilipp/sphinx-nbexamples/pull/1>`__

v0.3.0
======
Added
-----
* The removal of tags for the converted rst file. With
  `nbconvert 5.3 <https://nbconvert.readthedocs.io/en/stable/changelog.html>`__
  we have the ``nbconvert.preprocessors.TagRemovePreprocessor`` available
  which gave the motivation to 4 new gallery configuration values, namely

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

  The tags specified by these configuration values will be removed in the
  rst file.

v0.2.2
======
Added
-----
* The linkgalleries directive now can also insert links to the current
  sphinx project that is build

Changed
-------
* the linkgalleries directive uses the styles from the example_gallery_styles.css,
  i.e. the same style as it is used in the processed example gallery.


v0.2.1
======
Changed
-------
* Minor bug fix in option_spec of LinkGalleriesDirective

v0.2.0
======
Added
-----
* Added changelog
* Added linkgalleries directive

Changed
-------
* The name of a thumbnail is now ``reference + '_thumb.png'`` where
  ``reference`` is the section label of the rst file
* Reference labels are now all lower case
