# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'login_.ui'
#
# Created by: PyQt5 UI code generator 5.11.3
#
# WARNING! All changes made in this file will be lost!

from PyQt5 import QtCore, QtGui, QtWidgets

class Ui_LogIn(object):
    def setupUi(self, LogIn):
        LogIn.setObjectName("LogIn")
        LogIn.resize(397, 292)
        LogIn.setMinimumSize(QtCore.QSize(270, 200))
        self.lblLoginChooseMode = QtWidgets.QLabel(LogIn)
        self.lblLoginChooseMode.setGeometry(QtCore.QRect(20, 20, 151, 41))
        font = QtGui.QFont()
        font.setFamily("Calibri Light")
        font.setPointSize(12)
        self.lblLoginChooseMode.setFont(font)
        self.lblLoginChooseMode.setObjectName("lblLoginChooseMode")
        self.btnLoginEnter = QtWidgets.QPushButton(LogIn)
        self.btnLoginEnter.setEnabled(False)
        self.btnLoginEnter.setGeometry(QtCore.QRect(240, 160, 120, 40))
        self.btnLoginEnter.setMinimumSize(QtCore.QSize(120, 40))
        font = QtGui.QFont()
        font.setFamily("Calibri Light")
        font.setPointSize(10)
        self.btnLoginEnter.setFont(font)
        self.btnLoginEnter.setObjectName("btnLoginEnter")
        self.layoutWidget = QtWidgets.QWidget(LogIn)
        self.layoutWidget.setGeometry(QtCore.QRect(40, 80, 122, 121))
        self.layoutWidget.setObjectName("layoutWidget")
        self.verticalLayout = QtWidgets.QVBoxLayout(self.layoutWidget)
        self.verticalLayout.setContentsMargins(0, 0, 0, 0)
        self.verticalLayout.setObjectName("verticalLayout")
        self.rbLoginSelZb = QtWidgets.QRadioButton(self.layoutWidget)
        self.rbLoginSelZb.setMinimumSize(QtCore.QSize(120, 30))
        self.rbLoginSelZb.setStyleSheet("font: 25 10pt \"Calibri Light\";")
        self.rbLoginSelZb.setObjectName("rbLoginSelZb")
        self.buttonGroup = QtWidgets.QButtonGroup(LogIn)
        self.buttonGroup.setObjectName("buttonGroup")
        self.buttonGroup.addButton(self.rbLoginSelZb)
        self.verticalLayout.addWidget(self.rbLoginSelZb)
        self.rbLoginSelBlm = QtWidgets.QRadioButton(self.layoutWidget)
        self.rbLoginSelBlm.setMinimumSize(QtCore.QSize(120, 30))
        self.rbLoginSelBlm.setStyleSheet("font: 25 10pt \"Calibri Light\";")
        self.rbLoginSelBlm.setObjectName("rbLoginSelBlm")
        self.buttonGroup.addButton(self.rbLoginSelBlm)
        self.verticalLayout.addWidget(self.rbLoginSelBlm)
        self.rbLoginSelOpth = QtWidgets.QRadioButton(self.layoutWidget)
        self.rbLoginSelOpth.setEnabled(False)
        self.rbLoginSelOpth.setMinimumSize(QtCore.QSize(120, 30))
        self.rbLoginSelOpth.setStyleSheet("font: 25 10pt \"Calibri Light\";")
        self.rbLoginSelOpth.setObjectName("rbLoginSelOpth")
        self.buttonGroup.addButton(self.rbLoginSelOpth)
        self.verticalLayout.addWidget(self.rbLoginSelOpth)
        self.lblLoginUserName = QtWidgets.QLabel(LogIn)
        self.lblLoginUserName.setGeometry(QtCore.QRect(260, 250, 120, 30))
        self.lblLoginUserName.setMinimumSize(QtCore.QSize(100, 30))
        font = QtGui.QFont()
        font.setFamily("Calibri Light")
        font.setPointSize(10)
        self.lblLoginUserName.setFont(font)
        self.lblLoginUserName.setLayoutDirection(QtCore.Qt.LeftToRight)
        self.lblLoginUserName.setAlignment(QtCore.Qt.AlignRight|QtCore.Qt.AlignTrailing|QtCore.Qt.AlignVCenter)
        self.lblLoginUserName.setObjectName("lblLoginUserName")

        self.retranslateUi(LogIn)
        QtCore.QMetaObject.connectSlotsByName(LogIn)

    def retranslateUi(self, LogIn):
        _translate = QtCore.QCoreApplication.translate
        LogIn.setWindowTitle(_translate("LogIn", "Dialog"))
        self.lblLoginChooseMode.setText(_translate("LogIn", "Choose Mode:"))
        self.btnLoginEnter.setText(_translate("LogIn", "OK"))
        self.rbLoginSelZb.setText(_translate("LogIn", "zigbee"))
        self.rbLoginSelBlm.setText(_translate("LogIn", "ble mesh"))
        self.rbLoginSelOpth.setText(_translate("LogIn", "thread"))
        self.lblLoginUserName.setText(_translate("LogIn", "xxx"))

