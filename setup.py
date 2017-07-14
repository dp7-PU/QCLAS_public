from setuptools import setup

setup(
    # Application name:
    name='QCLAS',

    # Version numbuer:
    version="0.5.1",

    # Author
    author='Da Pan',

    # Pacakge
    packages=['QCLAS'],
    package_dir={'QCLAS': 'src'},
    package_data={'QCLAS': ['data/*.p']},

    # Dependency
    setup_requires=['numpy'],
    install_requires=['scipy', 'matplotlib', 'PyQt5', 'statsmodels']
)