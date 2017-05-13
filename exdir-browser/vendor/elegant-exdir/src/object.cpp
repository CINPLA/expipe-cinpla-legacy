#include "object.h"

#include "dataset.h"
#include "group.h"
#include "io/typehelper.h"

#include <yaml-cpp/yaml.h>
#include <boost/filesystem.hpp>

using namespace std;
namespace fs = boost::filesystem;

namespace elegant {
namespace exdir {

Object::Object(Type type, ConversionFlags conversionFlags)
    : m_type(type)
    , m_inheritedConversionFlags(conversionFlags)
{
}

Object::Object(string name, boost::filesystem::path path, Type type, ConversionFlags inheritedConversionFlags)
    : m_name(name)
    , m_path(path)
    , m_type(type)
    , m_inheritedConversionFlags(inheritedConversionFlags)
{
}

Object::Object(const Object &other, Object::CopyMode mode)
    : m_name(other.name())
    , m_path(other.path())
{
    if(mode == CopyMode::OpenOnCopy) {
        constructFromOther(other);
    }
}

Object &Object::operator=(const Object &other)
{
    bool copyFromExistingToExisting = isValid() && other.isValid();
    bool copyFromExistingToNonExisting = isNonExistingNamed() && other.isValid();

    bool isSame = (m_path == other.m_path);
    if(isSame) {
        DVLOG(1) << "Is the same object";
        return *this;
    } else if(copyFromExistingToExisting || copyFromExistingToNonExisting) {
        close();
        if(copyFromExistingToExisting) {
            std::runtime_error("Not implemented");
            // TODO
        }
        std::runtime_error("Not implemented");
        // TODO
        return *this;
    }
    constructFromOther(other);
    return *this;
}

Object &Object::operator =(const Dataset &other)
{
    const Object& otherObject = other;
    Object::operator =(otherObject);
    return *this;
}

Object &Object::operator =(const Group &other)
{
    const Object& otherObject = other;
    Object::operator =(otherObject);
    return *this;
}

void Object::constructFromOther(const Object &other)
{
    close();
    m_type = other.m_type;
    m_path = other.m_path;
    m_name = other.m_name;
    m_inheritedConversionFlags = other.m_inheritedConversionFlags;
}

boost::filesystem::path Object::path() const
{
    return m_path;
}

void Object::close()
{
    // TODO
}

Object::~Object()
{
    close();
}

const std::string& Object::name() const
{
    return m_name;
}

Object::Type Object::type() const
{
    return m_type;
}

bool Object::isValid() const
{
    // TODO
    return true;
}

bool Object::isDataset() const
{
    return (isValid() && type() == Type::Dataset);
}

bool Object::isGroup() const
{
    return (isValid() && type() == Type::Group);
}

bool Object::isNonExistingNamed() const
{
    return (!isValid() && !m_name.empty());
}

vector<string> Object::attributeKeys() const
{
    vector<string> keys;
    fs::path filePath = path() / "attributes.yml";
    if(!fs::exists(filePath)) {
        return keys;
    }
    YAML::Node rootNode = YAML::LoadFile(filePath.string());
    for(const auto& attribute : rootNode) {
        keys.push_back(attribute.first.as<string>());
    }
    return keys;
}

Attribute Object::operator()(string key) const
{
    return Attribute(path(), key, m_inheritedConversionFlags);
}

Attribute Object::attribute(string key) const
{
    if(!isValid()) {
        throw std::runtime_error("Trying to access attribute of invalid object");
    }
    return Attribute(path(), key, m_inheritedConversionFlags);
}

vector<Attribute> Object::attributes() const
{
    if(!isValid()) {
        throw std::runtime_error("Trying to access attributes of invalid object");
    }
    vector<Attribute> result;
    fs::path filePath = path() / "attributes.yml";
    if(!fs::exists(filePath)) {
        return result;
    }
    YAML::Node rootNode = YAML::LoadFile(filePath.string());
    for(const auto& attribute : rootNode) {
        result.push_back(Attribute(path(), attribute.first.as<string>(), m_inheritedConversionFlags));
    }
    return result;
}

bool Object::hasAttribute(string name) const
{
    if(!isValid()) {
        throw std::runtime_error("Trying to probe attribute of invalid object");
    }
    fs::path filePath = path() / "attributes.yml";
    if(!fs::exists(filePath)) {
        return false;
    }
    YAML::Node rootNode = YAML::LoadFile(filePath.string());
    if(rootNode[name]) {
        return true;
    }
    return false;
}


}
}
