#ifndef ATTRIBUTE_TPP
#define ATTRIBUTE_TPP

#include "attribute.h"

namespace elegant {
namespace exdir {

#ifndef ELEGANT_EXDIR_NO_USER_DEFINED_CONVERSION_OPERATORS
template<typename T>
Attribute::operator T() const
{
    return value<T>();
}

inline Attribute::operator std::string() const
{
    return toString();
}
#endif

template<>
inline std::string Attribute::value<std::string>(Object::ConversionFlags mode) const
{
    (void)mode;
    return toString();
}

template<typename T>
T Attribute::value(Object::ConversionFlags mode) const
{
    if(mode == Object::ConversionFlags::InheritedFlags) {
        mode = m_inheritedConversionFlags;
    }
    // TODO
}

template<typename T>
void Attribute::operator=(const T &object)
{
    // TODO
}

template<typename T>
inline T& operator<<(T &other, const elegant::exdir::Attribute &attribute)
{
    other = attribute.value<T>();
    return other;
}

template<typename T>
inline T& operator>>(const elegant::exdir::Attribute &attribute, T &other)
{
    other = attribute.value<T>();
    return other;
}

inline std::ostream& operator<< (std::ostream &out, const elegant::exdir::Attribute &attribute)
{
    // TODO
    return out;
}

} // namespace
} // namespace

#endif // ATTRIBUTE_TPP
