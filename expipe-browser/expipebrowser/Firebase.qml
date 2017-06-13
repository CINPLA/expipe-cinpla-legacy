pragma Singleton
import QtQuick 2.0
import ExpipeBrowser 1.0

QtObject {
    function get(name, callback) {
        var url = Pyrebase.buildUrl(name)
        var req = new XMLHttpRequest()
        req.open("GET", url)
        req.onreadystatechange = function() {
            if(req.readyState !== XMLHttpRequest.DONE) {
                return
            }
            if(req.status !== 200) {
                console.log("Error", req.status, req.statusText)
                console.log(req.responseText)
                return
            }
            callback(req)
        }
        //    req.setRequestHeader("Authorization", authorization)
        req.send()
    }

    function patch(name, data, callback) {
        var url = Pyrebase.buildUrl(name)
        var req = new XMLHttpRequest()
        req.onreadystatechange = function() {
            if(req.readyState != XMLHttpRequest.DONE) {
                return
            }
            if(req.status != 200) {
                console.log("ERROR:", req.status, req.statusText)
                console.log(req.responseText)
                return
            }
            callback(req)
        }
        req.open("POST", url)
        req.setRequestHeader("X-HTTP-Method-Override", "PATCH")
        //    req.setRequestHeader("Authorization", Firebase.authorization)
        req.send(JSON.stringify(data))
    }

    function put(name, data, callback) {
        var url = Pyrebase.buildUrl(name)
        var req = new XMLHttpRequest()
        req.onreadystatechange = function() {
            if(req.readyState != XMLHttpRequest.DONE) {
                return
            }
            if(req.status != 200) {
                console.log("ERROR:", req.status, req.statusText)
                console.log(req.responseText)
                return
            }
            callback(req)
        }
        req.open("PUT", url)
        //    req.setRequestHeader("Authorization", Firebase.authorization)
        req.send(JSON.stringify(data))
    }

    function remove(name, callback) {
        var url = Pyrebase.buildUrl(name)
        var req = new XMLHttpRequest()
        req.onreadystatechange = function() {
            if(req.readyState != XMLHttpRequest.DONE) {
                return
            }
            if(req.status != 200) {
                console.log("ERROR:", req.status, req.statusText)
                console.log(req.responseText)
                return
            }
            callback(req)
        }
        req.open("DELETE", url)
        req.send()
    }

    function post(name, data, callback) {
        var url = Pyrebase.buildUrl(name)
        var req = new XMLHttpRequest()
        req.onreadystatechange = function() {
            if(req.readyState != XMLHttpRequest.DONE) {
                return
            }
            if(req.status != 200) {
                console.log("ERROR:", req.status, req.statusText)
                console.log(req.responseText)
                return
            }
            console.log("Post result:", req.status, req.responseText)
            callback(req)
        }
        req.open("POST", url)
        req.send(JSON.stringify(data))
    }

    property var timer: Timer {
        interval: 60 * 1000
        repeat: true
        running: true
        onTriggered: {
            Pyrebase.refreshToken()
        }
    }
}
