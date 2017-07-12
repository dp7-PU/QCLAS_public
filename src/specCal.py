"""
Notes
-----
Calculate & Plot DAS using HAPI. This package can be used independently with
python script. An UI is also provided called qclasUI.py.


Author
------
Da Pan,
Department of Civil and Environmental Engineering,
Princeton University
Email: dp7@princeton.edu

Created Date
------------
02/10/2016

Edited Dates
------------
04/22/2016 by Da Pan:
    Added 'Simulation with parameters' method for calWms.

07/25/2016 by Da Pan:
    Bug fixed for 'Simulation with parameters' method for calWms. Added
    'read_config' function to read laser spec configuration.

07/26/2016 by Da Pan:
    Docstrings added for all functions.

08/18/2016 by Da Pan:
    Added etalon generation function.

09/17/2016 by Da Pan:
    Added save to csv function.

09/19/2016 by Da Pan:
    Added unit handler.

"""

import hapi
import numpy as np
import matplotlib.pyplot as plt
from matplotlib import ticker
from scipy.integrate import simps, romb
from scipy.signal import butter, lfilter
import csv
import statsmodels.api as sm

kb = 1.38064852e-23  # Boltzmann constant, m^2 kg s^-2 K^-1
nA = 6.022e23  # Avogadro's number molec/mol-1
R = 8.314  # Universal gas constant


def mixRatio2numDen(c, p, T):
    """
    Convert mixing ratio to number density.
    Parameters
    ----------
    c: float
        Volume mixing ratio.
    p: float
        Pressure in atm.
    T: float
        Temperature in K.

    Returns
    -------
    n: float
        Number density in molec/cm^3

    """
    n = p * 1.013e5 / kb / T * 1e-6 * c
    return n


def mixRatio2molDen(c, p, T):
    """
    Convert mixing ratio to molar density.

    Parameters
    ----------
    c: float
        Volume mixing ratio.
    p: float
        Pressure in atm.
    T: float
        Temperature in K.

    Returns
    -------
    m: float
        Mol density in mol/m^3.

    """
    m = p * 1.013e5 / R / T * c
    return m


def read_config(config_name):
    """
    Read configuration file and return configuration. Configuration should specify directory of data files (dir),
    and periods for analysis (t_start and t_end), base time specified in the LabView program (LV_time_base),
    and column names (col_names).

    Parameters
    ----------
    config_name: str
        Name of configuration file.

    Returns
    -------
    dict
        Configuration dict.

    """

    print "\nReading configuration from " + config_name + ":\n"

    config = {}

    with open(config_name) as f:
        for line in f:
            key, value = line.split(': ')
            config[key] = float(value[:-1])
            print key + ': ' + value[:-1]

    return config


