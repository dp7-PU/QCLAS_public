# -*- coding: utf-8 -*-
"""
Created on Sun Feb  7 16:10:48 2016

Module: das

The module contains classes and functions that can be easily used for DAS
retrieval. The module is created specifically for Zondlo lab's LabView-based
DAS program.

@author: Da
"""
# %% Import modules needed

import numpy as np
import matplotlib.pyplot as plt
import os
import readTxt
import pandas as pd


# %% Define DASpec class

class dasSignal:
    '''The class stores signal direct absoprtion .

    Attributes:
    -----------
    ts: pandas DataSeries
        ts contains strings of timestamps.
    spec: pandas DataFrame
        spec contains all the direct absorption spectra
    location: string
        location of lvm files

    '''

    def __init__(self, location=None, idx_range=None, adjust=True, prefix='DAS_'):
        self.location = None
        self.ns = None
        self.namelist = []
        self.startIdx = None
        self.threshIdx = None
        self.endIdx = None
        self.abnorm = None  # List of bools, true members will be used for fitting
        self.__nomred = False  # Flag for chekcing if normalizaiton has been executed
        self.__offseted = False  # Flag for checking if offset has been executed
        self.__fitted = False  # Flag for checking if baseline is fitted
        self.bsl = None
        self.nu = None
        self.absorbance = None
        if location is not None:
            self.read(location, idx_range, adjust=adjust, prefix=prefix, silent=True)

    def read(self, location, idx_range, prefix='DAS_',
             ns=10000, silent=False, norm=False, adjust=True):
        ''' Read DAS lvm files.

        Params:
        ------
        location: str
            Location of the files.
        idx_range: list
            List of files will be read.
        prefix: str
            Prefix of lvm files, default = 'DAS_'
        numDigit: int
            Width of file index in the file name. =0 means not parse, e.g.
            'DAS_1.lvm'. Default is 3, e.g. 'DAS_001.lvm'.
        ns: int
            Number of sample for each spectrum.
        silent: bool
            Show reading progress and plot final results if set True.
        norm: bool
            Normalize the spectra using min and max

        Returns:
        -------
        No return, the function assign values to self.ts and self.spec.
        '''

        # %% Change dir to location and create filename list
        self.location = location
        self.ns = ns
        self.ts = []
        self.data = []
        cwd = os.getcwd()
        os.chdir(os.path.abspath(location))
        filenames = os.listdir(os.getcwd())

        # %% Read files
        # idx_range = list(idx_range)
        for file in filenames:
            if ('_' in file) & ('.' in file):
                idx = int(file.split('_')[1].split('.')[0])
            if os.path.isfile(file) & (prefix in file) & (idx in idx_range):
                # %% Only exec for files
                self.namelist.append(file.split('.')[0])
                hstr, data = readTxt.read(file, 22)
                date = hstr[9].split('\n')[0].split('\t')[1]
                date = date.replace('/', '-')
                time = hstr[10].split('\n')[0].split('\t')[1]
                self.ts.append(pd.to_datetime(date + 'T' + time))
                self.data.append(data[:, 1])

        self.data = np.array(self.data).T
        self.ts = np.array(self.ts).T
        self.ns = self.data.shape[0]

        # %% Adjust the signals
        if adjust:
            #			self.reverse()
            self.startIdx = int(0.005 * self.ns)
            self.endIdx = int(0.99 * self.ns)
            self.offset()
            self.__offseted = True
            self.normalization()
            self.__normed = True
            self.reverse()
        else:
            self.abnorm = list(False for i in range(self.ns))
        # %% Change back to original dir
        os.chdir(cwd)
        if not silent:
            fig, ax = plt.subplots()
            ax.plot(self.data)
            plt.show()

    def normalization(self):
        ''' Normalize spectra using max and min values.'''
        if not self.__offseted:
            self.offset()
        l = len(self.data[:, 0])
        for i in range(self.data.shape[1]):
            minPt = np.min([self.data[int(l * 0.02):int(l * 0.03), i].mean(),
                            self.data[int(l * 0.985):int(l * 0.995), i].mean()])
            maxPt = np.max([self.data[int(l * 0.02):int(l * 0.03), i].mean(),
                            self.data[int(l * 0.985):int(l * 0.995), i].mean()])
            self.data[:, i] = (self.data[:, i] - minPt) / (
                maxPt - minPt)

    def offset(self, idx=None, diag=False):
        ''' Change offset point, idx must be given.	'''
        if idx is None:
            dataDiff = np.diff(self.data[self.startIdx:0.05 * self.ns], 1, 0).mean(
                axis=1)
            idx = dataDiff.argmax()
        for i in range(self.data.shape[1]):
            self.data[:, i] = self.data[:, i] - self.data[idx, i]

        self.threshIdx = idx

    def reverse(self):
        ''' Reverse the spectra'''
        self.data = 1 - self.data

    def plotall(self):
        ''' Plot all spec in same fig. Return fig, ax. '''
        fig, ax = plt.subplots()
        plt.plot(self.data)
        return fig, ax

    def plotid(self, col):
        ''' Plot individual spectrum.

        Params:
        ------
        col: 1

        Returns:
        --------
        fig, ax: handls
        '''
        if type(col) == str:
            col = np.argwhere(self.namelist == col)[0, 0]
        fig, ax = plt.subplots()
        ax.plot(self.data[:, col])

    def bslFit(self, col, fitRange, order=3, silent=False, diag=False):
        ''' Use specific signal for baseline fitting (polynomial)

        Params:
        -------
        col: int

        fitRange: list of tuples
            List of tuples for slice, e.g. [(0,30), (100,500)].

        order: int
            Order of polynomial for fitting.

        Returns:
        -------
        bsl: list of floats
            Baseline of the spec. The length is equal to ns
        '''
        if not self.__offseted:
            self.offset()
        if not self.__normed:
            self.normalization()
        if type(col) == str:
            col = self.namelist.index(col)

        idx = list(range(self.ns))
        x = []
        y = []

        for iRange in fitRange:
            if diag:
                print(iRange)
            x.extend(idx[iRange])
            y.extend(self.data[iRange, col])

        p = np.polyfit(x, y, order)
        self.bsl = np.polyval(p, idx)

        if not silent:
            fig, ax = plt.subplots()
            ax.plot(self.bsl, label='Baseline')
            ax.plot(self.data[:, col], label='Signal')
            plt.show()

    def getHalfAbsorpAndNu(self, peakRange, endIdx):
        '''
        :param peakRange: A tuple of start and end indicies
        :param endIdx: negative integer
        :return:
        '''
        if self.bsl is None:
            raise Exception('Baseline is unknown')
        else:
            n = self.data.shape[1]
            self.nu = []
            self.absorbance = []
            for i in range(0, n):
                fracAborp = (self.bsl - self.data[:, i]) / self.bsl
                argMax = fracAborp[peakRange[0]:peakRange[1]].argmax() + peakRange[0]
                halfSpec = fracAborp[argMax:endIdx]
                absorbance = np.hstack((np.flipud(halfSpec), halfSpec))
                absorbance = -np.log(1 - absorbance)
                nu = -(np.arange(0, len(absorbance)) - np.ceil(
                    len(absorbance) / 2)) * 0.00057 + 1.103457e3
                self.absorbance.append(absorbance)
                self.nu.append(nu)

    def calcHWHM(self, peakRange, col):
        if type(col) == str:
            col = self.namelist.index(col)

        tmp_spec = self.data[peakRange, col]
        half_max = np.max(tmp_spec) / 2.

        d = np.diff(np.sign(half_max - tmp_spec))
        left_idx = np.find(d > 0)[0]
        right_idx = np.find(d < 0)[-1]
        return right_idx - left_idx

    def getAbsorp(self, validRng):
        n = self.data.shape[1]
        self.absorbance = []
        for i in range(n):
            fracAbs = (self.bsl - self.data[:, i])/ self.bsl
            absorbance = fracAbs[validRng[0]:validRng[1]]
            absorbance = -np.log(1 - absorbance)
            self.absorbance.append(absorbance)

        self.absorbance = np.array(self.absorbance).T


def main():
    test = dasSignal(location=r"C:\Users\pdphy\Desktop\NH3_Calibration\DAS\\",
                     idx_range=range(1, 49))
    test.bslFit('DAS_048', [slice(20, 100), slice(900, 980)], 3)
    input('Press Enter to exit.')


if __name__ == '__main__':
    main()
