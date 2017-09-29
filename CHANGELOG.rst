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
