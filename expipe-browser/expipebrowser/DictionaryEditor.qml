import QtQuick 2.5
import QtQuick.Controls 1.4
import QtQuick.Layouts 1.0
import Qt.labs.settings 1.0

import "."

Item {
    id: column
    signal refreshParent()
    property string basePath
    property var contents: []
    property var contentsModel: []
    property var path: []
    property alias repeater: repeater
    property int level: 0
    property var object
    property var parentObject
    property bool isLastItem: true
    property bool expanded: false
    property bool isRoot: true
    property bool hasChanges: textField.text !== backendText
    property bool isObject: type === "object"
    property color readyColor: "#121212"
    property color waitingColor: "#979797"
    property var parentEditor
    property bool containsMouse: elementArea.containsMouse
    property bool parentContainsMouse: parentEditor !== undefined && parentEditor.containsMouse

    property string backendText: {
        if(type === "null") {
            return ""
        }
        if(type === "string") {
            return '"' + value.replace('"', '\\"') + '"'
        }
        if(type === "number") {
            return value
        }
        if(value === undefined) {
            return "undefined"
        }
        return value.toString()
    }

    property string key: {
        if(path.length === 0) {
            return ""
        }
        return path[path.length - 1]
    }

    property string keyString: {
        if(path.length === 0) {
            return "root"
        }
        return key
    }

    property var value: {
        if(object === undefined) {
            return null
        }
        return object
    }

    property string type: {
        if(value === null) {
            return "null"
        }
        return typeof(value)
    }
    function refresh() {
        updateObject()
        updateModel()
    }

    function refreshPath(pathSplit) {
        console.log("Requested refresh on", pathSplit)
        if(pathSplit.length === 0) {
            console.log("Updating on", path, key)
            refresh()
            return
        }
        var nextKey = pathSplit.shift() // first item is removed
        for(var i in contentsModel) {
            if(contentsModel[i].key === nextKey) {
                console.log("Passing on to", nextKey)
                updateObject()
                var nextObject = object[nextKey]
                if(nextObject === undefined || nextObject === null) {
                    refresh()
                    return
                } else {
                    var subEditor = repeater.itemAt(i).editor
                    subEditor.refreshPath(pathSplit)
                    return
                }
            }
        }
        console.log("Path not found, refresh ourselves", path, key)
        refresh()
    }

    function updateObject() {
        var self = contents
        var parent = null
        for(var i in path) {
            var subPath = path[i]
            parent = self
            self = self[subPath]
        }
        object = self
        parentObject = parent
        textField.reset()
    }

    function createModel() {
        var model = []
        if(!isObject) {
            return model
        }
        for(var i in object) {
            model.push({"key": i, "value": object[i]})
        }
        return model
    }

    function updateModel() {
        contentsModel = createModel()
    }

    function isNumeric(num) {
        return !isNaN(num)
    }

    function parseInput(input) {
        console.log("Input", input)
        if(input === "") {
            console.log("Empty string")
            return null
        }
        try {
            var obj = JSON.parse(input)
            console.log("Parsed!", JSON.stringify(obj))
            return obj
        } catch (e) {
            console.log("Failed parse", e)
        }

        var output = input
        if(isNumeric(input)) {
            output = parseFloat(input)
            console.log("Is numeric", output)
        } else {
            output = input.replace('\\"', '"')
            console.log("Is string", output)
            if(output[0] === '"' && output[output.length - 1] === '"') {
                output = output.substring(1, output.length - 1)
                console.log("substring", output)
            }
        }
        return output
    }

    function putChanges(callback) {
        if(!hasChanges) {
            console.log("No change, returning")
            return
        }
        var name = basePath + "/" + path.join("/")
        var data = parseInput(textField.text)
        Firebase.put(name, data, function(req) {
            console.log("Put result:", req.status, req.responseText)
            textField.text = Qt.binding(function() {return backendText})
            textField.readOnly = false
            textField.color = column.readyColor
            if(callback) {
                callback()
            }
        })
        textField.readOnly = true
        textField.color = column.waitingColor
    }

    function remove() {
        var name = basePath + "/" + path.join("/")
        console.log("Removing", name)
        Firebase.remove(name, function(req) {
            console.log("Remove result", req.responseText)
        })
    }

    function createNew() {
        console.log("Creating new")
        var name = basePath + "/" + path.join("/") + "/" + encodeURIComponent(nameInput.text)
        var data = parseInput(valueInput.text)
        Firebase.put(name, data, function(req) {
            console.log("Put new result:", req.status, req.responseText)
        })
        nameInput.text = ""
        valueInput.text = ""
        newRow.visible = false
    }

    onContentsChanged: {
        for(var i = 0; i < repeater.count; i++) {
            var subEditor = repeater.itemAt(i).editor
            subEditor.contents = contents
        }
    }

    Component.onCompleted: {
        refresh()
    }
    width: theColumn.width
    height: theColumn.height

    Column {
        id: theColumn
        Item {
            width: elementRow.width
            height: 33

            MouseArea {
                id: elementArea
                anchors.fill: parent

                hoverEnabled: true
                acceptedButtons: Qt.NoButton
                Row {
                    id: elementRow
                    spacing: 4
                    height: 33

                    Item {
                        width: 33
                        height: 33
                        clip: true
                        Image {
                            source: "grid.png"
                            x: -33 * 3
                            y: parentContainsMouse ? -33 : 0
                            visible: !column.isLastItem && parentContainsMouse
                        }
                        Image {
                            source: "grid.png"
                            x: {
                                if(column.isObject) {
                                    return column.expanded ? 0 : -33
                                } else {
                                    return -33 * 2
                                }
                            }
                            y: parentContainsMouse ? -33 : 0
                        }
                        MouseArea {
                            anchors.fill: parent
                            onClicked: column.expanded = !column.expanded
                        }
                    }

                    Text {
                        anchors {
                            verticalCenter: parent.verticalCenter
                        }
                        text: column.keyString + (isObject ? "" : ":")
                        color: "#434343"
                    }

                    Rectangle {
                        id: rect
                        property bool show: mouseArea.containsMouse || textField.activeFocus
                        anchors {
                            verticalCenter: parent.verticalCenter
                        }
                        visible: !column.isObject
                        width: textField.width + 16
                        height: textField.height + 8
                        color: show ? "white" : "transparent"
                        border {
                            color: show ? "black" : "transparent"
                            width: 1
                        }

                        MouseArea {
                            id: mouseArea
                            anchors.fill: textField
                            hoverEnabled: true
                            cursorShape: Qt.IBeamCursor
                            acceptedButtons: Qt.NoButton
                        }

                        TextInput {
                            id: textField

                            anchors.centerIn: parent
                            selectByMouse: true
                            width: Math.max(64, contentWidth)

                            color: "#121212"
                            text: backendText

                            onEditingFinished: {
                                putChanges()
                            }

                            function reset() {
                                text = Qt.binding(function() {return backendText})
                            }

                            Keys.onReturnPressed: {
                                focus = false
                            }

                            Keys.onEscapePressed: {
                                reset()
                                focus = false
                            }
                        }
                    }
                    MouseArea {
                        anchors.verticalCenter: parent.verticalCenter
                        width: plus.width + 4
                        height: plus.height + 4
                        visible: column.isObject

                        onClicked: {
                            newRow.visible = true
                        }

                        Text {
                            id: plus
                            anchors.centerIn: parent
                            color: "green"
                            visible: elementArea.containsMouse
                            text: "+"
                        }
                    }
                    MouseArea {
                        anchors.verticalCenter: parent.verticalCenter
                        width: minus.width + 4
                        height: minus.height + 4

                        onClicked: {
                            remove()
                        }

                        Text {
                            id: minus
                            anchors.centerIn: parent
                            color: "red"
                            text: "x"
                            visible: elementArea.containsMouse
                        }
                    }
                }
            }
        }

        Row {
            visible: column.expanded
            Item {
                width: 33
                height: col.height
                clip: true
                Image {
                    visible: !column.isLastItem && parentContainsMouse
                    x: -33 * 3
                    height: parent.height
                    fillMode: Image.TileVertically
                    source: "grid.png"
                }
            }

            Column {
                id: col

                Repeater {
                    id: repeater

                    model: column.contentsModel

                    delegate: Item {
                        property var editor: loader.item
                        width: loader.width
                        height: loader.height

                        Loader {
                            id: loader

                            Connections {
                                target: column
                                onExpandedChanged: {
                                    if(column.expanded) {
                                        var subPath = column.path.slice()
                                        subPath.push(modelData.key)
                                        loader.setSource("DictionaryEditor.qml", {
                                                      parentEditor: column,
                                                      contents: column.contents,
                                                      path: subPath,
                                                      isLastItem: (index === repeater.count - 1),
                                                      isRoot: false,
                                                      basePath: column.basePath
                                                  })
                                      }
                                  }
                            }

                            Connections {
                                target: loader.item
                                onRefreshParent: {
                                    //                                column.refresh()
                                }
                            }
                        }
                    }
                }
            }
        }

        Row {
            id: newRow
            visible: false

            x: 33 * 2

            Text {
                anchors {
                    verticalCenter: parent.verticalCenter
                }
                color: "#434343"
                text: "Name:"
            }

            Rectangle {
                anchors.verticalCenter: parent.verticalCenter
                width: nameInput.width + 16
                height: nameInput.height + 8
                TextInput {
                    id: nameInput
                    selectByMouse: true
                    width: 100
                    anchors.centerIn: parent
                    clip: true

                    MouseArea {
                        anchors.fill: parent
                        acceptedButtons: Qt.NoButton
                        hoverEnabled: true
                        cursorShape: Qt.IBeamCursor
                    }
                }
                Text {
                    anchors.fill: nameInput
                    text: "a good name"
                    color: "#999"
                    visible: !nameInput.text
                }
            }

            Text {
                anchors {
                    verticalCenter: parent.verticalCenter
                }
                font.weight: Font.Bold
                color: "#121212"
                text: "Value:"
            }

            Rectangle {
                anchors.verticalCenter: parent.verticalCenter
                width: valueInput.width + 16
                height: valueInput.height + 8
                TextInput {
                    id: valueInput
                    width: 160
                    clip: true
                    selectByMouse: true 
                    anchors.centerIn: parent
                    MouseArea {
                        anchors.fill: parent
                        acceptedButtons: Qt.NoButton
                        hoverEnabled: true
                        cursorShape: Qt.IBeamCursor
                    }
                }
                Text {
                    anchors.fill: valueInput
                    text: "with a fine value"
                    color: "#999"
                    visible: !valueInput.text
                }
                Keys.onReturnPressed: {
                    createNew()
                }
            }

            //        ComboBox {
            //            id: templateSelector
            //            textRole: "key"
            //            model: ListModel {
            //                ListElement { key: "Templates"; inactive: true }
            //                ListElement { key: "Tracking"; value: '{"box_size": null, "wireless": false, "camera": null, "ttl_channel": null}' }
            //                ListElement { key: "Grating"; value: '{"directions": null, "duration": false, "distance": null}' }
            //            }
            //            onActivated: {
            //                if(!model.get(index).value) {
            //                    valueInput.text = ""
            //                }
            //                valueInput.text = model.get(index).value
            //            }
            //        }

            Button {
                text: "OK"
                onClicked: {
                    createNew()
                }
            }

            Button {
                text: "Cancel"
                onClicked: {
                    newRow.visible = false
                }
            }
        }
    }

}
