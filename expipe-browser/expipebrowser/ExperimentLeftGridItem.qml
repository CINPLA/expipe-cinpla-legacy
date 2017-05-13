import QtQuick 2.4
import QtQuick.Controls 1.3
import QtQuick.Dialogs 1.2
import QtQuick.Layouts 1.1

Item {
    property alias text: textItem.text
    Layout.preferredHeight: 18
    Layout.preferredWidth: 240
    Text {
        id: textItem
        anchors {
            right: parent.right
        }
        color: "#434343"        
    }
}
