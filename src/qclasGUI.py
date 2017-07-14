"""

Make a GUI for qclas. This program uses HAPI to generate absorption profiles.

The program comes in without HITRAN data files. User can use the program to

download lines they need.



GUI of the program is based on PyQt5.



Da Pan, v-alpha, started on 02/13/2016
Da Pan, V-0.5.1, changed from PyQt4 to PyQt5.
Da Pan, V-0.5.2, added function to import experimental spectra.

"""

import hapi

import numpy as np

from PyQt5 import QtCore, QtGui, QtWidgets
import sys

import os

import gasPropertyWidget

import matplotlib.pyplot as plt

from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas

from matplotlib.backends.backend_qt5agg import NavigationToolbar2QT as NavigationToolbar

import specCal

import dasRead

import six

import matplotlib


class mplCanvas(QtWidgets.QWidget):
    def __init__(self, parent=None, width=5, height=4, dpi=100, bgcolor='#ffffff'):
        super(mplCanvas, self).__init__(parent)

        # a figure instance to plot on

        self.figure = plt.figure(figsize=(width, height), dpi=dpi, facecolor=bgcolor)

        self.axes = self.figure.add_subplot(111)

        self.index = 0

        # this is the Canvas Widget that displays the `figure`

        # it takes the `figure` instance as a parameter to __init__

        self.canvas = FigureCanvas(self.figure)

        FigureCanvas.setSizePolicy(self.canvas,

                                   QtWidgets.QSizePolicy.Expanding,

                                   QtWidgets.QSizePolicy.Expanding)

        FigureCanvas.updateGeometry(self)

        # this is the Navigation widget

        # it takes the Canvas widget and a parent

        self.toolbar = NavigationToolbar(self.canvas, self)

        # Just some plotButton connected to `plot` method

        self.plotButton = QtWidgets.QPushButton('Plot', parent=self)

        self.exportButton = QtWidgets.QPushButton('Export', parent=self)

        # set the layout

        layout = QtWidgets.QVBoxLayout()

        layout.addWidget(self.toolbar)

        layout.addWidget(self.canvas)

        buttonHBox = QtWidgets.QHBoxLayout()

        buttonHBox.addWidget(self.plotButton)

        buttonHBox.addWidget(self.exportButton)

        layout.addLayout(buttonHBox)

        self.setLayout(layout)


