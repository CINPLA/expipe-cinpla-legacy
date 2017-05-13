import QtQuick 2.4
import QtQuick.Controls 1.4
import QtQuick.Dialogs 1.2
import QtQuick.Layouts 1.1

import ExpipeBrowser 1.0

import "."

import "dicthelper.js" as DictHelper

Item {
    id: root

    readonly property string currentProject: listView.currentIndex > -1 ? listView.currentItem.key : ""
    property var projectsModel: []
    property var projects: {
        return {}
    }

    function refreshModules(path) {
        if(path.length < 1) {
            return
        }
        for(var i = 0; i < moduleView.count; i++) {
            var dictEditor = moduleView.itemAt(i)
            if(dictEditor.key === path[0]) {
                dictEditor.refreshPath(path)
            }
        }
    }

    function updateModel() {
        // TODO update surgically
        var newModel = []
        for(var id in projects) {
            newModel.push({id: id, data: data})
        }
        projectsModel = newModel
    }

    EventSource {
        id: eventSource
        path: "projects"
        includeHelpers: true
    }

    Rectangle {
        id: stuff
        anchors {
            left: parent.left
            right: parent.right
            top: parent.top
        }
        height: 36
        color: "#cecece"

        Text {
            anchors {
                verticalCenter: parent.verticalCenter
                left: parent.left
                leftMargin: 20
            }
            text: projectsModel.length + " projects"
            color: "#787878"
            font.pixelSize: 14
        }
    }

    Rectangle {
        id: projectList
        anchors {
            left: parent.left
            top: stuff.bottom
            bottom: parent.bottom
        }
        width: 400

        color: "#efefef"
        border {
            color: "#dedede"
            width: 1
        }

        ListView {
            id: listView
            anchors {
                top: parent.top
                bottom: parent.bottom
                right: parent.right
                left: parent.left
            }
            // ScrollBar.vertical: ScrollBar {}
            model: eventSource
            delegate: Item {
                readonly property var key: model.key
                readonly property var contents: model.contents
                anchors {
                    left: parent.left
                    right: parent.right
                }
                height: 64

                Row {
                    anchors {
                        margins: 12
                        left: parent.left
                        right: parent.right
                        top: parent.top
                        bottom: parent.bottom
                    }
                    spacing: 10
                    Identicon {
                        width: height
                        height: parent.height
                        project: key
                    }
                    Text {
                        color: "#121212"
                        text: key
//                        font.pixelSize: 14
                    }
                    Text {
                        color: "#121212"
                        text: contents.registered ? contents.registered : ".."
//                        font.pixelSize: 14
                    }
                    Text {
                        color: "#121212"
                        text: contents.start_date ? contents.start_date : ".."
//                        font.pixelSize: 14
                    }
                }
                MouseArea {
                    anchors.fill: parent
                    onClicked: {
                        listView.currentIndex = index
                    }
                }
            }
            highlightMoveDuration: 400
            highlight: Rectangle {
                color: "black"
                opacity: 0.1
            }
            clip: true
        }

        Button {
            anchors {
                right: parent.right
                bottom: parent.bottom
                margins: 32
            }
            // highlighted: true
            text: "Create new"
            onClicked: {
                newDialog.open()
            }
        }
    }

    Dialog {
        id: newDialog
        title: "Create new project"
        Column {
            spacing: 8
            Label {
                text: "Provide an unique ID for your project.\n" +
                      "This is permanent and cannot be changed later."
            }
            TextField {
                id: newName
            }
            Label {
                text: "Examples: 'mikkel_opto', 'perineural_v2_elimination'"
            }
        }
        standardButtons: Dialog.Cancel | Dialog.Ok
        onAccepted: {
            if(!newName.text) {
                console.log("ERROR: Name cannot be empty.")
                return
            }
            var registered = (new Date()).toISOString()
            var project = {
                registered: registered
            }
            Firebase.put("projects/" + newName.text, project, function(req) {
                console.log("Project created", req.responseText, req.statusText)
            })
        }
    }

    Rectangle {
        id: projectView
        anchors {
            left: projectList.right
            right: parent.right
            top: parent.top
            bottom: parent.bottom
        }
        color: "#fdfdfd"

        EventSource {
            id: moduleEventSource
            path: currentProject ? "project_modules/" + currentProject : ""

            onPutReceived: {
                refreshModules(path)
            }
            onPatchReceived: {
                refreshModules(path)
            }
        }

        Column {
            anchors {
                left: parent.left
                right: parent.right
            }

            Label {
                anchors {
                    left: parent.left
                    margins: 96
                }
                font.pixelSize: 24
                font.weight: Font.Light
                text: currentProject
            }

            RowLayout {
                anchors {
                    left: parent.left
                    right: parent.right
                    leftMargin: 100
                    rightMargin: 48
                }

                Label {
                    id: modulesTitle
                    font.pixelSize: 24
                    font.weight: Font.Light
                    color: "#434343"
                    horizontalAlignment: Text.AlignRight
                    text: "Modules"
                }

                Item {
                    Layout.fillWidth: true
                    Layout.fillHeight: true
                }

                Button {
                    id: addModuleButton
                    text: "Add module"
                    onClicked: {
                        newModuleDialog.open()
                    }
                }

                Button {
                    text: "Delete project"
                    onClicked: {
                        deleteDialog.open()
                    }
                }

            }

            Dialog {
                id: deleteDialog
                title: "Are you sure?"
                standardButtons: Dialog.Cancel | Dialog.Ok
                onAccepted: {
                    Firebase.remove("projects/" + currentProject, function(reply) {
                        console.log("Removed project and got reply", reply.responseText)
                    })
                    Firebase.remove("project_modules/" + currentProject, function(reply) {
                        console.log("Removed project modules and got reply", reply.responseText)
                    })
                }
            }

            Label {
                id: modulesLoadingText
                x: 100
                visible: moduleEventSource.status != EventSource.Connected
                color: "#ababab"
                text: {
                    switch(moduleEventSource.status) {
                    case EventSource.Connecting:
                        return "Loading..."
                    case EventSource.Disconnected:
                        return "Error loading modules!"
                    }
                    return ""
                }
            }

            Label {
                x: 100
                visible: !modulesLoadingText.visible && moduleView.count < 1
                color: "#ababab"
                text: "No modules"
            }

            TemplateDialog {
                id: newModuleDialog
                modulesPath: "project_modules/" + currentProject
            }

            Repeater {
                id: moduleView
                model: moduleEventSource
                DictionaryEditor {
                    property string key: model.key
                    x: 100
                    keyString: model.key
                    contents: model.contents
                    basePath: "project_modules/" + currentProject + "/" + model.key
                    onContentsChanged: {
                        console.log("Contents changed with length", contents.length)
                    }
                }
            }

        }
    }
}
