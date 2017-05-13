import ctypes
from ctypes.util import find_library

# OpenGL fix (must be set before other imports)
libGL = find_library("GL")
ctypes.CDLL(libGL, ctypes.RTLD_GLOBAL)

from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
from PyQt5.QtQml import *
import sys

class TreeModel(QAbstractItemModel):
    def index(self, row, column, parent):
        return self.createIndex(row, column, 0)

if __name__ == "__main__":
    qmlRegisterType(TreeModel, "TreeModel", 1, 0, "TreeModel")

    app = QApplication(sys.argv)

    engine = QQmlApplicationEngine()
    component = QQmlComponent(engine)
    component.setData(b"""
import QtQuick 2.4
import QtQuick.Controls 1.4
import TreeModel 1.0

ApplicationWindow {
    width: 1280
    height: 900
    visible: true
    
    TreeModel {
        id: treeModel
        Component.onCompleted: {
            var i = index(0, 0, 0)
            console.log("Index model", i.model)
            console.log("Real model", treeModel)
        }
    }
}
""", QUrl("test"))
    window = component.create()
    window.show()
    # engine.load(QUrl("qml/main.qml"))

    app.exec_()
