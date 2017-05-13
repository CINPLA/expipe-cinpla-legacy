import QtQuick 2.4
import QtQuick.Controls 1.4 as QQC1
import QtQuick.Controls 1.4
import QtQuick.Dialogs 1.2
import QtQuick.Layouts 1.1

import ExpipeBrowser 1.0

import "."

import "md5.js" as MD5
import "dicthelper.js" as DictHelper

Rectangle {
    id: root
    property alias model: listView.model
    property alias currentIndex: listView.currentIndex
    property var experiments: {
        return {}
    }
    property string requestedId
    property string currentProject
    property var currentData
    property bool trigger: false
    property bool bindingEnabled: true

    onCurrentProjectChanged: {
        experiments = {}
    }

    color: "#efefef"
    border {
        color: "#dedede"
        width: 1
    }

    Binding {
        target: root
        property: "currentData"
        when: bindingEnabled
        value: {
            trigger
            return listView.currentItem ? listView.currentItem.modelData : undefined
        }
    }

    EventSource {
        id: eventSource
        path: "actions/" + currentProject
        includeHelpers: true
    }

    ActionProxy {
        id: actionProxy
        sourceModel: eventSource
        query: searchField.text
    }

    Rectangle {
        id: filtering
        anchors {
            left: parent.left
            top: parent.top
            bottom: parent.bottom
        }

        width: 240
        color: "#ddd"

        ScrollView {
            anchors.fill: parent

            Column {
                anchors {
                    top: parent.top
                    left: parent.left
                    right: parent.right
                    margins: 8
                }

                Label {
                    text: "Filter"
                    font.pixelSize: 24
                    font.weight: Font.Light
                }

                Label {
                    text: "Action:"
                    height: 20
                    font.pixelSize: 15
                    font.weight: Font.Light
                }

                TextField {
                    id: searchField
                    anchors {
                        left: parent.left
                        right: parent.right
                    }

                    placeholderText: "Search"
                }

                Column {

                    Label {
                       text: "Tag"
                       height: 20
                       font.pixelSize: 15
                       font.weight: Font.Light
                    }
                    Repeater {
                        id: tagRepeater
                        property var checkedElements: []
                        model: ActionAttributeModel {
                            source: eventSource
                            name: 'tags'
                        }
                        delegate:   CheckBox {
                            text: attribute

                            onCheckedChanged: {
                                if(checked) {tagRepeater.checkedElements.push(attribute)}
                                else {tagRepeater.checkedElements.splice(
                                    tagRepeater.checkedElements.indexOf(attribute), 1)
                                }
                                var attributes = ""
                                for(var i in tagRepeater.checkedElements) {
                                  var attr = tagRepeater.checkedElements[i]
                                    attributes = attributes + ";" + attr
                                }
                                actionProxy.setRequirement("tags", attributes)
                            }
                        }
                    }
                    Label {
                       text: "Type"
                       height: 20
                       font.pixelSize: 15
                       font.weight: Font.Light
                    }
                    Repeater {
                        id: typeRepeater
                        property var checkedElements: []
                        model: ActionAttributeModel {
                            source: eventSource
                            name: 'type'
                          }
                          delegate:   CheckBox {
                              text: attribute

                            onCheckedChanged: {
                                if(checked) {typeRepeater.checkedElements.push(attribute)}
                                else {typeRepeater.checkedElements.splice(
                                    typeRepeater.checkedElements.indexOf(attribute), 1)
                                }
                                var attributes = ""
                                for(var i in typeRepeater.checkedElements) {
                                  var attr = typeRepeater.checkedElements[i]
                                    attributes = attributes + ";" + attr
                                }
                                actionProxy.setRequirement("type", attributes)
                            }
                        }
                    }
                    Label {
                       text: "User"
                       height: 20
                       font.pixelSize: 15
                       font.weight: Font.Light
                    }
                    Repeater {
                        id: userRepeater
                        property var checkedElements: []
                        model: ActionAttributeModel {
                            source: eventSource
                            name: 'users'
                        }
                        delegate:   CheckBox {
                            text: attribute

                            onCheckedChanged: {
                                if(checked) {userRepeater.checkedElements.push(attribute)}
                                else {userRepeater.checkedElements.splice(
                                    userRepeater.checkedElements.indexOf(attribute), 1)
                                }
                                var attributes = ""
                                for(var i in userRepeater.checkedElements) {
                                  var attr = userRepeater.checkedElements[i]
                                    attributes = attributes + ";" + attr
                                }
                                actionProxy.setRequirement("users", attributes)
                            }
                        }
                    }
                    Label {
                       text: "Subject"
                       height: 20
                       font.pixelSize: 15
                       font.weight: Font.Light
                    }
                    Repeater {
                        id: subjectRepeater
                        property var checkedElements: []
                        model: ActionAttributeModel {
                            source: eventSource
                            name: 'subjects'
                        }
                        delegate:   CheckBox {
                            text: attribute

                            onCheckedChanged: {
                                if(checked) {subjectRepeater.checkedElements.push(attribute)}
                                else {subjectRepeater.checkedElements.splice(
                                    subjectRepeater.checkedElements.indexOf(attribute), 1)
                                }
                                var attributes = ""
                                for(var i in subjectRepeater.checkedElements) {
                                  var attr = subjectRepeater.checkedElements[i]
                                    attributes = attributes + ";" + attr
                                }
                                actionProxy.setRequirement("subjects", attributes)
                            }
                        }
                    }
                    Label {
                       text: "Location"
                       height: 20
                       font.pixelSize: 15
                       font.weight: Font.Light
                    }
                    Repeater {
                        id: locationRepeater
                        property var checkedElements: []
                        model: ActionAttributeModel {
                            source: eventSource
                            name: 'location'
                        }
                        delegate:   CheckBox {
                            text: attribute

                            onCheckedChanged: {
                                if(checked) {locationRepeater.checkedElements.push(attribute)}
                                else {locationRepeater.checkedElements.splice(
                                    locationRepeater.checkedElements.indexOf(attribute), 1)
                                }
                                var attributes = ""
                                for(var i in locationRepeater.checkedElements) {
                                  var attr = locationRepeater.checkedElements[i]
                                    attributes = attributes + ";" + attr
                                }
                                actionProxy.setRequirement("location", attributes)
                            }
                        }
                    }
                    Label {
                       text: "Date"
                       height: 20
                       font.pixelSize: 15
                       font.weight: Font.Light
                    }
                    Repeater {
                        id: datetimeRepeater
                        property var checkedElements: []
                        model: ActionAttributeModel {
                            source: eventSource
                            name: 'datetime'
                        }
                        delegate:   CheckBox {
                            text: attribute

                            onCheckedChanged: {
                                if(checked) {datetimeRepeater.checkedElements.push(attribute)}
                                else {datetimeRepeater.checkedElements.splice(
                                    datetimeRepeater.checkedElements.indexOf(attribute), 1)
                                }
                                var attributes = ""
                                for(var i in datetimeRepeater.checkedElements) {
                                  var attr = datetimeRepeater.checkedElements[i]
                                    attributes = attributes + ";" + attr
                                }
                                actionProxy.setRequirement("datetime", attributes)
                            }
                        }
                    }
                }
            }
        }
    }

    Rectangle {
        id: stuff
        anchors {
            left: filtering.right
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
            text: listView.count + " actions"
            color: "#787878"
            font.pixelSize: 14
        }
    }

    QQC1.ScrollView {
        anchors {
            top: stuff.bottom
            bottom: parent.bottom
            right: parent.right
            left: filtering.right
        }
        ListView {
            id: listView
            anchors.fill: parent
            clip: true
            model: actionProxy

            highlightMoveDuration: 400
            highlight: Rectangle {
                color: "black"
                opacity: 0.1
            }
            delegate: Rectangle {
                readonly property var index: model.index
                readonly property var key: model.key
                readonly property var modelData: model.contents
                anchors {
                    left: parent.left
                    right: parent.right
                }
                height: 64
                color: 'transparent'
                Item {
                    id: imageItem
                    anchors {
                        left: parent.left
                        top: parent.top
                        bottom: parent.bottom
                    }
                    width: height
                    Identicon {
                        anchors.centerIn: parent
                        width: parent.height * 0.6
                        height: width
                        action: modelData
                    }
                }

                Column {
                    spacing: 10
                    anchors {
                        topMargin: 12
                        left: imageItem.right
                        right: parent.right
                        top: parent.top
                        bottom: parent.bottom
                    }
                    Text {
                        color: "#121212"
                        text: key
                        font.pixelSize: 12
                    }
                    Text {
                        color: "#545454"
                        text: {
                            var results = []
                            if(modelData.type) {
                                results.push(modelData.type)
                            }
                            if(modelData.datetime) {
                                try {
                                    var date = new Date(modelData.datetime)
                                    var dateString = date.toISOString().substring(0, 10)
                                    results.push(dateString)
                                } catch (e) {
                                }

                            }
                            return results.join(", ")
                        }
                        font.pixelSize: 11
                    }
                }
                MouseArea {
                    anchors.fill: parent
                    onClicked: {
                        listView.currentIndex = index
                        forceActiveFocus()
                    }
                }
            }
        }
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

    Dialog {
        id: newDialog
        title: "Create new action"
        Column {
            spacing: 8
            Label {
                text: "Provide an unique ID for your action.\n" +
                      "A good ID is easy to remember and follows a naming scheme."
            }
            TextField {
                id: newName
                selectByMouse: true
                text: {
                    return new Date().toISOString().slice(0, 10)
                }
            }
            Label {
                text: "Examples: '2016-01-12_1', 'bobby_1_init', 'lucia_surgery'"
            }
        }
        standardButtons: Dialog.Cancel | Dialog.Ok
        onAccepted: {
            if(!currentProject) {
                console.log("ERROR: Current project not set.")
                return
            }

            if(!newName.text) {
                console.log("ERROR: Name cannot be empty.")
                return
            }
            var registered = (new Date()).toISOString()
            var experiment = {
                registered: registered
            }
            Firebase.put("actions/" + currentProject + "/" + newName.text, experiment, function(req) {
                var experiment = JSON.parse(req.responseText)
                requestedId = experiment.name
            })
        }
    }
}
