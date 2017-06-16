import QtQuick 2.4
import QtQuick.Controls 1.4
import QtQuick.Dialogs 1.2
import QtQuick.Layouts 1.1

import "."

import "md5.js" as MD5

Item {
    id: root
    property string text
    property string property
    property var experimentData
    property color readyColor: "#121212"
    property color waitingColor: "#979797"
    property color inputColor: readyColor
    property var experimentItem
    property bool readOnly: false
    property var comboModel: []
    property var model: {
        var result = []
        if(!experimentData) {
            return []
        }

        var currentValue = experimentData[root.property]
        if(typeof(currentValue) !== "object") {
            return []
        }
        for(var i in currentValue) {
            result.push({key: i, value: currentValue[i]})
        }
        return result
    }

    height: row.height
    width: row.width

    function reset() {
        root.readOnly = false
        root.inputColor = root.readyColor
    }

    MouseArea {
        id: mouseArea
        anchors.fill: parent
        hoverEnabled: true
        propagateComposedEvents: true
        acceptedButtons: Qt.NoButton

        Row {
            id: row
            spacing: 8
            Text {
                width: 200
                color: "#434343"
                horizontalAlignment: Label.AlignRight
                text: root.text + ":"
            }
            Column {
                Repeater {
                    model: root.model
                    Item {
                        property var backendText: modelData.value
                        property bool hasChanges: backendText !== textInput.text

                        function putChanges(callback) {
                            if(!hasChanges) {
                                console.log("No change, returning")
                                if(callback) {
                                    callback()
                                }
                                return
                            }
                            var name = experimentData.__path + "/" + root.property
                            var targetProperty = root.property
                            var oldName = name + "/" + modelData.key
                            var newData = {}
                            newData[modelData.key] = textInput.text
                            console.log("Changing", oldName, JSON.stringify(newData))
                            Firebase.patch(name, newData, function(req2) {
                                console.log("Put result:", req2.status, req2.responseText)
                            })
                            Firebase.remove(oldName, function(req) {
                                console.log("Remove result:", req.responseText)
                            })
                        }
                        width: itemRow.width
                        height: itemRow.height
                        MouseArea {
                            id: itemMouseArea
                            anchors.fill: parent
                            acceptedButtons: Qt.NoButton
                            hoverEnabled: true
                            Row {
                                id: itemRow

                                spacing: 8

                                TextInput {
                                    id: textInput
                                    selectByMouse: true
                                    text: backendText
                                    horizontalAlignment: Label.AlignLeft
                                    color: root.inputColor

                                    onEditingFinished: {
                                        putChanges(root.reset)
                                    }
                                }

                                Text {
                                    text: "x"
                                    color: "red"
                                    opacity: itemMouseArea.containsMouse
                                    MouseArea {
                                        anchors.fill: parent
                                        onClicked: {
                                            var name = experimentData.__path + "/" + root.property
                                            var oldName = name + "/" + modelData.key
                                            Firebase.remove(oldName, function(req) {
                                                console.log("Remove result", req.responseText)
                                            })
                                            Firebase.get(name, function(req1) {
                                              console.log("RESPONSE", req1.responseText)
                                              var data = JSON.parse(req1.responseText)
                                              var newData = []
                                              for(var i = 0; i < data.length; i++) {
                                                  if(data[i] !== null) {
                                                      newData.push(data[i])
                                                  }
                                              }
                                              Firebase.put(name, newData, function(req2) {
                                                  console.log("Put result:", req2.status, req2.responseText)
                                              })
                                           })
                                        }
                                    }
                                }
                            }
                        }
                    }
                }
                // TODO refresh view after adding new row
                Row {
                    id: newRow
                    visible: false
                    TextInput {
                        id: newInput
                        selectByMouse: true
                        text: ""
                        onEditingFinished: {
                            if(newInput.text === "") {
                                newRow.visible = false
                                return
                            }

                            var name = experimentData.__path + "/" + root.property
                            var newData = {}
                            var index = root.model.length
                            newData[index] = newInput.text
                            Firebase.patch(name, newData, function(req2) {
                                console.log("Put result:", req2.status, req2.responseText)
                                root.reset()
                                newInput.text = ""
                            })
                            newRow.visible = false
                            root.readOnly = true
                            root.inputColor = root.waitingColor
                        }
                    }
                    Text {
                        color: "#979797"
                        text: "Enter new value"
                        visible: newInput.text == ""
                    }
                }
                Text {
                    id: addButton
                    color: "green"
                    opacity: mouseArea.containsMouse
                    text: "+"
                    MouseArea {
                        anchors.fill: parent
                        onClicked: {
                            newRow.visible = true
                            newInput.forceActiveFocus()
                        }
                    }
                }
            }
        }
    }
}
