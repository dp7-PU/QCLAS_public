"""
Create line with five text edits.
"""
from PyQt5 import QtCore, QtGui, QtWidgets
import sys


# TODO: Divide system into several submodule.

class gasLineEdit(QtWidgets.QWidget):
    def __init__(self, parent=None, dataList=[]):
        super(gasLineEdit, self).__init__(parent)
        self.setAttribute(QtCore.Qt.WA_DeleteOnClose)
        self.gasSelect = QtWidgets.QComboBox(parent)
        self.gasSelect.addItem('None')
        self.gasParams = {'gas': None, 'c': 0, 'p': 1000, 't': 296, 'l': 100}
        for gas in dataList:
            self.gasSelect.addItem(gas)

        cLE = QtWidgets.QLineEdit(parent)
        cLE.setText('0')
        pLE = QtWidgets.QLineEdit(parent)
        pLE.setText('1000')
        tLE = QtWidgets.QLineEdit(parent)
        tLE.setText('296')
        lLE = QtWidgets.QLineEdit(parent)
        lLE.setText('100')
        hbox = QtWidgets.QHBoxLayout()

        closeButton = QtWidgets.QPushButton('-')
        closeButton.setFixedWidth(20)
        closeButton.clicked.connect(self.closeup)

        pLE.textEdited[str].connect(self.assignP)
        tLE.textEdited[str].connect(self.assignT)
        lLE.textEdited[str].connect(self.assignL)
        cLE.textEdited[str].connect(self.assignC)
        self.gasSelect.activated[str].connect(self.assignGas)

        hbox.addWidget(self.gasSelect)
        hbox.addWidget(cLE)
        hbox.addWidget(pLE)
        hbox.addWidget(tLE)
        hbox.addWidget(lLE)
        hbox.addWidget(closeButton)
        hbox.setAlignment(QtCore.Qt.AlignLeft)
        hbox.setContentsMargins(0, 0, 0, 0)
        self.setLayout(hbox)

    def assignGas(self, text):
        try:
            self.gasParams['gas'] = str(text)
        except:
            pass

    def assignP(self, text):
        try:
            self.gasParams['p'] = float(text)
        except:
            pass

    def assignT(self, text):
        try:
            self.gasParams['t'] = float(text)
        except:
            pass

    def assignL(self, text):
        try:
            self.gasParams['l'] = float(text)
        except:
            pass

    def assignC(self, text):
        try:
            self.gasParams['c'] = float(text)
        except:
            pass

    def closeup(self):
        self.close()
        self.gasParams = None


class scrollPanel(QtWidgets.QWidget):
    def __init__(self, parent, gasList=[]):
        super(scrollPanel, self).__init__(parent)

        self.gasHandleList = []
        self.addButton = QtWidgets.QPushButton('Add Gas')
        self.addButton.clicked.connect(self.addGas)
        self.gasList = gasList
        headerWidget = QtWidgets.QWidget(self)
        hboxHeader = QtWidgets.QHBoxLayout()
        unitWidget = QtWidgets.QWidget(self)
        unitHBox = QtWidgets.QHBoxLayout()
        leGas = QtWidgets.QLabel('Gas')
        leC = QtWidgets.QLabel('C')
        leP = QtWidgets.QLabel('P ')
        leT = QtWidgets.QLabel('T ')
        leL = QtWidgets.QLabel('L ')
        leE = QtWidgets.QLabel('Delete')
        # leE.setFixedWidth()

        unitLabel = QtWidgets.QLabel('Unit: ')
        self.concUnit = QtWidgets.QComboBox()
        self.concUnit.addItems(['V ratio', 'mol/m^3'])
        self.pressUnit = QtWidgets.QComboBox()
        self.pressUnit.addItems(['hPa', 'kPa', 'Torr'])
        self.tempUnit = QtWidgets.QComboBox()
        self.tempUnit.addItems(['K', 'degC', 'degF'])
        self.lengthUnit = QtWidgets.QComboBox()
        self.lengthUnit.addItems(['cm', 'm', 'inch'])
        noneLabel = QtWidgets.QLabel(' ')

        # Header layout
        hboxHeader.addWidget(leGas)
        hboxHeader.addWidget(leC)
        hboxHeader.addWidget(leP)
        hboxHeader.addWidget(leT)
        hboxHeader.addWidget(leL)
        hboxHeader.addWidget(leE)
        hboxHeader.setSpacing(5)
        hboxHeader.setContentsMargins(0, 0, 0, 0)
        headerWidget.setLayout(hboxHeader)

        # Add widgets to unit row layout (2nd row)
        unitHBox.addWidget(unitLabel)
        unitHBox.addWidget(self.concUnit)
        unitHBox.addWidget(self.pressUnit)
        unitHBox.addWidget(self.tempUnit)
        unitHBox.addWidget(self.lengthUnit)
        unitHBox.addWidget(noneLabel)
        unitHBox.setSpacing(5)
        unitHBox.setContentsMargins(0, 0, 0, 0)
        unitWidget.setLayout(unitHBox)

        # scroll area widget contents - layout
        self.vbox = QtWidgets.QVBoxLayout()
        self.vbox.setAlignment(QtCore.Qt.AlignTop)
        self.vbox.addWidget(headerWidget)
        self.vbox.addWidget(unitWidget)
        # scroll area widget contents
        self.scrollWidget = QtWidgets.QWidget()
        self.scrollWidget.setLayout(self.vbox)

        # scroll area
        self.scrollArea = QtWidgets.QScrollArea()
        self.scrollArea.setWidgetResizable(True)
        self.scrollArea.setWidget(self.scrollWidget)
        # self.scrollArea.setMinimumWidth(480)

        # main layout
        self.mainLayout = QtWidgets.QVBoxLayout()

        # add all main to the main vLayout
        self.mainLayout.addWidget(self.addButton)
        self.mainLayout.addWidget(self.scrollArea)

        self.setLayout(self.mainLayout)

        self.resize(600, 600)

    def addGas(self):
        gasLayout = gasLineEdit(self, dataList=self.gasList)
        self.gasHandleList.append(gasLayout)
        self.vbox.addWidget(gasLayout)

    def updateAll(self):
        for gasHandle in self.gasHandleList:
            if gasHandle.gasParams is not None:
                gasHandle.gasSelect.clear()
                gasHandle.gasSelect.addItem('None')
                print(self.gasList)
                gasHandle.gasSelect.addItems(self.gasList)
            else:
                self.gasHandleList.remove(gasHandle)

    def getGasInfo(self):
        gasParamsList = []
        for gasHandle in self.gasHandleList:
            if gasHandle.gasParams is not None:
                print gasHandle.gasParams
                gasParamsList.append(gasHandle.gasParams)
            else:
                self.gasHandleList.remove(gasHandle)
        return gasParamsList


def main():
    app = QtWidgets.QApplication(sys.argv)
    ex = scrollPanel(None)
    ex.show()
    sys.exit(app.exec_())


if __name__ == '__main__':
    main()