class AppWindow(QtWidgets.QMainWindow):
    def __init__(self, parent=None):

        super(AppWindow, self).__init__(parent)

        self.setWindowTitle('QCLAS')

        self.scrsz = QtWidgets.QDesktopWidget().availableGeometry().getRect()

        self.dpi = int(self.scrsz[2] / 25)

        self.initUI()

    def resizeEvent(self, resizeEvent):

        self.updateCanvasGeometry()

    def initUI(self):

        # Action: set HAPI database Directory



        self.initMenu()

        self.gasListLabel = QtWidgets.QLabel()

        self.calGasList = []

        self.canvasList = []

        self.setGasListLabel()

        self.statusBar().addPermanentWidget(self.gasListLabel)

        self.mainWidget = QtWidgets.QWidget()

        self.setFrames()

        self.setLeftColumn()

        self.setCanvas()

        self.laserSpec = None

        self.setCalibFileDialog()

        self.setCentralWidget(self.mainWidget)

        self.resize(0.8 * self.scrsz[2], 0.8 * self.scrsz[3])

    def initMenu(self):

        # HITRAN Data menu

        chHapiDir = QtWidgets.QAction('&Change HITRAN Dir', self)

        chHapiDir.triggered.connect(self.setHapiDir)

        dnldData = QtWidgets.QAction('&Download HITRAN Data', self)

        dnldData.triggered.connect(self.fetchData)

        saveHData = QtWidgets.QAction('&Save HITRAN Data', self)

        saveHData.triggered.connect(self.commitHData)

        listHData = QtWidgets.QAction('Available HITRAN Data', self)

        listHData.triggered.connect(self.listHData)

        self.HapiMenu = QtWidgets.QMenu('&HITRAN Data', self)

        self.HapiMenu.addAction(chHapiDir)

        self.HapiMenu.addAction(dnldData)

        self.HapiMenu.addAction(saveHData)

        self.HapiMenu.addAction(listHData)

        # Laser setting menu

        loadLaserFile = QtWidgets.QAction('&Import laser config', self)

        loadLaserFile.triggered.connect(self.getLaserConfig)

        LoadExpSpec = QtWidgets.QAction('&Import spectrum', self)

        LoadExpSpec.triggered.connect(self.getExpSpec)

        self.importMenu = QtWidgets.QMenu('&Import')

        self.importMenu.addAction(loadLaserFile)

        self.importMenu.addAction(LoadExpSpec)

        # Calibration mode menu

        self.enterCaliMode = QtWidgets.QAction('Calibration mode', self, checkable=True)

        self.enterCaliMode.triggered.connect(self.showCaliMode)

        self.caliModeMenu = QtWidgets.QMenu('&Advance')

        self.caliModeMenu.addAction(self.enterCaliMode)

        # Save results menu

        # saveResults = QtGui.QAction('&')



        self.menuBar().addMenu(self.HapiMenu)

        self.menuBar().addMenu(self.importMenu)

        self.menuBar().addMenu(self.caliModeMenu)

    ##### BLOCK 1: HAPI data management


    def getLaserConfig(self):

        fileName = self.getFileNameDialog()

        self.laserSpec = specCal.read_config(fileName)

    def getDasDir(self):

        dirStr = self.getFileDirDialog()

        self.dasDir.setText(dirStr)

        self.calibDialog.raise_()

        self.calibDialog.activateWindow()

    def getWmsDir(self):

        wmsStr = self.getFileDirDialog()

        self.wmsDir.setText(wmsStr)

        self.calibDialog.raise_()

        self.calibDialog.activateWindow()

    def showCaliMode(self):

        if self.enterCaliMode.isChecked():

            self.calibDialog.show()

            self.numPanel.button(4).setChecked(True)

            self.plotTotalCheck.setEnabled(False)

            for button in self.numPanel.buttons():
                button.setEnabled(False)

            self.setCanvas()

            self.calibModeWidget.show()

        else:

            self.plotTotalCheck.setEnabled(True)

            for button in self.numPanel.buttons():
                button.setEnabled(True)

            self.calibModeWidget.hide()

        QtWidgets.QApplication.processEvents()

    def setCalibMode(self):

        self.calibModeWidget = QtWidgets.QWidget()

        vBox = QtWidgets.QVBoxLayout()

        bslLabel = QtWidgets.QLabel('Baseline name: ')

        self.bslName = QtWidgets.QLineEdit()

        bslOrderLabel = QtWidgets.QLabel('Order')

        self.bslOrder = QtWidgets.QLineEdit()

        bslHBox = QtWidgets.QHBoxLayout()

        bslHBox.addWidget(bslLabel)

        bslHBox.addWidget(self.bslName)

        bslHBox.addWidget(bslOrderLabel)

        bslHBox.addWidget(self.bslOrder)

        bslRngLabel = QtWidgets.QLabel('Baseline fit range:')

        self.bslRng = QtWidgets.QLineEdit()

        bslRngHBox = QtWidgets.QHBoxLayout()

        bslRngHBox.addWidget(bslRngLabel)

        bslRngHBox.addWidget(self.bslRng)

        fitButton = QtWidgets.QPushButton('Fit baseline')

        fitButton.clicked.connect(self.showBslFit)

        validRngLabel = QtWidgets.QLabel('Valid spec range:')

        validRngBox = QtWidgets.QHBoxLayout()

        self.validRng = QtWidgets.QLineEdit()

        validRngBox.addWidget(validRngLabel)

        validRngBox.addWidget(self.validRng)

        showAbsorbanceButton = QtWidgets.QPushButton('Show absorbance')

        showAbsorbanceButton.clicked.connect(self.calcAbsorbance)

        fitSettingBox = QtWidgets.QHBoxLayout()

        pkLocLabel = QtWidgets.QLabel('Peak nu: ')

        self.pkLoc = QtWidgets.QLineEdit()

        trateLabel = QtWidgets.QLabel('Tuning rate: ')

        self.trate = QtWidgets.QLineEdit()

        fitSettingBox.addWidget(pkLocLabel)

        fitSettingBox.addWidget(self.pkLoc)

        fitSettingBox.addWidget(trateLabel)

        fitSettingBox.addWidget(self.trate)

        fitAbsButton = QtWidgets.QPushButton()

        fitAbsButton.clicked.connect(self.dasFit)

        fitSettingBox.addWidget(fitAbsButton)

        vBox.addLayout(bslHBox)

        vBox.addLayout(bslRngHBox)

        vBox.addWidget(fitButton)

        vBox.addLayout(validRngBox)

        vBox.addWidget(showAbsorbanceButton)

        vBox.addLayout(fitSettingBox)

        self.calibModeWidget.setLayout(vBox)

        self.calibModeWidget.hide()

    def setCalibFileDialog(self):

        self.calibDialog = QtWidgets.QDialog()

        self.calibDialog.setWindowTitle('Open calibration files')

        vBox = QtWidgets.QVBoxLayout()

        calibTitle = QtWidgets.QLabel('Calibration setting')

        dasDirHBox = QtWidgets.QHBoxLayout()

        dasDirLabel = QtWidgets.QLabel('DAS dir: ')

        self.dasDir = QtWidgets.QLineEdit()

        dasDirButton = QtWidgets.QPushButton('...')

        dasDirButton.clicked.connect(self.getDasDir)

        dasDirHBox.addWidget(dasDirLabel)

        dasDirHBox.addWidget(self.dasDir)

        dasDirHBox.addWidget(dasDirButton)

        dasPrefixHBox = QtWidgets.QHBoxLayout()

        dasPrefixLabel = QtWidgets.QLabel('DAS prefix')

        self.dasPrefix = QtWidgets.QLineEdit()

        dasIdxRngLabel = QtWidgets.QLabel('Range (start:end):')

        self.dasIdxRng = QtWidgets.QLineEdit()

        dasPrefixHBox.addWidget(dasPrefixLabel)

        dasPrefixHBox.addWidget(self.dasPrefix)

        dasPrefixHBox.addWidget(dasIdxRngLabel)

        dasPrefixHBox.addWidget(self.dasIdxRng)

        wmsDirHBox = QtWidgets.QHBoxLayout()

        wmsDirLabel = QtWidgets.QLabel('WMS dir: ')

        self.wmsDir = QtWidgets.QLineEdit()

        wmsDirButton = QtWidgets.QPushButton('...')

        wmsDirButton.clicked.connect(self.getWmsDir)

        wmsDirHBox.addWidget(wmsDirLabel)

        wmsDirHBox.addWidget(self.wmsDir)

        wmsDirHBox.addWidget(wmsDirButton)

        wmsPrefixHBox = QtWidgets.QHBoxLayout()

        wmsPrefixLabel = QtWidgets.QLabel('DAS prefix')

        self.wmsPrefix = QtWidgets.QLineEdit()

        wmsPrefixHBox.addWidget(wmsPrefixLabel)

        wmsPrefixHBox.addWidget(self.wmsPrefix)

        okButton = QtWidgets.QPushButton('Import data')

        okButton.clicked.connect(self.readDasData)

        vBox.addWidget(calibTitle)

        vBox.addLayout(dasDirHBox)

        vBox.addLayout(dasPrefixHBox)

        vBox.addLayout(wmsDirHBox)

        vBox.addLayout(wmsPrefixHBox)

        vBox.addWidget(okButton)

        self.calibDialog.setLayout(vBox)

    def readDasData(self):

        print self.dasIdxRng.text()

        dasIdxRng = map(int, str(self.dasIdxRng.text()).split(':'))

        print dasIdxRng

        self.dasMeas = dasRead.dasSignal(location=str(self.dasDir.text()),

                                         idx_range=range(dasIdxRng[0], dasIdxRng[

                                             1]),

                                         prefix=str(self.dasPrefix.text()))

        canvas = self.canvasList[0]

        canvas.axes.plot(self.dasMeas.data)

        canvas.figure.tight_layout()

        canvas.canvas.draw()

        canvas.canvas.updateGeometry()

    def getFileNameDialog(self):

        fileName = QtWidgets.QFileDialog.getOpenFileName(self)[0]
        return fileName

    def getFileDirDialog(self):

        DirName = QtWidgets.QFileDialog.getExistingDirectory(self)

        return DirName

    def getGasList(self):

        self.gasList = hapi.getTableList()

        hapi.getTableList()

        self.gasList.remove('sampletab')

    def setGasListLabel(self):

        self.getGasList()

        if len(self.gasList) == 0:

            self.gasListLabel.setText('No Data')

        else:

            self.gasListLabel.setText('Data ready for: ' + ', '.join(self.gasList))

    def setHapiDir(self):

        dbDir = self.getFileDirDialog()

        hapi.db_begin_pickle(dbDir)

        for gas in self.gasList:
            hapi.dropTable(gas)

        self.gasList = []

        self.setGasListLabel()

        self.scrollGasPanel.gasList = self.gasList

        self.scrollGasPanel.updateAll()

        hapi.tableList()

    def fetchData(self):

        inputStr, ok = QtWidgets.QInputDialog.getText(self, 'Add data',

                                                      "Temporarily add data to the database; the data will not be saved." +

                                                      "\nLarge database will slow down loading processes when start the program." +

                                                      "\nTo Save the data, use 'Save HITRAN data'." +

                                                      "\n\nEnter Gas name, min, and max wavenumber separated by ',' (e.g. H2O,1000,2000)")

        if ok:

            params = str(inputStr).split(',')

            for i in range(40):

                try:

                    name = hapi.moleculeName(i + 1)

                    if name == params[0]:
                        M = i + 1

                        print M

                except:

                    pass

            # try:

            print params[0]

            hapi.fetch_pickle(params[0], M, 1, int(params[1]), int(params[2]))

            nu = hapi.getColumn(params[0], 'nu')

            self.statusBar().showMessage(

                str(len(nu)) + ' lines' + ' added for ' + params[0] + ' ' + params[

                    1] + '<nu<' + params[2])

            # except:

            #     self.statusBar().showMessage('Data fetch failed')

        self.setGasListLabel()

        self.scrollGasPanel.gasList = self.gasList

        self.scrollGasPanel.updateAll()

    def commitHData(self):

        hapi.db_commit_pickle()

        self.statusBar().showMessage('HITRAN data saved')

    ##### End of BLOCK 1.


    def getExpSpec(self):

        fileName = self.getFileNameDialog()

        try:
            self.importedSpec = np.genfromtxt(fileName)
        except:
            self.showError('Cannot find or read the file!', details='The file should be pure numbers')


    def setWaveRangeWidget(self):

        # TODO add cm-1, nm, um conversion

        self.waveRangeWidget = QtWidgets.QWidget(self.mainWidget)

        hbox = QtWidgets.QHBoxLayout()

        label1 = QtWidgets.QLabel('Nu range: ')

        label2 = QtWidgets.QLabel('to')

        self.minNu = QtWidgets.QLineEdit(self.mainWidget)

        self.minNu.setText('1000')

        self.minNu.setMaximumWidth(90)

        self.maxNu = QtWidgets.QLineEdit(self.mainWidget)

        self.maxNu.setText('1100')

        self.maxNu.setMaximumWidth(90)

        hbox.addWidget(label1)

        hbox.addWidget(self.minNu)

        hbox.addWidget(label2)

        hbox.addWidget(self.maxNu)

        labelNumPt = QtWidgets.QLabel('; # of point: ')

        self.numPt = QtWidgets.QLineEdit(self.mainWidget)

        self.numPt.setText('1000')

        self.numPt.setMaximumWidth(70)

        hbox.addWidget(labelNumPt)

        hbox.addWidget(self.numPt)

        hbox.setAlignment(QtCore.Qt.AlignLeft)

        hbox.setContentsMargins(0, 0, 0, 0)
        self.waveRangeWidget.setLayout(hbox)

    def setSpecWidget(self):

        self.specWidget = QtWidgets.QWidget(self.mainWidget)

        hbox = QtWidgets.QHBoxLayout()

        labelWhatPlot = QtWidgets.QLabel('   Plot: ')

        self.specChecks = QtWidgets.QButtonGroup(self.mainWidget)

        wmsCheck = QtWidgets.QRadioButton(self.mainWidget)

        dasCheck = QtWidgets.QRadioButton(self.mainWidget)

        wmsCheck.setText('WMS')

        dasCheck.setText('DAS')

        dasCheck.clicked.connect(self.chComboWhatPlot)

        wmsCheck.clicked.connect(self.chComboWhatPlot)

        self.comboWhatPlot = QtWidgets.QComboBox(self.mainWidget)

        self.specChecks.addButton(dasCheck, 1)

        self.specChecks.addButton(wmsCheck, 2)

        dasCheck.setChecked(True)

        self.chComboWhatPlot()

        hbox.addWidget(dasCheck)

        hbox.addWidget(wmsCheck)

        hbox.addWidget(labelWhatPlot)

        hbox.addWidget(self.comboWhatPlot)

        hbox.setAlignment(QtCore.Qt.AlignLeft)

        hbox.setContentsMargins(0, 0, 0, 0)
        hbox.setSpacing(10)

        self.specWidget.setLayout(hbox)

    def setLineShapeWidget(self):

        self.lineShapeWidget = QtWidgets.QWidget(self.mainWidget)

        lineShapeLabel = QtWidgets.QLabel('Line shape profile: ')

        self.comboLineShape = QtWidgets.QComboBox(self.mainWidget)

        self.comboLineShape.addItems(['Voigt', 'HT', 'Lorentz', 'Doppler'])

        hbox = QtWidgets.QHBoxLayout()

        hbox.addWidget(lineShapeLabel)

        hbox.addWidget(self.comboLineShape)

        hbox.setAlignment(QtCore.Qt.AlignLeft)

        hbox.setContentsMargins(0, 0, 0, 0)
        self.lineShapeWidget.setLayout(hbox)

    def setNumPanelWidget(self):

        self.numPanelWidget = QtWidgets.QWidget()

        self.numPanel = QtWidgets.QButtonGroup(self.mainWidget)

        onePanel = QtWidgets.QRadioButton(self.mainWidget)

        onePanel.setText('1')

        onePanel.setChecked(True)

        onePanel.clicked.connect(self.setCanvas)

        twoPanel = QtWidgets.QRadioButton(self)

        twoPanel.setText('2')

        twoPanel.clicked.connect(self.setCanvas)

        fourPanel = QtWidgets.QRadioButton(self)

        fourPanel.setText('4')

        fourPanel.clicked.connect(self.setCanvas)

        numLabel = QtWidgets.QLabel('# of panel: ')

        self.plotTotalCheck = QtWidgets.QCheckBox('Plot total')

        self.plotTotalCheck.setChecked(True)

        hbox = QtWidgets.QHBoxLayout()

        hbox.addWidget(numLabel)

        hbox.addWidget(onePanel)

        hbox.addWidget(twoPanel)

        hbox.addWidget(fourPanel)

        hbox.addWidget(self.plotTotalCheck)

        self.numPanel.addButton(onePanel, 1)

        self.numPanel.addButton(twoPanel, 2)

        self.numPanel.addButton(fourPanel, 4)

        hbox.setAlignment(QtCore.Qt.AlignLeft)

        hbox.setContentsMargins(0, 0, 0, 0)
        self.numPanelWidget.setLayout(hbox)

    def setWmsMethodWidget(self):

        self.wmsMethodWidget = QtWidgets.QWidget(self.mainWidget)

        hbox = QtWidgets.QHBoxLayout()

        labelWmsMethod = QtWidgets.QLabel('WMS calculation method: ')

        self.wmsMethod = QtWidgets.QComboBox(self.mainWidget)

        self.wmsMethod.addItem('Theoretical', 1)

        self.wmsMethod.addItem('Simulation w/ params', 2)

        hbox.addWidget(labelWmsMethod)

        hbox.addWidget(self.wmsMethod)

        hbox.setContentsMargins(0, 0, 0, 0)
        self.wmsMethodWidget.setLayout(hbox)

    def setWmsModWidget(self):

        self.wmsModWidget = QtWidgets.QWidget(self.mainWidget)

        hbox = QtWidgets.QHBoxLayout()

        labelWmsMod = QtWidgets.QLabel('WMS modulation: ')

        labelModUnit = QtWidgets.QLabel('cm -1')

        self.leWmsMod = QtWidgets.QLineEdit('0.01')

        hbox.addWidget(labelWmsMod)

        hbox.addWidget(self.leWmsMod)

        hbox.addWidget(labelModUnit)

        hbox.setContentsMargins(0, 0, 0, 0)
        self.wmsModWidget.setLayout(hbox)

    def setICutWidget(self):

        self.iCutWidget = QtWidgets.QWidget(self.mainWidget)

        hbox = QtWidgets.QHBoxLayout()

        labelIcut = QtWidgets.QLabel('Intensity threshold: ')

        labelIcut.setMaximumWidth(150)

        self.leICut = QtWidgets.QLineEdit(self.mainWidget)

        self.leICut.setText('1e-30')

        self.leICut.setMaximumWidth(90)

        self.leICut.setAlignment(QtCore.Qt.AlignLeft)

        hbox.addWidget(labelIcut)

        hbox.addWidget(self.leICut)

        hbox.setSpacing(10)

        hbox.setContentsMargins(0, 0, 0, 0)
        hbox.setAlignment(QtCore.Qt.AlignLeft)

        self.iCutWidget.setLayout(hbox)

    def setLeftColumn(self):

        vboxTop = QtWidgets.QVBoxLayout()

        vboxBottom = QtWidgets.QVBoxLayout()

        self.scrollGasPanel = gasPropertyWidget.scrollPanel(self.mainWidget,

                                                            gasList=self.gasList)

        self.setWaveRangeWidget()

        self.setSpecWidget()

        self.setWmsMethodWidget()

        self.setWmsModWidget()

        self.setLineShapeWidget()

        self.setICutWidget()

        self.setNumPanelWidget()

        self.setCalibMode()

        vboxBottom.addWidget(self.waveRangeWidget)

        vboxBottom.addWidget(self.specWidget)

        vboxBottom.addWidget(self.wmsMethodWidget)

        vboxBottom.addWidget(self.wmsModWidget)

        vboxBottom.addWidget(self.lineShapeWidget)

        vboxBottom.addWidget(self.iCutWidget)

        vboxBottom.addWidget(self.numPanelWidget)

        vboxBottom.addWidget(self.calibModeWidget)

        vboxBottom.setAlignment(QtCore.Qt.AlignTop)

        vboxTop.addWidget(self.scrollGasPanel)

        self.leftTop.setLayout(vboxTop)

        self.leftBottom.setLayout(vboxBottom)

    def genUnitDict(self):

        """

        Generate unit dict to be passed down to specCal.

        Returns

        -------

        unitDict: dict

            A dict has following keys: 'c', 'p', 't', 'l'

        """

        unitDict = {}

        unitDict['c'] = str(self.scrollGasPanel.concUnit.currentText())

        unitDict['p'] = str(self.scrollGasPanel.pressUnit.currentText())

        unitDict['t'] = str(self.scrollGasPanel.tempUnit.currentText())

        unitDict['l'] = str(self.scrollGasPanel.lengthUnit.currentText())

        return unitDict

    def setCanvas(self):

        numPanel = self.numPanel.checkedId()

        self.grid = QtWidgets.QGridLayout()

        for canvas in self.canvasList:
            self.grid.removeWidget(canvas)

            canvas.deleteLater()

            canvas.close()

            canvas.setParent(None)

        self.canvasList = []

        self.resultList = []

        position = [[1, 0], [2, 0], [1, 1], [2, 1]]

        for i in range(numPanel):
            canvas = mplCanvas(self, dpi=self.dpi)

            canvas.plotButton.clicked.connect(self.calPlot)

            canvas.exportButton.clicked.connect(self.exportData)

            canvas.index = i

            self.canvasList.append(canvas)

            self.resultList.append({})

            self.grid.addWidget(canvas, position[i][0], position[i][1])

            # canvas.draw()

        self.vboxRight.addLayout(self.grid)

    def chComboWhatPlot(self):

        if self.specChecks.checkedId() == 1:

            self.comboWhatPlot.clear()

            self.comboWhatPlot.addItem('Absorp coeff')

            self.comboWhatPlot.addItem('Absorbance')

            self.comboWhatPlot.addItem('Transmission')

        else:

            self.comboWhatPlot.clear()

            for i in range(12):
                self.comboWhatPlot.addItem(str(i + 1) + 'f')

    def setFrames(self):

        self.leftTop = QtWidgets.QGroupBox(self.mainWidget)

        self.leftTop.setTitle('Set gas properties')

        self.leftBottom = QtWidgets.QGroupBox(self.mainWidget)

        self.leftBottom.setTitle('Set plot properties')

        self.right = QtWidgets.QGroupBox(self.mainWidget)

        self.right.setTitle('Results')

        self.vboxRight = QtWidgets.QVBoxLayout()

        self.right.setLayout(self.vboxRight)

        self.split1 = QtWidgets.QSplitter(QtCore.Qt.Vertical)

        self.split1.addWidget(self.leftTop)

        self.split1.addWidget(self.leftBottom)

        self.split2 = QtWidgets.QSplitter(QtCore.Qt.Horizontal)

        self.split2.addWidget(self.split1)

        self.split2.addWidget(self.right)

        self.split2.setStretchFactor(1, 2)

        hbox = QtWidgets.QHBoxLayout()

        hbox.addWidget(self.split2)

        self.mainWidget.setLayout(hbox)

    def showError(self, errStr, details):

        errBox = QtWidgets.QMessageBox(self)

        errBox.setIcon(QtWidgets.QMessageBox.Information)

        errBox.setText(errStr)

        errBox.setDetailedText(details)

        errBox.setWindowTitle('Error message')

        errBox.setStandardButtons(QtWidgets.QMessageBox.Ok)

    def calPlot(self):

        canvas = self.sender().parent()

        print canvas.index

        unitDict = self.genUnitDict()

        nuMin = float(self.minNu.text())

        nuMax = float(self.maxNu.text())

        numPt = int(self.numPt.text())

        nu = np.linspace(nuMin, nuMax, numPt)

        iCut = float(self.leICut.text())

        gasParamsList = self.scrollGasPanel.getGasInfo()

        profile = self.comboLineShape.currentText()

        mode = self.comboWhatPlot.currentText()

        self.statusBar().showMessage('Calculating...')

        if self.specChecks.checkedId() == 1:

            dasResults = specCal.calDas(gasParamsList, nu, profile, mode,

                                        iCut=iCut, unitDict=unitDict)

            if type(dasResults) is str:

                errorMessage = QtWidgets.QMessageBox()

                errorMessage.setText(dasResults)

                errorMessage.exec_()

                self.statusBar().showMessage(dasResults)

            else:

                specCal.plotDas(canvas.axes, dasResults, mode,

                                showTotal=self.plotTotalCheck.isChecked(),

                                unitDict=unitDict)

                self.statusBar().showMessage('Done.')

            self.resultList[canvas.index] = dasResults



        else:

            method = self.wmsMethod.currentText()

            dNu = float(self.leWmsMod.text())

            nf = int(mode.replace('f', ''))

            if method == 'Theoretical':

                wmsResults = specCal.calWms(gasParamsList, nu, profile, nf, method,

                                            dNu=dNu, unitDict=unitDict)

            else:

                if self.laserSpec is None:

                    self.showError('No laser configuration.', 'Please go to Laser '

                                                              'config and load a '

                                                              'laser configuration.')

                    wmsResults = 'No laser configuration.'

                else:

                    # self.laserSpec['central_wavelength'] = (nuMin + nuMax) / 2.

                    # self.laserSpec['aRamp'] = (nuMax -

                    #                            nuMin) / 200 * 1e3 / self.laserSpec[

                    #                               'tRamp']

                    wmsResults = specCal.calWms(gasParamsList, nu, profile, nf,

                                                'Simulation with parameters',

                                                laserSpec=self.laserSpec,

                                                unitDict=unitDict)

            if type(wmsResults) is str:

                errorMessage = QtWidgets.QMessageBox()

                errorMessage.setText(wmsResults)

                errorMessage.exec_()

                self.statusBar().showMessage(wmsResults)

            else:

                self.statusBar().showMessage('Done.')

                specCal.plotWms(canvas.axes, wmsResults,

                                showTotal=self.plotTotalCheck.isChecked(),

                                unitDict=unitDict)

            self.resultList[canvas.index] = wmsResults

        canvas.figure.tight_layout()

        canvas.canvas.draw()

        canvas.canvas.updateGeometry()

    def exportData(self):

        canvas = self.sender().parent()

        filename, pat = QtWidgets.QFileDialog.getSaveFileName(self, "Export "

                                                                    "data "

                                                                    "to csv file",

                                                              "output.csv",

                                                              filter=self.tr(

                                                                  "CSV "

                                                                  "files (*.csv)"))

        specCal.csvOutput(filename, self.resultList[canvas.index])

    def showBslFit(self):

        rngStrs = str(self.bslRng.text()).split(',')

        bslRng = []

        for rng in rngStrs:
            idx = map(int, rng.split(':'))

            bslRng.append(slice(idx[0], idx[1]))

        self.dasMeas.bslFit(str(self.bslName.text()), bslRng, silent=True,

                            order=int(str(self.bslOrder.text())))

        canvas = self.canvasList[0]

        # canvas.axes.clf()

        canvas.axes.plot(self.dasMeas.bsl)

        canvas.figure.tight_layout()

        canvas.canvas.draw()

        canvas.canvas.updateGeometry()

    def calcAbsorbance(self):

        validRng = map(int, str(self.validRng.text()).split(':'))

        self.dasMeas.getAbsorp(validRng)

        canvas = self.canvasList[2]

        canvas.axes.plot(self.dasMeas.absorbance)

        canvas.figure.tight_layout()

        canvas.canvas.draw()

        canvas.canvas.updateGeometry()

    def dasFit(self):

        nuMin = float(self.minNu.text())

        nuMax = float(self.maxNu.text())

        numPt = int(self.numPt.text())

        nu = np.linspace(nuMin, nuMax, numPt)

        self.dasConc = specCal.dasFit(self.scrollGasPanel.getGasInfo(), float(str(

            self.trate.text())), self.dasMeas.absorbance, nu, silence=False)

    def updateCanvasGeometry(self):

        for canvas in self.canvasList:
            canvas.figure.tight_layout()

            canvas.canvas.updateGeometry()

    def listHData(self):

        dialog = QtWidgets.QDialog(self.mainWidget)

        vboxScroll = QtWidgets.QVBoxLayout()

        scrollWidget = QtWidgets.QWidget(self.mainWidget)

        scrollArea = QtWidgets.QScrollArea(self.mainWidget)

        closeButton = QtWidgets.QPushButton('Close')

        closeButton.clicked.connect(dialog.close)

        vboxDialog = QtWidgets.QVBoxLayout()

        for gas in self.gasList:
            nu = np.array(hapi.getColumn(gas, 'nu'))

            gasInfo = gas + ' :' + str(nu.min()) + ' to ' + str(nu.max()) + ' cm -1'

            labelGasInfo = QtWidgets.QLabel(gasInfo)

            vboxScroll.addWidget(labelGasInfo)

        vboxScroll.setAlignment(QtCore.Qt.AlignTop)

        scrollWidget.setLayout(vboxScroll)

        scrollArea.setWidget(scrollWidget)

        vboxDialog.addWidget(scrollArea)

        vboxDialog.addWidget(closeButton)

        dialog.setWindowTitle('Available HITRAN data')

        dialog.setMinimumWidth(0.3 * self.scrsz[2])

        dialog.setLayout(vboxDialog)

        dialog.show()


def resource_path(relative):
    if hasattr(sys, "_MEIPASS"):
        return os.path.join(sys._MEIPASS, relative)

    return os.path.join(relative)


def main():
    filename = 'defaultSettings.txt'

    app = QtWidgets.QApplication(sys.argv)

    appWindow = AppWindow()

    appWindow.show()

    sys.exit(app.exec_())


if __name__ == '__main__':
    main()
