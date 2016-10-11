#!/bin/bash
# script to automatically generate the sphinx_nbexamples api documentation using
# sphinx-apidoc and sed
sphinx-apidoc -f -M -e  -T -o api ../sphinx_nbexamples/
# replace chapter title in sphinx_nbexamples.rst
sed -i '' -e 1,1s/.*/'API Reference'/ api/sphinx_nbexamples.rst
sed -i '' -e 2,2s/.*/'============='/ api/sphinx_nbexamples.rst
