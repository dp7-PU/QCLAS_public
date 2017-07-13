# QCLAS
A graphic for spectroscopic analyses for Quantum Cascade Laser-based sensor.

# Installation guide

First, QCLAS is written in Python 2.7. A valid version of Python 2 is needed.

Following packages are needed as well:

1. Numpy
2. Scipy
3. Pandas
4. Matplotlib
5. Statsmodels
6. PyQt4

## Install PyQt4 first

PyQt4 needs to be installed first before everything else. Download SIP first from:

https://sourceforge.net/projects/pyqt/files/sip/sip-4.19.3/sip-4.19.3.zip/download

Unzip the file and go to the unziped folder and run cmd or powershell or bash, and then excute:

    python configure.py
    
Download wheel file from:

http://www.lfd.uci.edu/~gohlke/pythonlibs/#pyqt4

## Install QCLAS with pip

To install the package itself, clone the repository or download the tar.gz file in dist folder. Unzip the file and go to the folder.

For windows user, open cmd or powershell and then excute:

    pip install .

The program will automatically install other packages.

## Run the program

To run the program, go to ./src folder and run qclasGUI.pyw.

Windows user can create a shortcut for the program.
