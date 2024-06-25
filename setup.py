from Cython.Build import cythonize
from setuptools import setup

setup(
    name='c_utils',
    ext_modules=cythonize('c_utils.pyx'),
)