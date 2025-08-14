import os
from setuptools import setup, Extension


params_ext = Extension('params',
    include_dirs=['.'],
   sources=['search_params_wrapper.cpp']
)


setup(
    name='params-wrapper',
    description='Wrapping search_params in C/C++ for Python',
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Intended Audience :: Developers',
        'Topic :: Software Development :: Libraries',
        'Programming Language :: C',
        'Programming Language :: C++',
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
        'License :: OSI Approved :: MIT License',
        ],
    platforms='unix',
    ext_package='',
    ext_modules=[params_ext],
    py_modules=['search_params']
)