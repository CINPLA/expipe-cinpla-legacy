import QtQuick 2.4
import QtQuick.Controls 1.4
import QtQuick.Dialogs 1.2
import QtQuick.Layouts 1.1
import Qt.labs.settings 1.0

import "." // qmldir for Style

Rectangle {
    id: root
    property string identiconProvider: "robohash"
    Settings {
        property alias identiconProvider: root.identiconProvider
    }
    onIdenticonProviderChanged: {
        Style.identiconProvider = root.identiconProvider
    }

    Column {
        anchors.centerIn: parent
        // GroupBox {
        //     title: "Icon flavor"
        //     ButtonGroup {
        //         id: buttonGroup
        //         buttons: column.children
        //     }
        //     Binding {
        //         target: root
        //         property: "identiconProvider"
        //         value: buttonGroup.checkedButton.value
        //     }
        //     Column {
        //         id: column
        //         RadioButton {
        //             id: roboHashButton
        //             property string value: "robohash"
        //             text: "Awesome robots"
        //             checked: true
        //             Binding {
        //                 target: roboHashButton
        //                 property: "checked"
        //                 value: root.identiconProvider === roboHashButton.value
        //             }
        //         }
        //         RadioButton {
        //             id: geometricButton
        //             property string value: "gravatar"
        //             text: "Beautiful geometries"
        //             Binding {
        //                 target: geometricButton
        //                 property: "checked"
        //                 value: root.identiconProvider === geometricButton.value
        //             }
        //         }
        //     }
        // }
    }
}
