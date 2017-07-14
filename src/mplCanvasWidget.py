"""
Define the widget for showing matplotlib in main GUI.
"""
from PyQt5 import QtCore, QtGui, QtWidgets
from matplotlib.figure import Figure

from matplotlib.backends.backend_qt4agg import FigureCanvasQTAgg as FigureCanvas

import sys



class mplCanvas(FigureCanvas):
    def __init__(self, parent=None, width=5, height=4, dpi=100):
        fig = Figure(figsize=(width, height), dpi=dpi)
        self.axes = fig.add_subplot(111)
        # We want the axes cleared every time plot() is called

        #
        FigureCanvas.__init__(self, fig)
        self.setParent(parent)

        FigureCanvas.setSizePolicy(self,
                                   QtWidgets.QSizePolicy.Expanding,
                                   QtWidgets.QSizePolicy.Expanding)
        FigureCanvas.updateGeometry(self)


class plotArea(QtWidgets.QWidget):
    def __init__(self, parent):
        super(plotArea, self).__init__(parent)

        self.vbox = QtWidgets.QVBoxLayout()
        self.vbox.setAlignment(QtCore.Qt.AlignTop)

        self.canvasList = []

        self.setNumPanelWidget()
        self.setCanvas()

        self.vbox.addLayout(self.grid)
        # self.resize(800, 1200)
        self.setLayout(self.vbox)

    def setNumPanelWidget(self):
        self.numPanel = QtWidgets.QButtonGroup(self)
        onePanel = QtWidgets.QRadioButton(self)
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
        hbox = QtWidgets.QHBoxLayout()
        hbox.addWidget(numLabel)
        hbox.addWidget(onePanel)
        hbox.addWidget(twoPanel)
        hbox.addWidget(fourPanel)
        self.numPanel.addButton(onePanel, 1)
        self.numPanel.addButton(twoPanel, 2)
        self.numPanel.addButton(fourPanel, 4)
        hbox.setAlignment(QtCore.Qt.AlignLeft)
        self.vbox.addLayout(hbox)

    def setCanvas(self):
        numPanel = self.numPanel.checkedId()
        self.grid = QtWidgets.QGridLayout()
        for canvas in self.canvasList:
            self.grid.removeWidget(canvas)
            canvas.deleteLater()
            canvas.close()
            canvas.setParent(None)
        self.canvasList = []

        position = [[1, 0], [2, 0], [1, 1], [2, 1]]
        for i in range(numPanel):
            canvas = mplCanvas(self)
            self.canvasList.append(canvas)
            self.grid.addWidget(canvas, position[i][0], position[i][1])
            # canvas.draw()

        self.vbox.addLayout(self.grid)
        self.setLayout(self.vbox)
        print(self.grid)
        print(self.canvasList)


def main():
    app = QtWidgets.QApplication(sys.argv)
    ex = plotArea(None)
    ex.show()
    sys.exit(app.exec_())


if __name__ == '__main__':
    main()
