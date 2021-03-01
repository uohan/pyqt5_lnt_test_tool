# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'dev_log.ui'
#
# Created by: PyQt5 UI code generator 5.11.3
#
# WARNING! All changes made in this file will be lost!

from PyQt5 import QtCore, QtGui, QtWidgets

class Ui_VersionUpdate(object):
    def setupUi(self, VersionUpdate):
        VersionUpdate.setObjectName("VersionUpdate")
        VersionUpdate.resize(482, 450)
        VersionUpdate.setMinimumSize(QtCore.QSize(480, 450))
        self.labelVersion = QtWidgets.QLabel(VersionUpdate)
        self.labelVersion.setGeometry(QtCore.QRect(30, 50, 111, 41))
        self.labelVersion.setStyleSheet("font: 75 8pt \"Calibri Light\";\n"
"font: 14pt \"MS Shell Dlg 2\";")
        self.labelVersion.setObjectName("labelVersion")
        self.labelUpdateFeature = QtWidgets.QLabel(VersionUpdate)
        self.labelUpdateFeature.setGeometry(QtCore.QRect(30, 110, 331, 101))
        self.labelUpdateFeature.setStyleSheet("font: 25 12pt \"Calibri Light\";")
        self.labelUpdateFeature.setObjectName("labelUpdateFeature")

        self.retranslateUi(VersionUpdate)
        QtCore.QMetaObject.connectSlotsByName(VersionUpdate)

    def retranslateUi(self, VersionUpdate):
        _translate = QtCore.QCoreApplication.translate
        VersionUpdate.setWindowTitle(_translate("VersionUpdate", "Dialog"))
        self.labelVersion.setText(_translate("VersionUpdate", "xxx"))
        self.labelUpdateFeature.setText(_translate("VersionUpdate", "xxx"))

