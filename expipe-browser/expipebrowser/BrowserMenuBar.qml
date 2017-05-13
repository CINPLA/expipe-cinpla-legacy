import QtQuick 2.4
import QtQuick.Controls 1.3
import QtQuick.Dialogs 1.2
import QtQuick.Layouts 1.1

//import io.thp.pyotherside 1.3

MenuBar {
    property Action loadDataAction
    Menu {
        title: qsTr("File")
        MenuItem {
            action: loadDataAction
        }
        MenuItem {
            text: qsTr("Exit")
            onTriggered: Qt.quit();
        }
    }
}
