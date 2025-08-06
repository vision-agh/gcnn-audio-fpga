from setuptools import setup, Extension
import pybind11
from setuptools.command.build_ext import build_ext

from setuptools import setup
from torch.utils.cpp_extension import CppExtension, BuildExtension

setup(
    name='edge_generator',
    ext_modules=[
        CppExtension(
            'edge_generator',
            ['data/edge_generator.cpp'],
        )
    ],
    cmdclass={
        'build_ext': BuildExtension
    }
)