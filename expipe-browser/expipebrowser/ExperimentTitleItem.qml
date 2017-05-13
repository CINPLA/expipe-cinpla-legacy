import QtQuick 2.4
import QtQuick.Controls 1.3
import QtQuick.Dialogs 1.2
import QtQuick.Layouts 1.1

Item {
    property alias text: textItem.text
    Layout.columnSpan: 2
    Layout.fillWidth: true
    Layout.preferredHeight: 36
    Text {
        id: textItem
        anchors.left: parent.left
        anchors.bottom: parent.bottom
        anchors.leftMargin: 72
        color: "#434343"
    }
}
