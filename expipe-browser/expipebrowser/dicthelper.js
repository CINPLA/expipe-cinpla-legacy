function replace(object, value) {
    // we cannot assign directly, so just replace all properties
    for(var i in object) {
        delete(object[i])
    }
    for(var i in value) {
        object[i] = value[i]
    }
}

function findTarget(object, path) {
    var parts = path.split("/")
    var target = object
    for(var i = 0; i < parts.length - 1; i++) {
        if(parts[i] === "") {
            continue
        }
        target = target[parts[i]]
    }
    return {object: target, property: parts[i]}
}

function put(object, path, value) {
    console.log("Putting", path, JSON.stringify(value))
    if(path === "/") {
        replace(object, value)
        console.log("Put result on " + path, JSON.stringify(object))
        return
    }
    var t = findTarget(object, path)
    if(value === null) {
        delete(t.object[t.property])
    } else {
        t.object[t.property] = value
    }
    console.log("Put result on " + path, JSON.stringify(object))
}

function patch(object, path, value) {
    console.log("Patching", path, JSON.stringify(value))
    if(path === "/") {
        replace(object, value)
        console.log("Patch result on " + path, JSON.stringify(object))
        return
    }
    var t = findTarget(object, path)
    console.log("Got target", JSON.stringify(t))
    for(var j in value) {
        if(typeof(t.object[t.property]) !== "object") {
            // replace with object - setting properties on values won't work
            t.object[t.property] = {}
        }
        t.object[t.property][j] = value[j]
    }
    console.log("Patch result on " + path, JSON.stringify(object))
}
