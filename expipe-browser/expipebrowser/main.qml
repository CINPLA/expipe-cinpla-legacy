import QtQuick 2.4
import QtQuick.Controls 1.4
import QtQuick.Dialogs 1.2
import QtQuick.Layouts 1.1
import Qt.labs.settings 1.0

ApplicationWindow {
    id: root

    visible: true
    width: 1440
    height: 1024
    title: qsTr("Expipe Browser")

    property bool hasToken: false
    property var xhr

    onHasTokenChanged: {
        if(hasToken) {
            projectsView.retryConnection()
        }
    }

    Settings {
        property alias width: root.width
        property alias height: root.height
    }

    Item {
        anchors.fill: parent
        MouseArea {
            anchors.fill: parent
            onClicked: {
                parent.forceActiveFocus()
            }
        }
    }

    LeftMenu {
        id: leftMenu
        anchors {
            left: parent.left
            top: parent.top
            bottom: parent.bottom
        }

        width: 240
        currentProject: projectsView.currentProject
    }

    Item {
        id: viewArea
        anchors {
            left: leftMenu.right
            top: parent.top
            bottom: parent.bottom
            right: parent.right
        }
    }

    ProjectsView {
        id: projectsView
        anchors.fill: viewArea
        visible: leftMenu.selectedState === "projects"
    }

    ExperimentsView {
        id: experimentsView
        anchors.fill: viewArea
        visible: leftMenu.selectedState === "actions"
        currentProject: projectsView.currentProject
    }

    TemplatesView {
        id: templatesView
        anchors.fill: viewArea
        visible: leftMenu.selectedState === "templates"
    }

    SettingsView {
        anchors.fill: viewArea
        visible: leftMenu.selectedState === "settings"
    }
}
