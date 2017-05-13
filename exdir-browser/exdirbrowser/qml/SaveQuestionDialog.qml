import QtQuick 2.5
import QtQuick.Window 2.2
import QtQuick.Controls 1.4
import QtQuick.Controls.Styles 1.4
import QtQuick.Layouts 1.1
import QtQml.Models 2.2
import QtQuick.Dialogs 1.2

import H5Vis 1.0

MessageDialog {
    id: saveQuestionDialog
    property var acceptCallback: undefined
    property var rejectCallback: undefined
    property var discardCallback: undefined

    function resetCallbacks() {
        acceptCallback = undefined
        rejectCallback = undefined
        discardCallback = undefined
    }

    standardButtons: StandardButton.Discard | StandardButton.Cancel | StandardButton.Save
    text: "You have unsaved changes. Would you like to save or discard these?"
    onAccepted: {
        if(tableModel.save()) {
            acceptCallback()
        } else {
            rejectCallback()
        }
        resetCallbacks()
    }
    onDiscard: {
        if(discardCallback) {
            discardCallback()
        }
        resetCallbacks()
    }
    onRejected: {
        if(rejectCallback) {
            rejectCallback()
        }
        resetCallbacks()
    }
}
