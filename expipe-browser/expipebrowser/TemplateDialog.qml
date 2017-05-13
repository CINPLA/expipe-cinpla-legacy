import QtQuick 2.4
import QtQuick.Controls 1.4 as QQC1
import QtQuick.Controls 1.4
import QtQuick.Dialogs 1.2
import QtQuick.Layouts 1.1

import ExpipeBrowser 1.0

import "."

import "md5.js" as MD5
import "dicthelper.js" as DictHelper

Dialog {
    id: newModuleDialog
    property string modulesPath
    standardButtons: Dialog.Ok | Dialog.Cancel
    Column {
        id: newModuleColumn
        spacing: 8
        anchors {
            left: parent.left
            right: parent.right
        }

        Label {
            anchors {
                left: parent.left
                right: parent.right
            }
            wrapMode: Text.WrapAtWordBoundaryOrAnywhere
            font.pixelSize: 18
            text: "New module"
        }

        Label {
            anchors {
                left: parent.left
                right: parent.right
            }
            wrapMode: Text.WrapAtWordBoundaryOrAnywhere
            text: "Template:"
        }
        
        EventSource {
            id: templateEventSource
            path: "templates"
        }
        
        // TODO resize based on dialog size using Layouts
        QQC1.ScrollView {
            anchors {
                left: parent.left
                right: parent.right
            }
            height: 160
            ListView {
                id: templateSelector
                anchors.fill: parent
                model: templateEventSource
                highlightMoveDuration: 0
                highlight: Rectangle {
                    color: "black"
                    opacity: 0.1
                }
                delegate: Item {
                    readonly property var modelData: model
                    anchors {
                        left: parent.left
                        right: parent.right
                    }
                    height: 32
                    Text {
                        anchors {
                            fill: parent
                            margins: 8
                        }
                        fontSizeMode: Text.Fit
                        text: key
                    }
                    MouseArea {
                        anchors.fill: parent
                        onClicked: {
                            templateSelector.currentIndex = index
                        }
                    }
                }
            }
        }

        Label {
            anchors {
                left: parent.left
                right: parent.right
            }
            wrapMode: Text.WrapAtWordBoundaryOrAnywhere
            text: "Name: "
        }

        TextField {
            id: nameField
            anchors {
                left: parent.left
                right: parent.right
            }
            text: templateSelector.currentItem.modelData.key
            // wrapMode: Text.WrapAtWordBoundaryOrAnywhere
        }

        Label {
            anchors {
                left: parent.left
                right: parent.right
            }
            color: "#ababab"
            wrapMode: Text.WrapAtWordBoundaryOrAnywhere
            text: "(Permanent: Cannot be changed)"
        }
    }
    onAccepted: {
        if(!modulesPath) {
            console.log("ERROR: modulesPath not set on TemplateDialog.")
            return
        }
        var selection = templateSelector.currentItem.modelData
        var name = nameField.text
        Firebase.get("templates_contents/" + selection.key + "/", function(req) {
            console.log("RESPONSE", req.responseText)
            var data = JSON.parse(req.responseText)
            if(!data || !name) {
                console.log("ERROR: Missing name or value")
                return
            }
            var target = modulesPath + "/" + name
            var targetProperty = root.property
            Firebase.put(target, data, function(req) {
                console.log("Add module result:", req.status, req.responseText)
                templateSelector.currentIndex = 0
            })
        })
    }
}