def calDas(gasList, nu, profile, mode, iCut=1e-30, etalonCoeff=None,
           unitDict={'c': 'V ratio', 'p': 'hPa', 't': 'K', 'l': 'cm'}, info_out=False):
    """
    Calculate direction absorption spectrum.
    Parameters
    ----------
    gasList: list of dict
        List of parameters for calculation. The dict should have keys for 'gas' (
        gas name str), 'p' (pressure in hPa), 't' (temperature in K), 'l' (path
        length in cm), 'c' (volume mixing ratio).
    nu: array
        Wavelength array in cm-1.
    profile: str
        Choose one from 'Voigt', 'HT', 'Doppler', and 'Lorentz'.
    mode: str
        Choose one from 'Absorbance', 'Transmission', 'Absorb coeff'.
    iCut: float
        Intensity cut threshold.
    etalonCoeff: list of dict
        Results from generateEtalons, containing coefficients for etalon calculation.
    info_out: bool
        True to output line infomation.

    Returns
    -------
    results: list of dict
        Each dict in the list has keys of 'gasParams' (dict given in input),
        'nu' (wavelength array cm^-1), 'coeff' (spectrum coeff).
    """
    results = []
    for idx, gasParams in enumerate(gasList):
        if gasParams['gas'] not in hapi.tableList():
            return str('Cannot find specified gas.')
        nuInTable = hapi.getColumn(gasParams['gas'], 'nu')
        if (np.min(nu) < np.min(nuInTable) - 1) | (
                    np.min(nu) > np.max(nuInTable) + 1) | (
                    np.max(nu) > np.max(nuInTable) + 1) | (
                    np.max(nu) < np.min(nuInTable) - 1):
            return str(
                'Cannot find lines within specified wavenumber range, please download data.')
        Cond = ('AND', ('BETWEEN', 'nu', np.min(nu), np.max(nu)), ('>=', 'sw', iCut))
        hapi.select(gasParams['gas'], Conditions=Cond, DestinationTableName='tmp')
        p, t, l, n = unitHandler(gasParams, unitDict)

        if profile == 'Voigt':
            nu, coeff = hapi.absorptionCoefficient_Voigt(SourceTables='tmp',
                                                         OmegaGrid=nu,
                                                         Environment={'T': t,
                                                                      'p': p})
        elif profile == 'HT':
            nu, coeff = hapi.absorptionCoefficient_HT(SourceTables='tmp',
                                                      OmegaGrid=nu,
                                                      Environment={'T': t, 'p': p},
                                                      IntensityThreshold=iCut)
        elif profile == 'Doppler':
            nu, coeff = hapi.absorptionCoefficient_Doppler(SourceTables='tmp',
                                                           OmegaGrid=nu,
                                                           Environment={'T': t,
                                                                        'p': p},
                                                           IntensityThreshold=iCut)
        elif profile == 'Lorentz':
            nu, coeff = hapi.absorptionCoefficient_Lorentz(SourceTables='tmp',
                                                           OmegaGrid=nu,
                                                           Environment={'T': t,
                                                                        'p': p},
                                                           IntensityThreshold=iCut)
        else:
            raise Exception('No suitable profile.')
        if mode == 'Absorbance':
            coeff = coeff * n * l
        elif mode == 'Transmission':
            coeff = coeff * n * l
            coeff = np.exp(-coeff)
        if info_out:
            hapi.select('tmp', File='tmp.txt')
        hapi.dropTable('tmp')
        result = dict()
        result['gasParams'] = gasParams
        result['nu'] = nu
        result['spectrum'] = coeff
        results.append(result)
    return results


def plotDas(ax, results, mode, showTotal=True,
            iCut=1e-30, diag=False,
            unitDict={'c': 'V ratio', 'p': 'hPa', 't': 'K', 'l': 'cm'}):
    """
    Plot direction absorption spectroscopy results from calDas.

    Parameters
    ----------
    ax: object
        Axis object for plotting.
    results: list of dict
        Results from calDas. Each dict in the list has keys of 'gasParams' (dict
        given in input), 'nu' (wavelength array cm^-1), 'spectrum' (spectrum spectrum).
    mode: str
        Choose from 'Absorbance', 'Transmission', 'Absorb spectrum'.
    showTotal: bool
        If True, plot the sum of given spectra.

    Returns
    -------

    """
    sumAbsorp = np.zeros(results[0]['nu'].shape)
    sumTrans = np.copy(sumAbsorp) + 1
    ax.clf()

    for idx, result in enumerate(results):
        # resuls is a dict containing gasParameter, nu, and spectrum
        gasParams = result['gasParams']
        nu = result['nu']
        spectrum = result[
            'spectrum']  # spectrum could be absorption spectrum, absorbance,
        # or transmittance
        if mode == 'Absorp coeff':
            ax.plot(nu, spectrum, label=strGasParams(gasParams, unitDict))
        elif mode == 'Absorbance':
            ax.plot(nu, spectrum, label=strGasParams(gasParams, unitDict))
            sumAbsorp = sumAbsorp + spectrum
            # print(strGasParams(gasParams))
        elif mode == 'Transmission':
            ax.plot(nu, spectrum, label=strGasParams(gasParams, unitDict))
            sumTrans = sumTrans * spectrum

    if mode == 'Absorbance':
        if showTotal:
            ax.plot(nu, sumAbsorp, label='Total')
        ax.set_ylabel('Absorbance')
        leg = ax.legend(fontsize=11, loc=2, frameon=False)
    elif mode == 'Transmission':
        if showTotal:
            ax.plot(nu, sumTrans, label='Total')
        ax.set_ylabel('Transmission')
        leg = ax.legend(fontsize=11, loc=3, frameon=False)
    elif mode == 'Absorp coeff':
        if showTotal:
            ax.set_ylabel('Absorp coeff')
        leg = ax.legend(fontsize=11, loc=2, frameon=False)
    formatter = ticker.ScalarFormatter(useMathText=True)
    if leg:
        leg.draggable()
    ax.set_xlabel('Wavenumber (cm$^{-1}$)')
    ax.set_xlim([nu.min(), nu.max()])
    formatter.set_scientific(True)
    formatter.set_useOffset(False)
    ax.yaxis.set_major_formatter(formatter)
    ax.xaxis.set_major_formatter(formatter)
    plt.tight_layout()
    return 0


