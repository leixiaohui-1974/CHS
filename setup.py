from setuptools import setup, find_packages

setup(
    name="chs_sdk",
    version="0.1.0",
    packages=find_packages(where="water_system_sdk/src"),
    package_dir={"": "water_system_sdk/src"},
    install_requires=[
        "pandas",
        "matplotlib",
        "scipy",
        "pykrige",
        "numpy",
        "cvxpy",
        "osqp",
        "numba",
        "PyYAML",
        "meshio",
        "pytest",
        "loguru",
        "pydantic"
    ],
    author="Teixinhui-1974/CHS Team",
    author_email="your_email@example.com",
    description="Conscious Hydraulic System (CHS) - The Operating System for Smart Water",
    long_description=open('README.md').read(),
    long_description_content_type="text/markdown",
    url="https://github.com/leixiaohui-1974/CHS",
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires='>=3.8',
)
