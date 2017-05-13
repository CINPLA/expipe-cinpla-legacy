#ifndef TYPEHELPER
#define TYPEHELPER

#include <vector>
#include <functional>

namespace elegant {
namespace npy {

//using FromFileCallback = std::function<void(char* buffer, size_t byteCount)>;
//using ToFileCallback = std::function<void(const char* buffer, std::vector<size_t> shape, bool fortranOrder)>;

class Writer;
class Reader;

template<typename T, typename U>
struct BaseTypeHelper
{
    using ObjectType = T;
    using ElementType = T;
    ObjectType fromFile(const std::vector<size_t> &shape, Reader &reader) {
        (void)(shape);
        (void)(reader);
        throw std::runtime_error("Conversion to this type is not supported");
    }
    void toFile(const ObjectType& object, Writer &writer) {
        (void)(object);
        (void)(writer);
        throw std::runtime_error("Saving of this type is not supported");
    }
    bool isSame() {
        throw std::runtime_error("This type lacks comparison information");
    }
    bool isLossyConvertible() {
        throw std::runtime_error("This type lacks comparison information");
    }
    std::vector<size_t> shape(const T& object) {
        (void)object;
        throw std::runtime_error("Saving this type is not supported");
    }
};

template<typename T, typename U>
struct TypeHelper : public BaseTypeHelper<T, U>
{
};

}
}

#endif // TYPEHELPER

