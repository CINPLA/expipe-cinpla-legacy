import QtQuick 2.4
import QtQuick.Controls 1.4 as QQC1
import QtQuick.Controls 1.4
import QtQuick.Dialogs 1.2
import QtQuick.Layouts 1.1

import ExpipeBrowser 1.0

import "."

import "dicthelper.js" as DictHelper

Item {
    id: root

    property var currentKey: listView.currentItem ? listView.currentItem.key : undefined
    property var currentTemplate: listView.currentItem ? listView.currentItem.contents : undefined

    EventSource {
        id: templatesModel
        path: "templates"
        includeHelpers: true
        shallow: true
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
            text: listView.count + " templates"
            color: "#787878"
            font.pixelSize: 14
        }
    }

    Rectangle {
        id: templateList
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
            model: templatesModel
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
                        text: key ? key : "[unnamed]"
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

    Loader {
        anchors {
            left: templateList.right
            right: parent.right
            top: parent.top
            bottom: parent.bottom
        }
        sourceComponent: currentTemplate ? component : undefined
    }

    Component {
        id: component
        Rectangle {
            id: templateView
            color: "#fdfdfd"
            
            EventSource {
                id: eventSource
                path: "templates_contents/" + currentKey
                onPathChanged: console.log("Path is now", path)
                includeHelpers: false
            }
            
            Label {
                id: title
                anchors {
                    left: parent.left
                    top: parent.top
                    margins: 96
                }
                font.pixelSize: 24
                font.weight: Font.Light
                text: currentKey
            }

            GridLayout {
                anchors {
                    top: title.bottom
                    left: parent.left
                    right: parent.right
                    margins: 48
                }
                columns: 2
                rowSpacing: 8
                columnSpacing: 8

                // -- invisible spacers --

                Item {
                    implicitHeight: 1
                    Layout.minimumWidth: 200
                }

                Item {
                    implicitHeight: 1
                    Layout.fillWidth: true
                }

                // --------- row ---------

                Label {
                    id: identifierLabel
                    Layout.alignment: Qt.AlignRight
                    text: "Default module name:"
                }

                BoundTextEdit {
                    contents: currentTemplate
                    property: "identifier"
                }


                // --------- row ---------

                Label {
                    text: "Contents:"
                    Layout.alignment: Qt.AlignRight
                }

                DictionaryEditor {
                    id: dictionaryEditor
                    
                    visible: eventSource.status == EventSource.Connected
                    
                    Connections {
                        target: eventSource
                        onPutReceived: {
                            dictionaryEditor.refreshPath(path)
                        }
                        onPatchReceived: {
                            dictionaryEditor.refreshPath(path)
                        }
                    }

                    keyString: currentTemplate.identifier
                    contents: eventSource.contents
                    basePath: eventSource.path
                }
            }
        }
    }
    
    Dialog {
        id: newDialog
        title: "Create new template"
        Column {
            spacing: 8
            Label {
                text: "Provide an unique ID for your template."
            }
            TextField {
                id: newName
                selectByMouse: true
            }
            Label {
                text: "Examples: 'eddy_analysis', 'microscope_manufacturer'"
            }
        }
        standardButtons: Dialog.Cancel | Dialog.Ok
        onAccepted: {
            if(!newName.text) {
                console.log("ERROR: Name cannot be empty.")
                return
            }
            var name = newName.text
            var registered = (new Date()).toISOString()
            var experiment = {
                registered: registered,
                identifier: name
            }
            Firebase.put("templates/" + name, experiment, function(req) {
                var createdTemplate = JSON.parse(req.responseText)
                // requestedId = createdTemplate // TODO select new template
            })
        }
    }
}
