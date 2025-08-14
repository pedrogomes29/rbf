import os
from setuptools import setup, Extension


obf_ext = Extension("obf", include_dirs=["."], sources=["open_bloom_filter.cpp"])


setup(
    name="obf",
    description="Wrapping Open Bloom Filter library in C/C++ for Python",
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "Topic :: Software Development :: Libraries",
        "Programming Language :: C",
        "Programming Language :: C++",
        "Programming Language :: Python :: 2",
        "Programming Language :: Python :: 2.7",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.4",
        "Programming Language :: Python :: 3.5",
        "Programming Language :: Python :: 3.6",
        "License :: OSI Approved :: MIT License",
    ],
    platforms="unix",
    ext_package="",
    ext_modules=[obf_ext],
    py_modules=['open_bloom_filter'],
)
