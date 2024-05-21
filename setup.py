# readout-generator/setup.py
"""
setup.py for readout generator cli tool
"""
from setuptools import setup, find_packages

setup(
    name='insight-creator',
    version='1.0',
    py_modules=['main'],
    install_requires=[
        'click'
    ],
    entry_points={
        'console_scripts': [
            'insight-creator = main:generate',
        ],
    },
    packages=find_packages(),
    classifiers=[
        'Programming Language :: Python :: 3',
        'License :: OSI Approved :: Apache License',
        'Operating System :: OS Independent',
    ],
)