def calWms(gasList, nu, profile, nf, method='Theoretical', laserSpec=None, dNu=None,
           iCut=1e-30, diag=False,
           unitDict={'c': 'V ratio', 'p': 'hPa', 't': 'K', 'l': 'cm'}):
    """
    Calculate spectra using wavelength modulation spectroscopy. This function
    calls calDas. Two methods are provided. The 'theoretical' method is based on
    Schilt et al. (2003). The 'Simulation with parameters' is Sun et al. (2014).

    Parameters
    ----------
    gasList: list of dict
        List of parameters for calculation. The dict should have keys for 'gas' (
        gas name str), 'p' (pressure in hPa), 't' (temperature in K), 'l' (path
        length in cm), 'c' (volume mixing ratio).
    nu: array
        Wavelength array in cm-1. This is used to generate the absorp coeff for
        later WMS calculation. Larger range should be given.
    profile: str
        Choose one from 'Voigt', 'HT', 'Doppler', and 'Lorentz'.
    nf: int
        Harmonics for WMS calculation.
    method: str
        Choose between 'theoretical' and 'Simulation with parameters'.
    laserSpec: dict, default=None
        Only for 'Simulation with parameters' method. Laser spec should
        have keys of fMod (modulation frequency in Hz), fRamp (ramp frequency in
        Hz), fS (sampling frequency in Hz), aRamp (ramp amplitude in mV),
        aMod (modulation amplitude in mV), tMod (modulation tuning rate cm^-1/V),
        tRamp (ramp tuning rate cm^-1/V), laserDC (DC laser power, mW),
        c2p (current to laser power mW/V), fCut (frequency threshold
        cut in Hz), phase (phase in deg), central_wavelength (in cm^-1). This
        specs are defined in the same way as the LabView program.
    dNu: float, default=None
        Only for Wavelength modulation depth (cm^-1).
    iCut: float
        Intensity cut threshold.
    diag: bool
        If true, plot figures for diagnostics.

    Returns
    -------
    wmsResults: list of dict
        Each dict in the list contains keys of gasParams (gas parameters in
        gasList), nu (wavelength number cm^-1), spectrum (wms spectrum),
        nf (nth harmonics), modDepth (modulation depth).

    """
    maxNu = nu.max()
    minNu = nu.min()
    if method == 'Theoretical':
        hdNu = np.linspace(minNu, maxNu, int((maxNu - minNu) / dNu * 1024) + 1)

        dasResults = calDas(gasList, hdNu, profile, 'Transmission', iCut,
                            unitDict=unitDict)
        if type(dasResults) is str:
            return dasResults
        wmsResults = []
        for result in dasResults:
            coeff = result['spectrum']
            Hnf = []
            for iNu in nu:
                u, du = np.linspace(-np.pi, np.pi, 2 ** 10 + 1, retstep=True)

                nuMod = iNu + dNu * np.cos(u)
                coeffMod = np.interp(nuMod, hdNu, coeff)
                integrateSample = coeffMod * np.cos(nf * u)
                Hnf.append(1. / np.pi * romb(np.array(integrateSample), dx=du))

            Hnf = np.array(Hnf)

            wmsResult = dict()
            wmsResult['gasParams'] = result['gasParams']
            wmsResult['nu'] = nu
            wmsResult['spectrum'] = Hnf
            wmsResult['nf'] = nf
            wmsResult['modDepth'] = dNu

            wmsResults.append(wmsResult)

    elif method == 'Simulation with parameters':
        # laserSpec is needed for this option, which is a dict containing:
        #   laser name: str, used for label
        #   linP: bool, true -> linear power for ramp
        #   linNu: bool, true -> linear wavelength (tuning rate) for ramp

        fS = laserSpec['fS']  # fS: sample frequency in Hz
        fMod = laserSpec['fMod']  # fMod: modulation frequency in Hz
        fRamp = laserSpec['fRamp']  # fRamp: ramp frequency in Hz
        aRamp = laserSpec[
            'aRamp']  # aRamp: ramp amplitude for linear power curve in mA
        aMod = laserSpec['aMod']  # aMod: modulation amplitude in mA
        tRamp = laserSpec['tRamp']  # tRamp: tuning rate for ramp in cm-1/mA
        tMod = laserSpec['tMod']  # tMod: tuning rate for modulation in cm-1/mA
        c2p = laserSpec['c2p']  # c2p: current to power conversion constant V/mA
        laserDC = laserSpec[
            'laserDC']  # Laser output DC component.
        fCut = laserSpec['fCut']  # curOff: fCut frequency for Butter filter
        phase = laserSpec['phase'] / 180. * np.pi  # Optimized phase
        central_wavelength = laserSpec['central_wavelength']
        laserCtrlFactor = laserSpec['laserCtrlFactor']

        nS = fS / fRamp  # number of sample
        ts = np.arange(nS) / fS  # time stamp for samples

        currRamp = (np.linspace(0, aRamp, nS) - aRamp * 0.5) / 1000
        currMod = 0.5 * aMod * np.sin(2. * np.pi * fMod * ts) / 1000

        nuRamp = currRamp * tRamp * laserCtrlFactor + central_wavelength
        nuTotal = nuRamp + currMod * tMod * laserCtrlFactor

        intensity = (currRamp + currMod) * c2p + laserDC
        intensity[intensity < 0] = 0

        b, a = butter(4, fCut / fS, 'low')

        wmsResults = []
        dasResults = calDas(gasList, nu, profile, 'Transmission', iCut,
                            unitDict=unitDict)

        if type(dasResults) is str:
            return dasResults

        for dasResult in dasResults:
            coeff = dasResult['spectrum']
            modCoeff = np.interp(np.flipud(nuTotal), nu, coeff)

            S = intensity * modCoeff
            if diag:
                plt.plot(S)
                plt.show()
            # plt.plot(S * np.cos(2. * nf * np.pi * fMod * ts + phase))
            y = lfilter(b, a, S * np.cos(2. * nf * np.pi * fMod * ts + phase))
            x = lfilter(b, a, S * np.sin(2. * nf * np.pi * fMod * ts))
            wmsResult = dict()
            wmsResult['gasParams'] = dasResult['gasParams']
            wmsResult['nu'] = nuRamp
            wmsResult['spectrum'] = y
            wmsResult['nf'] = nf
            wmsResult['modDepth'] = tMod * aMod / 1000 * laserCtrlFactor * 0.5
            wmsResults.append(wmsResult)
    print gasList

    return wmsResults


