# -*- coding: utf-8 -*-

import sys
from PyQt4 import QtGui

from controller import controller



def main():
    app = QtGui.QApplication( sys.argv )
    app_window = controller.CurrentQt()
    app_window.show()
    app.exec_()

if __name__ == '__main__':
    app = QtGui.QApplication( sys.argv )
    app_window = controller.CurrentQt()
    app_window.show()
    sys.exit(app.exec_())



