#ifndef DATASET_TPP
#define DATASET_TPP

#include "dataset.h"
#include "dataset_p.h"
#include <npy.h>

namespace elegant {
namespace exdir {

#ifndef ELEGANT_EXDIR_NO_USER_DEFINED_CONVERSION_OPERATORS
template<>
inline Object::operator Dataset() const {
    return Dataset(*this);
}
#endif

template<typename T>
inline void Object::operator=(const T& matrix)
{
    Dataset dataset = *this;
    dataset = matrix;
}

template<typename T>
Dataset& Dataset::operator=(const T &object)
{
    // TODO
    throw std::runtime_error("Not implemented");
}

template<typename T>
Dataset Dataset::create(Object *parent, const std::string &name, const T &data)
{
    // TODO
    throw std::runtime_error("Not implemented");
}

template<typename T>
T Object::value(ConversionFlags mode) const
{
    if(type() != Type::Dataset) {
        std::stringstream errorStream;
        errorStream << "Tried to convert non-dataset object to " << demangle(typeid(T).name());
        throw std::runtime_error(errorStream.str());
    }
    Dataset dataset = *this;
    return dataset.valueImpl<T>(mode);
}

// TODO Does this lead to a costly copy? If so, the implementation needs to be changed.
template<typename T>
inline T Dataset::valueImpl(ConversionFlags mode) const
{
    auto filePath = path() / "data.npy";
    auto data = npy::load(filePath.string());
    return data.value<T>();
}

} // namespace
} // namespace

#endif // DATASET_TPP
