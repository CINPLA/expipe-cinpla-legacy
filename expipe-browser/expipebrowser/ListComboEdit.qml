import QtQuick 2.4
import QtQuick.Controls 1.4
import QtQuick.Dialogs 1.2
import QtQuick.Layouts 1.1

import "."

import "md5.js" as MD5

Column {
    id: root
    property string text
    property string property
    property var experimentData
    property color readyColor: "#121212"
    property color waitingColor: "#979797"
    property color inputColor: readyColor
    property var experimentItem
    property bool readOnly: false
    property string path
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
            result.push({key: i})
        }
        return result
    }

    width: 400

    onExperimentDataChanged: {
        console.log("Experiment data changed", JSON.stringify(experimentData[root.property]))
    }

    onPathChanged: {
        resetComboModel()
    }

    Component.onCompleted: {
        resetComboModel()
    }

    function resetComboModel() {
        Firebase.get(path, function(xhr) {
            console.log("Resetting combo model!")
            var data = JSON.parse(xhr.responseText)
            var newModel = []
            for(var i in data) {
                newModel.push(i)
            }
            console.log(JSON.stringify(newModel))
            comboModel = newModel
        })
    }

    function putChanges() {
        console.log("Not implemented!")
    }

    function reset() {
        console.log("Resetting")
        console.log("Experiment data", JSON.stringify(experimentData[root.property]))
        console.log("Model", JSON.stringify(model))
        root.readOnly = false
        root.inputColor = root.readyColor
    }

    Row {
        spacing: 8
        Text {
            font.weight: Font.Bold
            text: root.text + ":"
        }
        Text {
            text: "+"
            color: "green"
            MouseArea {
                anchors.fill: parent
                onClicked: {
                    newRow.visible = true
                    newInput.forceActiveFocus()
                }
            }
        }
    }

//    Row {
//        id: newRow
//        visible: false
//        TextInput {
//            id: newInput
//            text: ""
//            onEditingFinished: {
//                if(newInput.text === "") {
//                    newRow.visible = false
//                    return
//                }

//                var name = "actions/" + experimentData.id + "/" + root.property
//                var newData = {}
//                newData[newInput.text] = true
//                Firebase.patch(name, newData, function(req2) {
//                    console.log("Put result:", req2.status, req2.responseText)
//                    root.reset()
//                    newInput.text = ""
//                })
//                newRow.visible = false
//                root.readOnly = true
//                root.inputColor = root.waitingColor
//            }
//        }
//        Text {
//            color: "#979797"
//            text: "Enter new value"
//            visible: newInput.text == ""
//        }
//    }

    Repeater {
        model: root.model
        Row {
//            property var backendText: modelData.key
//            property bool hasChanges: backendText !== textInput

//            function putChanges(callback) {
//                if(!hasChanges) {
//                    console.log("No change, returning")
//                    if(callback) {
//                        callback()
//                    }
//                    return
//                }
//                var name = "actions/" + experimentData.id + "/" + root.property
//                var targetProperty = root.property
//                var oldName = name + "/" + modelData.key
//                var newData = {}
//                newData[textInput.text] = true
//                Firebase.patch(name, newData, function(req2) {
//                    console.log("Put result:", req2.status, req2.responseText)
//                })
//                Firebase.remove(oldName, function(req) {
//                    console.log("Remove result:", req.responseText)
//                })
//            }

            spacing: 8

            ComboBox {
                id: textInput
                model: root.comboModel
            }

            Text {
                text: "x"
                color: "red"
                MouseArea {
                    anchors.fill: parent
                    onClicked: {
                        var name = "actions/" + experimentData.id + "/" + root.property
                        var oldName = name + "/" + modelData.key
                        Firebase.remove(oldName, function(req) {
                            console.log("Remove result", req.responseText)
                        })
                    }
                }
            }
        }
    }
}
