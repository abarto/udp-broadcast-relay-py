from setuptools import setup
from os import path
from io import open

with open(path.join(path.abspath(path.dirname(__file__)), 'README.md'), encoding='utf-8') as f:
    long_description = f.read()

setup(
    name='udp-broadcast-relay-py',
    version='0.1',
    description='A set of Python scripts to relay UDP packets between networks.',
    long_description=long_description,
    long_description_content_type='text/markdown',
    url='https://github.com/abarto/udp-broadcast-relay-py',
    author='Agustin Barto',
    author_email='abarto@gmail.com',
    classifiers=[
        'Development Status :: 3 - Beta',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
    ],
    keywords='networking ip udp relay',
    py_modules=['udp_broadcast_forward', 'udp_broadcast_replay'],
    entry_points={
        'console_scripts': [
            'udp_broadcast_forward=udp_broadcast_forward:main',
            'udp_broadcast_replay=udp_broadcast_replay:main',
        ],
    }
)
