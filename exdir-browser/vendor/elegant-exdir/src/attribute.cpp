#include "attribute.h"

#include <boost/filesystem.hpp>
#include <yaml-cpp/yaml.h>

using namespace std;
namespace fs = boost::filesystem;

namespace elegant {
namespace exdir {


Attribute::Attribute()
{
}

Attribute::Attribute(fs::path path, const std::string &name, Object::ConversionFlags inheritedFlags)
    : m_path(path)
    , m_name(name)
    , m_inheritedConversionFlags(inheritedFlags)
{
}


//Attribute::Attribute(Attribute &&other)
//    : m_id(move(other.m_id))
//    , m_parentID(move(other.m_parentID))
//    , m_name(move(other.m_name))
//{
//    other.m_id = 0;
//}

Attribute::Attribute(const Attribute &other)
{
    DVLOG(1) << "Copy construct attribute";
    constructFromOther(other);
}

Attribute &Attribute::operator=(const Attribute &other)
{
    // TODO
    throw std::runtime_error("Not implemented");
}

void Attribute::constructFromOther(const Attribute &other) {
    m_path = other.m_path;
    m_name = other.m_name;
    m_inheritedConversionFlags = other.m_inheritedConversionFlags;
}

Attribute::~Attribute()
{
    close();
}

void Attribute::close()
{
    // TODO
}

Datatype::Type Attribute::datatype() const
{
//    return Datatype::Type::Unknown;
    return Datatype::Type::String;
}

bool Attribute::isValid() const
{
    fs::path filePath = m_path / "attributes.yml";
    if(!fs::exists(filePath)) {
        return true;
    }
    return false;
}

bool Attribute::isNonExistingNamed() const
{
    return (!isValid() && !m_name.empty() && m_parent != nullptr);
}

bool Attribute::isScalar() const
{
    return true; // TODO what does this mean now?
}

bool Attribute::isSimple() const
{
    return true; // TODO what does this mean now?
}

int Attribute::dimensionCount() const
{
    return 1; // TODO what does this mean now?
}

std::vector<size_t> Attribute::extents() const
{
    return {1};
}

std::string Attribute::name() const
{
    return m_name;
}

boost::filesystem::path Attribute::path() const
{
    return m_path;
}

std::string Attribute::toString() const
{
    // TODO perhaps just return the YAML node?
    fs::path filePath = m_path / "attributes.yml";
    if(!fs::exists(filePath)) {
        cerr << filePath << endl;
        throw std::runtime_error("Requested attribute file does not exist");
    }
    YAML::Node rootNode = YAML::LoadFile(filePath.string());
    YAML::Node node = rootNode[name()];
    if(node.IsMap()) {
        if(node["value"]) {
            if(node["value"].IsScalar()) {
                stringstream result;
                result << node["value"].as<string>();
                if(node["unit"].IsScalar()) {
                    result << " ";
                    result << node["unit"].as<string>();
                }
                return result.str();
            }
        }
        return "[map]";
    }
    if(node.IsSequence()) {
        stringstream result;
        for(size_t i = 0; i < node.size(); i++) {
            result << node[i].as<string>();
            if(i < node.size() - 1) {
                result << ", ";
            }
        }
        return result.str();
    }
    if(node.IsNull()) {
        return "[null]";
    }
    if(!node.IsDefined()) {
        return "[undefined]";
    }
    auto value = node.as<string>();
    return value;
}

Attribute &Attribute::operator=(const string &value)
{
    // TODO
    throw std::runtime_error("Not implemented");
}

Attribute& Attribute::operator=(const char *object)
{
    operator=(std::string(object));
    return *this;
}

}
}
