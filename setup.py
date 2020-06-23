from setuptools import setup

setup(name='crossword',
      version='2.1.3',
      description='Crossword Puzzle Editor',
      url='http://github.com/philhanna/crossword',
      author='Phil Hanna',
      license='MIT',
      packages=['crossword', 'crossword.ui', 'crossword.tests', 'crossword.util'],
      zip_safe=False)
