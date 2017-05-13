import QtQuick 2.5
import QtQuick.Window 2.2
import QtQuick.Controls 1.4
import QtQuick.Controls.Styles 1.4
import QtQuick.Layouts 1.1
import QtQml.Models 2.2
import QtQuick.Dialogs 1.2

import H5Vis 1.0

ApplicationWindow {
    id: windowRoot

    property bool closeWithoutSaving: false

    visible: true
    width: 1280
    height: 1024

    title: "Exdir Browser"

    Timer {
        id: expandLater
        interval: 200
        onTriggered: {
            var index = treeView.__model.mapRowToModelIndex(0)
            treeView.__model.expand(index) // TODO revert this when calling expand works
        }
    }

    function loadFile(filename) {
        treeModel.source = filename
        treeView.forceActiveFocus()
        expandLater.start()
    }

    menuBar: MenuBar {
        Menu {
            title: "File"
            MenuItem {
                text: "Open..."
                action: openAction
            }
            MenuItem {
                text: "Save"
                action: saveAction
            }
        }
    }

    onClosing: {
        focusDummy.forceActiveFocus()
        if(tableModel.hasUnsavedChanges && !windowRoot.closeWithoutSaving) {
            close.accepted = false
            saveQuestionDialog.acceptCallback = function() {
                if(tableModel.save()) {
                    windowRoot.close()
                }
            }
            saveQuestionDialog.discardCallback = function() {
                windowRoot.closeWithoutSaving = true
                windowRoot.close()
            }
            saveQuestionDialog.rejectCallback = function() {}
            saveQuestionDialog.open()
        } else {
            close.accepted = true
        }
    }

    Action {
        id: openAction
        shortcut: StandardKey.Open
        onTriggered: {
            openFileDialog.open()
        }
    }

    Action {
        id: saveAction
        shortcut: StandardKey.Save
        onTriggered: {
            focusDummy.forceActiveFocus() // take focus away from text inputs to trigger editingFinished
            tableModel.save()
        }
    }

    Item {
        id: focusDummy
    }

    FileDialog {
        id: openFileDialog
        function loadFile() {
            windowRoot.loadFile(fileUrl)
        }

        onAccepted: {
            tableModel.loadOrAsk(loadFile, undefined, loadFile)
        }
    }

    ExdirDatasetModel {
        id: tableModel
    
        function loadCurrentDataset() {
            tableModel.dataset = treeView.currentItem.path
        }
    
        function loadOrAsk(acceptCallback, rejectCallback, discardCallback) {
            if(!tableModel.hasUnsavedChanges) {
                acceptCallback()
            } else {
                saveQuestionDialog.acceptCallback = acceptCallback
                saveQuestionDialog.rejectCallback = rejectCallback
                saveQuestionDialog.discardCallback = discardCallback
                saveQuestionDialog.open()
            }
        }
    
        currentSlice: sliceSlider.value
        source: treeModel.source
    }

    ExdirTreeModel {
        id: treeModel
        source: ""
        onDataChanged: {
            treeView.selection.clear()
        }
    }

    SaveQuestionDialog {
        id: saveQuestionDialog
    }

    RowLayout {
        anchors.fill: parent
        spacing: 0
        TreeView {
            id: treeView
            property var pIndex: undefined
            property var ppIndex: undefined

            property var currentItem: treeModel.item(currentIndex)

            Layout.minimumWidth: 300
            Layout.fillHeight: true
            frameVisible: false
            model: treeModel
            style: TreeViewStyle {
                itemDelegate: Item {
                    Text {
                        anchors {
                            verticalCenter: parent.verticalCenter
                            left: parent.left
                            leftMargin: 18
                        }
                        color: styleData.selected ? "#efefef" : "#cdcdcd"
                        font.pointSize: 11
                        text: model ? model.name : ""
                    }
                }
                branchDelegate: Item {
                    width: 16
                    height: 16
                    anchors.left: parent ? parent.left : undefined
                    anchors.leftMargin: 15
                    Image {
                        anchors.centerIn: parent
                        width: 12
                        height: 12
                        source: "../images/branch.png"
                        rotation: styleData.isExpanded ? 90 : 0
                        smooth: true
                        antialiasing: true
                        Behavior on rotation {
                            NumberAnimation {
                                easing.type: Easing.OutQuad
                                duration: 120
                            }
                        }
                    }
                }
                rowDelegate: Rectangle {
                    Rectangle {
                        width: 6
                        height: parent.height
                        color: "#39B2E1"
                        visible: styleData.selected
                    }
                    height: 36
                    color: styleData.selected ? "#282828" : "#363636"
                }
                headerDelegate: Item {

                }
            }

            selection: ItemSelectionModel {
                property bool ignoreIndexChange: false

                function revertSelection() {
                    ignoreIndexChange = true
                    setCurrentIndex(treeView.ppIndex, ItemSelectionModel.ClearAndSelect)
                    ignoreIndexChange = false
                    treeView.pIndex = treeView.ppIndex
                }

                onCurrentIndexChanged: {
                    if(ignoreIndexChange) {
                        return
                    }
                    treeView.ppIndex = treeView.pIndex
                    treeView.pIndex = treeView.currentIndex
                    tableModel.loadOrAsk(tableModel.loadCurrentDataset,
                                         treeView.revertSelection,
                                         tableModel.loadCurrentDataset)
                }

                model: treeView.model
            }

            function revertSelection() {
                selection.revertSelection()
            }
            
            onDoubleClicked: __model.isExpanded(index) ? __model.collapse(index) : __model.expand(index)
            // onClicked: expand(index)
            
            
            // TODO these are defined in the original TreeView, but call TreeView.expand()
            // which is currently broken in PyQt. Remove these once the original functions work.
            Keys.onRightPressed: {
                if (currentIndex.valid)
                    treeView.__model.expand(currentIndex)
                else
                    event.accepted = false
            }

            Keys.onLeftPressed: {
                if (currentIndex.valid)
                    treeView.__model.collapse(currentIndex)
                else
                    event.accepted = false
            }

            Keys.onReturnPressed: {
                if (currentIndex.valid)
                    treeView.__model.activated(currentIndex)
                else
                    event.accepted = false
            }

            TableViewColumn {
                title: "Name"
                role: "name"
                width: 290
            }
        }
        Rectangle {
            Layout.minimumWidth: 300
            Layout.fillHeight: true
            color: "#efefef"
            Rectangle {
                anchors {
                    top: parent.top
                    bottom: parent.bottom
                    right: parent.right
                }
                color: "#dedede"
                width: 1
            }
            Column {
                id: objectInfoColumn
                anchors {
                    top: parent.top
                    left: parent.left
                    leftMargin: 36
                    topMargin: 24
                    rightMargin: 16
                    right: parent.right
                }
                spacing: 12
                Text {
                    font.pixelSize: 24
                    text: treeView.currentItem ? treeView.currentItem.name : ""
                    font.weight: Font.Light
                    color: "#121212"
                    elide: Text.ElideRight
                    width: parent.width
                }
                RowLayout {
                    height: 16
                    width: parent.width
                    Text {
                        id: typeText
                        font.pointSize: 10
                        text: treeView.currentItem ? treeView.currentItem.type : ""
                        color: "#787878"
                    }
//                    Text {
//                        Layout.fillWidth: true
//                        font.pointSize: 10
//                        text: treeView.currentItem ? treeView.currentItem.path : ""
//                        color: "#787878"
//                        width: parent.width
//                        elide: Text.ElideMiddle
//                    }
                }
                Text {
                    font.pointSize: 10
                    color: "#787878"
                    // text: attributesModel.count + " attributes"
                    visible: treeView.currentItem ? true : false
                }
                Text {
                    font.pointSize: 10
                    color: "#787878"
                    text: treeView.currentItem ? treeView.currentItem.info : ""
                    visible: treeView.currentItem ? true : false
                }
                Text {
                    font.pointSize: 10
                    color: "#787878"
                    text: "Slice " + (sliceSlider.value + 1) + " of " + (sliceSlider.maximumValue + 1)
                    visible: sliceSlider.visible
                }

                Slider {
                    id: sliceSlider
                    minimumValue: 0.0
                    // maximumValue: Math.max(0.0, Math.floor(tableModel.sliceCount - 1))
                    visible: tableModel.sliceCount > 1
                    stepSize: 1.0
                    width: parent.width
                }
            }
            ListView {
                anchors {
                    top: objectInfoColumn.bottom
                    topMargin: 24
                    bottom: parent.bottom
                    left: objectInfoColumn.left
                    right: objectInfoColumn.right
                }
                spacing: 12
                model: ExdirAttributesModel {
                    id: attributesModel
                    source: treeModel.source
                    path: tableModel.dataset
                }
                delegate: Column {
                    spacing: 8
                    width: parent.width
                    TextEdit {
                        anchors {
                            left: parent.left
                            right: parent.right
                        }
                        text: name ? name : ""
                        font.pointSize: 10.5
                        color: "#494949"
                        wrapMode: Text.WrapAtWordBoundaryOrAnywhere
                        selectByMouse: true
                        readOnly: true
                        onFocusChanged: {
                            if(!focus) {
                                select(0, 0)
                            }
                        }
                    }
                    TextEdit {
                        anchors {
                            left: parent.left
                            leftMargin: 16
                            right: parent.right
                        }
                        text: value ? formatValue(value) : ""
                        selectByMouse: true
                        wrapMode: Text.WrapAtWordBoundaryOrAnywhere
                        color: "#121212"
                        font.pointSize: 11
                        font.weight: Font.Light
                        readOnly: true
                        onFocusChanged: {
                            if(!focus) {
                                select(0, 0)
                            }
                        }
                        function formatValue(value) {
                            if(typeof(value) == "object") {
                                var string = "["
                                var first = true
                                for(var i in value) {
                                    if(!first) {
                                        string += ", "
                                    }
                                    string += value[i]
                                    first = false
                                }
                                string += "]"
                                return string
                            } else {
                                return value
                            }
                        }
                    }
                }
                Text {
                    anchors.centerIn: parent
                    visible: attributesModel.count < 1
                    text: "< no attributes >"
                    color: "#787878"
                    font.weight: Font.Light
                    font.pointSize: 10
                }
        
            }
        }
        ScrollView {
            id: scrollView
        
            property bool textVisible: true
            property real lastMove: Date.now()
            
            property real contentX: flickableItem.contentX
            property real contentY: flickableItem.contentY
        
            Layout.fillHeight: true
            Layout.fillWidth: true
        
            horizontalScrollBarPolicy: Qt.ScrollBarAlwaysOn
            verticalScrollBarPolicy: Qt.ScrollBarAlwaysOn
            Rectangle {
                anchors.fill: parent
                color: "#fefefe"
            }
        
            MatrixView {
                id: tableView
        
                model: tableModel
        
                cellWidth: 75
                cellHeight: 30
        
                delegate: Component {
                        Rectangle {
                        id: cell
                        property bool selected: index === tableView.currentIndex
                        property bool active: cellTextInput.focus
                        color: "#fefefe"
                        border.width: 1.0
                        border.color: Qt.rgba(0.9, 0.9, 0.95, 1.0)
                        Rectangle {
                            anchors.fill: parent
                            visible: cell.selected
                            color: "#cdf0f3"
                        }
                        Text {
                            id: cellText
                            anchors.fill: parent
                            anchors.margins: 4
                            visible: !cell.active
                            font: cellTextInput.font
                            text: value
                            elide: Text.ElideRight
                            verticalAlignment: Text.AlignVCenter
                            horizontalAlignment: Text.AlignLeft
                            renderType: Text.NativeRendering
                        }
                        TextInput {
                            id: cellTextInput
                            property var contextValue: cell.selected ? value : ""
                            property bool textSetByContextValue: false
                            property bool dirty: false
                            anchors.fill: parent
                            anchors.margins: 4
                            clip: true
                            visible: focus
                            text: "N/A"
                            font.pixelSize: 14
                            selectByMouse: true
                            verticalAlignment: Text.AlignVCenter
                            horizontalAlignment: Text.AlignLeft
                            renderType: Text.NativeRendering
                            validator: DoubleValidator {
                                locale: "en_US.UTF-8"
                            }
                            onContextValueChanged: {
                                textSetByContextValue = true
                                text = value
                                textSetByContextValue = false
                                dirty = false
                            }
                            onTextChanged: {
                                if(!textSetByContextValue) {
                                    dirty = true
                                }
                            }
                            onEditingFinished: {
                                if(dirty) {
                                    text = text.replace(",", ".")
                                    tableModel.setData(index, text)
                                    dirty = false
                                }
                            }
                            onAccepted: {
                                cell.forceActiveFocus()
                            }
                        }
                        Keys.priority: Keys.AfterItem
                        Keys.onPressed: {
                            if(cellTextInput.focus) {
                                event.accepted = false
                                return
                            }
                            if(event.modifiers & Qt.ControlModifier) {
                                event.accepted = false
                                return
                            }
                            if(event.key === Qt.Key_Shift || event.key === Qt.Key_Enter
                                    || event.key === Qt.Key_Return) {
                                event.accepted = false
                                return
                            }
                            if(event.key === Qt.Key_Delete || event.key === Qt.Key_Backspace) {
                                cellTextInput.forceActiveFocus()
                                cellTextInput.text = ""
                                return
                            }
                            if(event.text === "") {
                                event.accepted = false
                                return
                            }
                            cellTextInput.forceActiveFocus()
                            cellTextInput.text = event.text
                        }
                        MouseArea {
                            id: cellMouseArea
                            anchors.fill: parent
                            propagateComposedEvents: true
                            onDoubleClicked: {
                                cellTextInput.selectAll()
                            }
                            onPressed: {
                                tableView.currentIndex = index
                                if(cellTextInput.focus) {
                                    mouse.accepted = false
                                } else if(cell.focus) {
                                    cellTextInput.forceActiveFocus()
                                    cellTextInput.ensureVisible(0)
                                    var position = cellMouseArea.mapToItem(cellTextInput, mouse.x, mouse.y)
                                    var cursor = cellTextInput.positionAt(position.x, position.y)
                                    cellTextInput.select(cursor, cursor)
                                } else {
                                    cell.forceActiveFocus()
                                }
                            }
                        }
                    }
                }
            }
        }
    }

    DropArea {
        anchors.fill: parent
        onDropped: {
            for(var i in drop.urls) {
                var url = drop.urls[i]
                loadFile(url)
            }
        }
    }

    Shortcut {
        sequence: "Ctrl+R"
        onActivated: {
            loadFile("file:///tmp/test.exdir")
        }
    }
}
