#ifndef DATASET_H
#define DATASET_H

#include "object.h"
#include "io/typehelper.h"
#include "utils/logging.h"
#include "utils/demangle.h"
#include "datatype.h"
//#include "converters/native-converters.h"
//#include "converters/std-converters.h"

//#ifndef H5CPP_NO_ARMA
//#include "converters/armadillo-converters.h"
//#endif

#include <iostream>
#include <typeinfo>

namespace elegant {
namespace exdir {

class Dataset : public Object
{
public:
    Dataset();
    Dataset(std::string name, boost::filesystem::path path);

    Dataset(const Object &other);
    Dataset(const Dataset &other);

    ~Dataset();

    Dataset& operator=(const Object &other);
    Dataset& operator=(const Dataset &other);

    template<typename T>
    Dataset& operator=(const T &data);

    Datatype::Type datatype() const;

    bool isScalar() const;
    bool isSimple() const;
    int dimensionCount() const;
    std::vector<size_t> extents() const;

    template<typename T>
    static Dataset create(Object *parent, const std::string &name, const T &data);

private:
    template<typename T>
    T valueImpl(Object::ConversionFlags mode) const;

    friend class Object;
    friend class DatasetWriter;
};

}
}

#include "dataset.tpp"

#endif // DATASET_H
