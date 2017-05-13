import QtQuick 2.4
import QtQuick.Controls 1.4
import QtQuick.Dialogs 1.2
import QtQuick.Layouts 1.1

import ExpipeBrowser 1.0

import "."

import "md5.js" as MD5
import "dicthelper.js" as DictHelper

Item {
    id: root

    property string currentProject

    ExperimentList {
        id: experimentList
        anchors {
            left: parent.left
            top: parent.top
            bottom: parent.bottom
        }
        width: 640
        currentProject: root.currentProject
    }

    Component {
        id: experimentComponent
        Experiment {
            currentProject: root.currentProject
            experimentData: experimentList.currentData
        }
    }

    Loader {
        id: experimentLoader
        anchors {
            left: experimentList.right
            right: parent.right
            top: parent.top
            bottom: parent.bottom
        }
        sourceComponent: experimentList.currentData ? experimentComponent : undefined
    }
}
