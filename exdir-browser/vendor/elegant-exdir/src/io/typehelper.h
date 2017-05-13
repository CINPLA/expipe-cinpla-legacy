#ifndef ELEGANT_EXDIR_UTILS_H
#define ELEGANT_EXDIR_UTILS_H

#include "../utils/logging.h"
#include "../io/reader.h"
#include "../io/writer.h"


#include <string>
#include <type_traits>
#include <vector>

namespace elegant {
namespace exdir {

class Dataset;

template<typename T>
struct SimpleTypeHelper
{
    using ObjectType = T;
    static int dimensionCount() {
        return 0;
    }
    static std::vector<size_t> extents(const ObjectType &object) {
        (void)object;
        return std::vector<size_t>();
    }
    ObjectType readFromFile(const std::vector<size_t> &extents, Reader &reader) {
        (void)extents;
        ObjectType object;
        reader.read(&object);
        return object;
    }
    void writeToFile(const ObjectType &object, Writer& writer) {
        writer.write(&object);
    }
};

template<typename T>
struct TypeHelper : public SimpleTypeHelper<T>
{
    // IMPORTANT: This function is deleted because it must be explicitly implemented for each type used.
    // If not, errors would not appear before compile time because the EXDIR type is not given.
//    static hid_t hdfType() {
//        static_assert(false, "ERROR: hdfType not implemented for this type.");
//    }
//    static hid_t hdfType() = delete;
};

}
}

#endif // ELEGANT_EXDIR_UTILS_H
