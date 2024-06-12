# yoda/setup.py
"""
setup.py for yoda cli tool
"""
from setuptools import setup, find_packages

setup(
    name='yoda',
    version='1.0',
    py_modules=['main'],
    install_requires=[
        'click'
    ],
    entry_points={
        'console_scripts': [
            'yoda = main:cli',
        ],
    },
    packages=find_packages(),
    classifiers=[
        'Programming Language :: Python :: 3',
        'License :: OSI Approved :: Apache License',
        'Operating System :: OS Independent',
    ],
)