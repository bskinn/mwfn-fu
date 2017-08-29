from setuptools import setup
from os import environ

def readme():
    with open('README.rst') as f:
        return f.read()

setup(
    name='mwfn_fu',
    version='0.1',
    provides=['mwfn_fu'],
    install_requires=['sarge', 'psutil'],
    packages=['mwfn_fu'],
    url='https://www.github.com/bskinn/mwfn-fu',
    license='MIT License',
    author='Brian Skinn',
    author_email='bskinn@alum.mit.edu',
    description='Automated and Enhanced Manual Runner for Multiwfn',
    long_description=readme(),
    classifiers=['License :: OSI Approved :: MIT License',
                 'Natural Language :: English',
                 'Environment :: Console',
                 'Intended Audience :: Science/Research',
                 'Operating System :: OS Independent',
                 'Programming Language :: Python :: 3 :: Only',
                 'Programming Language :: Python :: 3.4',
                 'Programming Language :: Python :: 3.5',
                 'Topic :: Scientific/Engineering',
                 'Topic :: Utilities',
                 'Development Status :: 2 - Pre-Alpha'] #,
#    entry_points={
#        'console_scripts': [
#            'h5cube = h5cube.h5cube:script_run'
#                           ]
#                  }
    )
