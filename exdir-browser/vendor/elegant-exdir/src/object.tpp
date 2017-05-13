#ifndef OBJECT_TPP
#define OBJECT_TPP

#include "object.h"

namespace elegant {
namespace exdir {

#ifndef ELEGANT_EXDIR_NO_USER_DEFINED_CONVERSION_OPERATORS
template<typename T>
Object::operator T() const
{
    return value<T>();
}
#endif

template<typename T>
inline T& operator<<(T &other, const elegant::exdir::Object &object)
{
    other = object.value<T>();
    return other;
}

template<typename T>
inline T& operator>>(const elegant::exdir::Object &object, T &other)
{
    other = object.value<T>();
    return other;
}

inline std::ostream& operator<< (std::ostream &out, const elegant::exdir::Object &object)
{
    std::string typeName = "Unknown";
    elegant::exdir::Object::Type type = object.type();
    switch(type) {
    case elegant::exdir::Object::Type::File:
        typeName = "File";
        break;
    case elegant::exdir::Object::Type::Group:
        typeName = "Group";
        break;
    case elegant::exdir::Object::Type::Datatype:
        typeName = "Datatype";
        break;
    case elegant::exdir::Object::Type::Dataset:
        typeName = "Dataset";
        break;
    case elegant::exdir::Object::Type::Attribute:
        typeName = "Attribute";
        break;
    default:
        break;
    }
//    out << "Object(type=" << typeName << ", id=" << object.id() << ", name=\"" << object.name() << "\")";
    return out;
}

}
}

#endif // OBJECT_TPP
