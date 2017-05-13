#ifndef GROUP_H
#define GROUP_H

#include "utils/logging.h"
#include "attribute.h"
#include "dataset.h"
#include "object.h"

#include <string>

#include <vector>
#include <iostream>

namespace elegant {
namespace exdir {

class  Group : public Object
{
public:
    Group(ConversionFlags conversionFlags = ConversionFlags::NoFlags);
    Group(const Object &other);
    Group(const Group &other);

    ~Group();

    Group& operator=(const Object &other);
    Group& operator=(const Group &other);

    std::vector<std::string> keys() const;
    std::vector<Object> items();

    Object item(std::string key) const;
    Object operator[](std::string key) const;

    Group createGroup(std::string name);

    bool hasKey(std::string name) const;

private:
    Group(std::string name,
          boost::filesystem::path path,
          ConversionFlags conversionFlags);
};

#ifndef ELEGANT_EXDIR_NO_USER_DEFINED_CONVERSION_OPERATORS
template<>
inline Object::operator Group() const {
    return Group(*this);
}
#endif

}
}

#endif // GROUP_H