def IIRFilter(signal, fS, fMod, nf, fCut, phase):
    """
    Apply IIR filter to input signal.

    Parameters
    ----------
    signal: array
        Input signal.
    fS: float
        Sampling frequency.
    fMod: float
        Modulation frequency.
    nf: int
        Nth harmonics to be calculated.
    fCut: float
        Low cut frequency for butter filter.
    phase: float
        Phase in degree.

    Returns
    y: array
        Filtered signal.
    -------

    """
    nS = len(signal)
    tS = np.arange(nS) / fS
    b, a = butter(4, fCut / fS, 'low')
    y = lfilter(b, a, signal * np.cos(2. * nf * np.pi * fMod * tS + np.deg2rad(phase)
                                      ))

    return y


def peakTroughHeight(signal, startIdx, endIdx, twoSideTrough=True, avgWindow=50):
    """
    Calculate peak to trough height.
    Parameters
    ----------
    signal: array
        Input signal.
    startIdx: int
        Start index.
    endIdx: int
        End index.

    Returns
    -------
    PTH: float
        Peak to trough height.

    """
    tmpSignal = signal[startIdx:endIdx]

    peakIdx = np.argmax(tmpSignal)

    lTroughIdx = np.argmin(tmpSignal[:peakIdx])  # Left trough index
    rTroughIdx = np.argmin(tmpSignal[peakIdx:])  # Right trough index

    hWindow = int(avgWindow / 2)
    return np.mean(tmpSignal[peakIdx - hWindow:peakIdx + hWindow]) - 0.5 * (
        np.mean(tmpSignal[lTroughIdx - hWindow:lTroughIdx + hWindow]) + np.mean(
            tmpSignal[rTroughIdx - hWindow:rTroughIdx + hWindow]))


