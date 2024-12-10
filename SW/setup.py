from setuptools import setup, Extension
from torch.utils.cpp_extension import BuildExtension, CUDAExtension

setup(
    name='edge_generator',
    ext_modules=[
        CUDAExtension(
            'edge_generator',
            ['data/edge_generator.cpp'],
        )
    ],
    cmdclass={
        'build_ext': BuildExtension
    }
)