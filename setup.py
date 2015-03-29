# coding: utf-8

__author__ = 'Junki Ishida'

from setuptools import setup

setup(
    name='redis-xslock',
    version='0.0.1-dev',
    description='A provider of exclusive and shared lock via redis.',
    author='Junki Ishida',
    author_email='likegomi@gmail.com',
    url='https://github.com/likegomi/redis-xslock',
    packages=['redis_xslock', ],
    license='MIT',
    install_requires=['redis>=2.10.0', ],
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 2.6',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.3',
        'Programming Language :: Python :: 3.4',
    ]
)