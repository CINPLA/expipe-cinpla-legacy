#ifndef H5CPP_ATTRIBUTE_H
#define H5CPP_ATTRIBUTE_H

#include "io/typehelper.h"
#include "utils/logging.h"
#include "utils/demangle.h"
#include "object.h"
#include "datatype.h"

#include <ostream>
#include <string>
#include <iostream>
#include <sstream>
#include <typeinfo>
#include <boost/filesystem.hpp>

namespace elegant {
namespace exdir {


class AttributeReader : public Reader
{
public:
    AttributeReader();
    virtual void read(void *buffer);
private:
};

class AttributeWriter : public Writer
{
public:
    AttributeWriter();
    virtual void write(const void *buffer);
private:
};

class Attribute
{
public:
    Attribute();
    Attribute(boost::filesystem::path path,
              const std::string &name,
              Object::ConversionFlags inheritedFlags);
    Attribute(const Attribute &other);
    Attribute& operator=(const Attribute &other);
    Attribute& operator=(const std::string &value);
    Attribute& operator=(const char* object);
    ~Attribute();

    template<typename T>
    void operator=(const T &other);


    bool isValid() const;
    bool isNonExistingNamed() const;

    std::string name() const;
    boost::filesystem::path path() const;
    void close();

    // dataspace properties
    bool isScalar() const;
    bool isSimple() const;
    int dimensionCount() const;
    std::vector<size_t> extents() const;
    Datatype::Type datatype() const;

    template<typename T>
    T value(Object::ConversionFlags mode = Object::ConversionFlags::InheritedFlags) const;

    std::string toString() const;

#ifndef ELEGANT_EXDIR_NO_USER_DEFINED_CONVERSION_OPERATORS
    template<typename T>
    operator T() const;

    operator std::string() const;
#endif

    friend std::ostream& operator<<(std::ostream&, const Attribute&);

private:
    void constructFromOther(const Attribute &other);

    boost::filesystem::path m_path;
    std::string m_name;
    Object* m_parent = nullptr;
    Object::ConversionFlags m_inheritedConversionFlags = Object::ConversionFlags::NoFlags;
};

} // namespace
} // namespace

#include "attribute.tpp"

#endif // H5CPP_ATTRIBUTE_H
