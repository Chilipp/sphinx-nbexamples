from setuptools import setup, find_packages
import sys

needs_pytest = {'pytest', 'test', 'ptr'}.intersection(sys.argv)
pytest_runner = ['pytest-runner'] if needs_pytest else []


def readme():
    with open('README.rst') as f:
        return f.read()


setup(name='sphinx-nbexamples',
      version='0.3.2',
      description=(
          'Create an examples gallery with sphinx from Jupyter Notebooks'),
      long_description=readme(),
      classifiers=[
        'Development Status :: 5 - Production/Stable',
        'Intended Audience :: Developers',
        'Topic :: Documentation',
        'License :: OSI Approved :: GNU General Public License v2 (GPLv2)',
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.2',
        'Programming Language :: Python :: 3.3',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
        'Operating System :: OS Independent',
      ],
      keywords=('sphinx sphinx-gallery examples documentation notebook ipython'
                ' jupyter nbconvert nbsphinx'),
      url='https://github.com/Chilipp/sphinx-nbexamples',
      author='Philipp Sommer',
      author_email='philipp.sommer@unil.ch',
      license="GPLv2",
      packages=find_packages(exclude=['docs', 'tests*', 'examples']),
      package_data={'sphinx_nbexamples': ['sphinx_nbexamples/_static/*']},
      include_package_data=True,
      install_requires=[
          'sphinx',
          'ipython',
          'nbconvert',
          'Pillow',
          'jupyter_client',
          'ipykernel',
      ],
      setup_requires=pytest_runner,
      tests_require=['pytest'],
      zip_safe=False)
