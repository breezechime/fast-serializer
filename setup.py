from setuptools import setup

setup(
    name='pyserializer',
    version='0.8.1',
    author='且听风铃、我是指针*、ZDLAY、KYZ',
    author_email='breezechime@163.com',
    description='python 数据类验证器和序列化框架',
    long_description=open('README.md').read(),
    long_description_content_type="text/markdown",
    url='https://github.com/breezechime/fast-serializer',
    license='MIT',
    packages=['fast_serializer'],
    install_requires=[],
    classifiers=[
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
        'Programming Language :: Python :: 3',
    ],
    python_requires='>=3.6',
)