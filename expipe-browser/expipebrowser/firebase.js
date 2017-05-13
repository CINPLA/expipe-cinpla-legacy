.pragma library

Qt.include("eventsource.js")

var server_url = "https://expipe-26506.firebaseio.com/"
var auth
//var authorization = "Bearer ya29.ElvZA4EwrxikCePuWNANUp6EYW2is2tPnYiCIhsOiAtfUWqEfI1xYYScquAeIkdwn8asStPVZpbCjOAgFwLH31Lr964XSQwSw7dsNeMiOY5HOVw6D-hZORh-ADaI"

function test(callback) {
    var url = server_url + ".json?shallow=true&auth=" + auth
    var req = new XMLHttpRequest()
    req.open("GET", url)
    req.onreadystatechange = function() {
        if(req.readyState !== XMLHttpRequest.DONE) {
            return
        }
        if(req.status !== 200) {
            console.log("Error", req.status, req.statusText)
            console.log(req.responseText)
            callback(false)
            return
        }
        callback(true)
    }
    //    req.setRequestHeader("Authorization", authorization)
    req.send()
}

function get(name, callback) {
    var url = server_url + name + ".json?auth=" + auth
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
    var url = server_url + name + ".json?auth=" + auth
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
    var url = server_url + name + ".json?auth=" + auth
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
    var url = server_url + name + ".json?auth=" + auth
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
    var url = server_url + name + ".json?auth=" + auth
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

function listen(parent, name, putCallback, patchCallback, errorCallback) {
    if(!timerRoot) {
        timerRoot = parent
    }

    console.log("Requesting listen on", name)

    var url = server_url + name + ".json?auth=" + auth

    var source = new EventSource(url);

    source.onopen = function () {
        console.log("Opened listen on", name)
    };
    source.onerror = function () {
        console.log("Errored")
        errorCallback()
    };

    source.addEventListener("put", function (event) {
        var data = JSON.parse(event.data)
        putCallback(data.path, data.data)
    });

    source.addEventListener("patch", function (event) {
        var data = JSON.parse(event.data)
        patchCallback(data.path, data.data)
    });

    source.onmessage = function (event) {
        console.log("Message", event)
    }
    return source
}
