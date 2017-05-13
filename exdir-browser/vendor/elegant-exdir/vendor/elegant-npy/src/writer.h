#ifndef ELEGANT_NPY_WRITER_H
#define ELEGANT_NPY_WRITER_H

#include <string>
#include <vector>

namespace elegant {
namespace npy {

class Writer
{
public:
    Writer(std::string filename, size_t elementSize, const std::type_info &typeInfo);

    bool write(const char* buffer, std::vector<size_t> shape);

    bool fortranOrder() const;
    void setFortranOrder(bool fortranOrder);

private:
    bool m_fortranOrder = false;
    std::string m_filename;
    size_t m_elementSize;
    const std::type_info& m_typeInfo;
};

}
}

#endif // ELEGANT_NPY_WRITER_H