def plotWms(ax, results, showTotal=True,
            iCut=1e-30, diag=False,
            unitDict={'c': 'V ratio', 'p': 'hPa', 't': 'K', 'l': 'cm'}):
    """
    Plot results from calWMS.

    Parameters
    ----------
    ax: object
        Axis handle for plotting.
    results: list of dict
        wmsResults frosm calWms.
    showTotal: bool
        If True, plot sum of the given results in the list.

    Returns
    -------

    """
    ax.clf()
    sumWms = np.zeros(results[0]['nu'].shape)
    for idx, result in enumerate(results):
        nu = result['nu']
        spectrum = result['spectrum']
        gasParams = result['gasParams']
        ax.plot(nu, spectrum, label=strGasParams(gasParams, unitDict))
        sumWms = sumWms + spectrum

    if showTotal:
        ax.plot(nu, sumWms, label='Total')
    leg = ax.legend(fontsize=11, loc=2, frameon=False)
    if leg:
        leg.draggable()
    formatter = ticker.ScalarFormatter(useMathText=True)
    formatter.set_useOffset(False)
    ax.yaxis.set_major_formatter(formatter)
    ax.xaxis.set_major_formatter(formatter)
    ax.set_xlabel('Wavenumber (cm$^{-1}$)')
    ax.set_xlim([nu.min(), nu.max()])
    ax.set_ylabel('WMS ' + str(results[0]['nf']) + 'f (Mod depth: ' + str(
        results[0]['modDepth']) + ' cm$^{-1}$)')


def generateEtalons(etalonParams):
    """
    This function generates coeffecients for etalon calculatoin from etalon
    parameters.
    Parameters
    ----------
    etalonParams: list of dict
        A list of dict containing information of etalons. The dict should have
        following keys: n (refractive index), theta (angle of the light in deg),
        l (thickness of the part), R (reflectance of the part)
    Returns
    -------
    etalonCoeffs: list of dict
        A list of dict containing coefficients for etalon calculation. The dict
        has following keys: F (coefficient of finesse), delta_coeff (coefficient
        for calculating phase difference).
    """
    etalonCoeffs = []
    for param in etalonParams:
        etalonCoeffs.append({'F': 4 * param['R'] / (1 - param['R']) ** 2,
                             'delta_coeff': 4 * np.pi * param['n'] * param['l'] *
                                            np.cos(np.degrees(param['theta']))})
    return etalonCoeffs


def strGasParams(gasParams, unitDict):
    """
    Combine gas parameters into string for labeling in figure.

    Parameters
    ----------
    gasParams: dict
        Gas parameters contain gas (gas name), l (path length in cm),
        c (concentration), t (temperature in K), p (pressure in hPa).

    Returns
    -------
    str_gas_params: str
        Combined string for gas paraemters.

    """
    return str(gasParams['l']) + unitDict['l'] + ' ' + \
           str(gasParams['c']) + {'V ratio': ' ', 'mol/m^3': 'mol/m$^3$ '}[
               unitDict['c']] + gasParams['gas'] + r' @ ' + str(gasParams['p']) + \
           unitDict['p'] + ' & ' \
           + str(gasParams['t']) + unitDict['t']


def csvOutput(csvFile, results):
    """
    Output spectra to the given csv file.
    Parameters
    ----------
    csvFile: str
        Output file name.
    results: dict
        Results from calWms or calDas.
    specType: str
        Choose between 'WMS' and 'DAS'.

    Returns
    -------
    error: bool
        If there's an error, will return True.
    """
    headers = []

    # Generate a line for gas names
    line = 'Gas:,'
    for result in results:
        line += (result['gasParams']['gas'] + ',')
    headers.append(line[:-1])
    print line

    # Generate a line for path length
    line = 'Path lenght (cm):,'
    for result in results:
        line += (str(result['gasParams']['l']) + ',')
    headers.append(line[:-1])

    # Generate a line for concentration
    line = 'Conc. (volume ratio),'
    for result in results:
        line += (str(result['gasParams']['c']) + ',')
    headers.append(line[:-1])

    # Generate a line for pressure
    line = 'Pressure (hPa),'
    for result in results:
        line += (str(result['gasParams']['p']) + ',')
    headers.append(line[:-1])

    # Genearte a line for temperature
    line = 'Temperature (K),'
    for result in results:
        line += (str(result['gasParams']['t']) + ',')
    headers.append(line[:-1])

    # Separator
    line = '--,'
    for result in results:
        line += ('--,')
    headers.append(line[:-1])

    line = 'Nu (cm^-1),'
    for idx, result in enumerate(results):
        line += ('spec' + str(idx) + ',')
    headers.append(line[:-1])

    nu = results[0]['nu']
    print len(nu)
    spectra = []
    for result in results:
        spectra.append(result['spectrum'])

    print headers
    print '!'
    with open(csvFile, 'wb') as f:
        for line in headers:
            f.write(line + '\n')
        for idx, n in enumerate(nu):
            line = str(n) + ','
            for spectrum in spectra:
                line += (str(spectrum[idx]) + ',')
            f.write(line[:-1] + '\n')


