#include "dataset.h"
#include "dataset_p.h"

#include <npy.h>
#include <iostream>
#include <boost/filesystem.hpp>

using namespace std;
namespace fs = boost::filesystem;

namespace elegant {
namespace exdir {


Dataset::Dataset()
    : Object(Type::Dataset)
{
}

Dataset::~Dataset()
{
    close();
}

vector<size_t> Dataset::extents() const
{
    fs::path filePath = path() / "data.npy";
    const auto& data = npy::load(filePath.string());
    return data.shape();
}

int Dataset::dimensionCount() const
{
    return extents().size();
}

Dataset::Dataset(string name, boost::filesystem::path path)
    : Object(name, path, Type::Dataset, m_inheritedConversionFlags)
{
}

Dataset::Dataset(const Object &other)
    : Object(Type::Dataset)
{
    constructFromOther(other);
}

Dataset::Dataset(const Dataset &other)
    : Object(Type::Dataset)
{
    constructFromOther(other);
}

Dataset& Dataset::operator=(const Object &other)
{
    if(!other.isDataset()) {
        DVLOG(1) << "ERROR: Cannot assign to Dataset with " << other;
        return *this;
    }
    Object::operator=(other);
    return *this;
}

Dataset& Dataset::operator=(const Dataset &other)
{
    Object::operator=(other);
    return *this;
}

Datatype::Type Dataset::datatype() const
{
    auto filePath = m_path / "data.npy";
    auto data = npy::load(filePath.string());
    auto numpyType = data.numpyType();
    if(numpyType == npy::NumpyType::Float) {
        return Datatype::Type::Float;
    } else if(numpyType == npy::NumpyType::Integer) {
        return Datatype::Type::Int;
    } else if(numpyType == npy::NumpyType::UnsignedInteger) {
        return Datatype::Type::Unknown;
    } else if(numpyType == npy::NumpyType::Byte) {
        return Datatype::Type::Int;
    }
    // TODO what about long and such?
    // TODO could we just return Numpy::Type and use those instead?
    return Datatype::Type::Unknown;
}

}
}
