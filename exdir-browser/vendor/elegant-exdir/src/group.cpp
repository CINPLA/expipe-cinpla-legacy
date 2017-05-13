#include "group.h"

#include <sstream>
#include <iostream>
#include <regex>
#include <boost/range/iterator_range.hpp>
#include <boost/filesystem.hpp>
#include <boost/filesystem/fstream.hpp>
#include <fstream>
#include <yaml-cpp/yaml.h>

#include "object.h"
#include "dataset.h"
#include "attribute.h"

using namespace std;
namespace fs = boost::filesystem;

namespace elegant {
namespace exdir {


Group::Group(ConversionFlags conversionFlags)
    : Object(Type::Group, conversionFlags)
{
}

Group::Group(const Group &other)
    : Object(Type::Group)
{
    constructFromOther(other);
}

Group::~Group()
{
    close();
}

Group::Group(const Object &other)
{
    constructFromOther(other);
}

Group& Group::operator=(const Object &other)
{
    Object::operator =(other);
    return *this;
}

Group& Group::operator=(const Group &other)
{
    Object::operator =(other);
    return *this;
}

Group::Group(string name, boost::filesystem::path path, ConversionFlags conversionFlags)
    : Object(name, path, Type::Group, conversionFlags)
{
}

vector<string> Group::keys() const
{
    if(!isValid()) {
        DVLOG(1) << "Object is not valid. Cannot request list of keys. " << *this;
        return vector<string>();
    }
    vector<string> result;
    for(auto& entry : boost::make_iterator_range(fs::directory_iterator(path()), {})) {
        if(boost::filesystem::is_directory(entry)) {
            result.push_back(entry.path().filename().string());
        }
    }
    sort(begin(result), end(result));
    return result;
}

vector<Object> Group::items()
{
    vector<Object> returnedItems;
    for(auto key : keys()) {
        returnedItems.push_back(item(key));
    }
    return returnedItems;
}

Object Group::item(string key) const
{
    if(!isValid()) {
        throw(std::runtime_error("Requested key from from invalid group object"));
    }
    if(!hasKey(key)) {
        throw(std::runtime_error("Could not find key"));
    }
    boost::filesystem::path keyPath = path() / key;
    boost::filesystem::path metaFilePath = keyPath / "meta.yml";

    if(!boost::filesystem::exists(metaFilePath)) {
        std::cout << "Could not find " << metaFilePath << std::endl;
        return Object();
    }
    YAML::Node rootNode = YAML::LoadFile(metaFilePath.string());
    YAML::Node exdirNode = rootNode["exdir"];
    Type type = Type::Invalid;
    if(exdirNode["type"].as<string>() == "group") {
        type = Type::Group;
    } else if (exdirNode["type"].as<string>() == "dataset") {
        type = Type::Dataset;
    }

//    Type type = Type::Group;
    return Object(key, m_path / key, type, m_inheritedConversionFlags);
}

Object Group::operator[](string key) const
{
    return item(key);
}

vector<string> split(const string &s, char delim)
{
    vector<string> elements;
    string item;

    stringstream ss(s);
    while (getline(ss, item, delim)) {
        if(!item.empty()) {
            elements.push_back(item);
        }
    }
    return elements;
}

Group Group::createGroup(string name)
{
    if(!isValid()) {
        throw(std::runtime_error("Cannot create group in invalid object"));
    }
    if(hasKey(name)) {
        if(item(name).type() == Type::Group) {
            DVLOG(1) << "WARNING: Group already exists with name " << name;
        } else {
            throw(std::runtime_error("Cannot create group. A non-group object already exists with that name."));
        }
        return Group();
    }
    // TODO create groups
    throw std::runtime_error("Not implemented");
}

bool Group::hasKey(string name) const
{
    if(!isValid()) {
        return false;
    }
    if(boost::filesystem::exists(path() / name)) {
        return true;
    } else {
        return false;
    }
}

}
}
