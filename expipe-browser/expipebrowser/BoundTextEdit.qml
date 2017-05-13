import QtQuick 2.4
import QtQuick.Controls 1.4
import QtQuick.Dialogs 1.2
import QtQuick.Layouts 1.1

import ExpipeBrowser 1.0

import "."

import "dicthelper.js" as DictHelper

Rectangle {
    id: root
    readonly property bool valid: root.property && root.contents
    property var contents
    property string property
    property string path: root.valid ? contents.__path : ""
    property bool show: mouseArea.containsMouse || textField.activeFocus
    property color readyColor: "#121212"
    property color waitingColor: "#979797"
    property bool waiting: false
    baselineOffset: textField.y + textField.baselineOffset
    width: textField.width + 16
    height: textField.height + 8
    color: show ? "white" : "transparent"
    border {
        color: show ? "black" : "transparent"
        width: 1
    }
    
    Rectangle {
        id: background
        anchors.fill: parent
        color: "green"
        opacity: 0
        
        NumberAnimation {
            id: backgroundAnimation
            target: background
            property: "opacity"
            duration: 1000
            easing.type: Easing.InOutQuad
            from: 0.2
            to: 0
        }
    }
    
    MouseArea {
        id: mouseArea
        anchors.fill: textField
        propagateComposedEvents: true
        hoverEnabled: true
        cursorShape: Qt.IBeamCursor
        acceptedButtons: Qt.NoButton
    }
    
    TextInput {
        id: textField
        
        anchors {
            left: parent.left
            verticalCenter: parent.verticalCenter
            margins: 8
        }
        
        color: waiting ? waitingColor : readyColor
        readOnly: waiting ? true : false
        width: Math.max(64, contentWidth)
        
        onEditingFinished: {
            if(!valid) {
                return
            }
            if(textField.text === contents[root.property]) {
                return
            }
            var data = {}
            data[root.property] = textField.text
            Firebase.patch(path, data, function(req) {
                console.log("Updated", path, root.property, req.statusText, req.responseText)
                backgroundAnimation.restart()
                waiting = false
            })
            waiting = true
        }
        
        Keys.onReturnPressed: {
            focus = false
        }
        
        Keys.onEscapePressed: {
            textField.text = contents[root.property]
            focus = false
        }
        
        Binding {
            target: textField
            property: "text"
            value: root.valid ? contents[root.property] : undefined
            when: root.valid
        }
    }
}
