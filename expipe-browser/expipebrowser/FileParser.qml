import QtQuick 2.4
import QtQuick.Controls 1.3
import QtQuick.Dialogs 1.2
import QtQuick.Layouts 1.1

import io.thp.pyotherside 1.3

Python {
    id: fileparserRoot
    property bool ready: false
    
    function loadData() {
        if(!ready) {
            return
        }
        call("hdf5_loader.load_file", [], parseData)
    }

    function parseData(result) {
        for(var i in result) {
            var element = result[i]
            tableModel.append(element)
        }
    }
    
    Component.onCompleted: {
        addImportPath(Qt.resolvedUrl("."))
        importModule("hdf5_loader", function() {
            ready = true
        })
    }
}
