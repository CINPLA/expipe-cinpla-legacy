import QtQuick 2.4
import QtQuick.Controls 1.4
import QtQuick.Dialogs 1.2
import QtQuick.Layouts 1.1
import Qt.labs.settings 1.0

import "md5.js" as MD5
import "." // qmldir for Style

Item {
    id: root
    property string identiconProvider
    property string project
    property var action

    function robohash(name, size, set, bgset) {
        if(size === undefined) {
            size = 32
        }
        if(set === undefined) {
            set = "set1"
        }
        if(bgset === undefined) {
            bgset = "bg1"
        }
        size = parseInt(size)
        return "https://robohash.org/" + name + ".png?bgset=" + bgset + "&set=" + set + "&size=" + size + "x" + size
    }

    function gravatar(name, size) {
        if(size === undefined) {
            size = 32
        }
        size = parseInt(size)
        return "http://gravatar.com/avatar/" + MD5.md5(name) + "?s=" + size + "&d=identicon&r=PG"
    }

    function dreamhash(name, size, set) {
        if(size === undefined) {
            size = 32
        }
        if(set === undefined) {
            set = 45
        } else {
            set = parseInt(set)
        }
        return "http://95.85.59.61:8080/" + name + "?size=" + size
    }

    function common(name, size, set, bgset) {
        switch(Style.identiconProvider) {
        case "gravatar":
            return gravatar(name, size)
        case "robohash":
            return robohash(name, size, set, bgset)
        case "dreamhash":
            return dreamhash(name, size, set)
        default:
            return gravatar(name, size)
        }
    }

    Rectangle {
        anchors.fill: parent
        color: "#dedede"
        visible: image.status != Image.Ready
    }

    Text {
        id: text
        anchors.centerIn: parent
        text: "..."
        visible: image.status != Image.Ready

        NumberAnimation {
            target: text
            loops: Animation.Infinite
            property: "rotation"
            running: image.status != Image.Ready
            from: 0
            to: 359
            duration: 4000
            easing.type: Easing.InOutQuad
        }
    }

    Image {
        id: image
        anchors.fill: parent
        antialiasing: true
        smooth: true
        source: {
            if(project !== "") {
                return common(project, width, "set2", "bg1")
            } else if(action && action["__key"]) {
                return common(action["__key"], width)
            } else {
                return common("undefined", width)
            }
        }
    }
}
