# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'dev_info.ui'
#
# Created by: PyQt5 UI code generator 5.11.3
#
# WARNING! All changes made in this file will be lost!

from PyQt5 import QtCore, QtGui, QtWidgets

class Ui_Software(object):
    def setupUi(self, Software):
        Software.setObjectName("Software")
        Software.resize(650, 250)
        Software.setMinimumSize(QtCore.QSize(650, 250))
        self.labelInfo = QtWidgets.QLabel(Software)
        self.labelInfo.setGeometry(QtCore.QRect(80, 140, 471, 51))
        self.labelInfo.setStyleSheet("font: 25 12pt \"Calibri Light\";")
        self.labelInfo.setObjectName("labelInfo")
        self.labelLogo = QtWidgets.QLabel(Software)
        self.labelLogo.setGeometry(QtCore.QRect(150, 50, 331, 61))
        self.labelLogo.setStyleSheet("font: 25 8pt \"Calibri Light\";\n"
"font: 18pt \"MS Shell Dlg 2\";")
        self.labelLogo.setObjectName("labelLogo")

        self.retranslateUi(Software)
        QtCore.QMetaObject.connectSlotsByName(Software)

    def retranslateUi(self, Software):
        _translate = QtCore.QCoreApplication.translate
        Software.setWindowTitle(_translate("Software", "Dialog"))
        self.labelInfo.setText(_translate("Software", "Any Question, Send E-Mail to chan.luo@nxp.com"))
        self.labelLogo.setText(_translate("Software", "ezLNT Test Software"))

