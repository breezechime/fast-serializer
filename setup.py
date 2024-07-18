import warnings
from setuptools import setup
from setuptools.command.build_ext import build_ext

try:
    from Cython.Build import cythonize
    use_cython = True
except ImportError:
    warnings.warn('不使用cython')
    use_cython = False

setup(
    name='fast-serializer',
    version='0.8.4',
    author='且听风铃、我是指针*、ZDLAY、KYZ',
    author_email='breezechime@163.com',
    description='python 数据类验证器和序列化框架',
    long_description=open('README.md').read(),
    long_description_content_type="text/markdown",
    url='https://github.com/breezechime/fast-serializer',
    license='MIT',
    packages=['fast_serializer'],
    install_requires=[],
    # ext_modules=cythonize(extensions),
    ext_modules=cythonize('fast_serializer/*.py', language_level=3) if use_cython else [],
    classifiers=[
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
        'Programming Language :: Python :: 3',
    ],
    python_requires='>=3.6',
    script_args=['build_ext']
)