def unitHandler(gasParams, unitDict):
    """
    Convert gas parameters with non-standard units to standard units that can be
    used in calDAS and calWMS.

    Parameters
    ----------
    gasParams: dict
        Gas parameters contain gas (gas name), l (path length in cm),
        c (concentration), t (temperature in K), p (pressure in hPa).
    unitDict: dict
        A dict has following keys: 'c', 'p', 't', 'l'.
    Returns
    -------
    p: float
        Pressure in atm.
    t: float
        Temperature in K.
    l: float
        Path length in cm.
    c: float
        Number density in molec/cm^3

    """
    # Pressure unit converstion
    p0 = gasParams['p']
    p = {'hPa': p0 / 1.013e3, 'kPa': p0 / 1.013e2, 'Torr': p0 / 760, 'atm': p0}[
        unitDict['p']]

    # Temperature unit conversion
    t0 = gasParams['t']
    t = {'K': t0, 'degC': t0 + 273.15, 'degF': (t0 + 459.67) * 5. / 9.}[
        unitDict['t']]

    # Path length unit conversion
    l0 = gasParams['l']
    l = {'cm': l0, 'm': 1e2 * l0, 'inch': 2.54 * l0}[unitDict['l']]

    # Concentration unit conversion
    c0 = gasParams['c']
    c = {'V ratio': p * 1.013e5 / kb / t * 1e-6 * c0, 'mol/m^3': nA * c0 * 1e-6}[
        unitDict['c']]

    return p, t, l, c


def dasFit(gasList, trate, dasData, nu, silence=True):
    """
    :param gasList: Gas list
    :param nu: Wavenumber range
    :param dasData: List of data contains measured DAS spectra for fitting
    :param dasBsl: Array of
    :return:
    """
    dasResults = calDas(gasList, nu, 'Voigt', 'Absorp coeff')
    n = dasData.shape[1]
    print n
    concPriori = []
    colDen = []
    for result in dasResults:
        p = result['gasParams']['p'] / 1.013e3
        t = result['gasParams']['t']
        l = result['gasParams']['l']
        c = result['gasParams']['c']
        numDen = mixRatio2numDen(c, p, t)
        colDen.append(numDen * l)
        concPriori.append(c)

    concPriori = np.array(concPriori)
    colDen = np.array(colDen)
    pkLoc = np.argmax(dasResults[0]['spectrum'])

    measPkLoc = np.argmax(dasData[:, 0])
    dasNu = (np.arange(len(dasData[:, 0])) - measPkLoc) * trate + pkLoc

    for i in range(0, n):
        matCoeff = []
        for idx, result in enumerate(dasResults):
            matCoeff.append(
                np.interp(dasNu, result['nu'], result['spectrum']) * colDen[idx])

        matCoeff = np.array(matCoeff).transpose()
        X = sm.add_constant(matCoeff)
        est = sm.RLM(dasData[:, i], X, M=sm.robust.norms.HuberT()).fit()
        if i == 0:
            conc = np.array(est.params[1:] * concPriori)
        else:
            conc = np.vstack((conc, est.params[1:] * concPriori))
        if not silence:
            plt.plot(dasNu, dasData[:, i])
            plt.plot(dasNu, np.dot(X, est.params))

    print concPriori
    return conc


def main():
    """
    Initiate HAPI and print out package name.

    Returns
    -------

    """

    hapi.db_begin_pickle('./Data')
    print 'specCal is package from spectroscopy calculation for QCL spectroscopy.'


main()
