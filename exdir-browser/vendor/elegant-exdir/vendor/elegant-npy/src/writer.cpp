#include "writer.h"
#include "typehelper.h"
#include "common.h"

#include <sstream>
#include <fstream>

using namespace std;

namespace elegant {
namespace npy {

Writer::Writer(std::string filename, size_t elementSize, const std::type_info& typeInfo)
    : m_filename(filename)
    , m_elementSize(elementSize)
    , m_typeInfo(typeInfo)
{
}

bool Writer::write(const char *buffer, std::vector<size_t> shape) {
    stringstream header;
    header << "{'descr': '<";
    // TODO test and write correct endian
    if(false) {}
    else if(m_typeInfo == typeid(bool)) { header << "b"; }
    else if(m_typeInfo == typeid(int8_t)) { header << "i"; }
    else if(m_typeInfo == typeid(int16_t)) { header << "i"; }
    else if(m_typeInfo == typeid(int32_t)) { header << "i"; }
    else if(m_typeInfo == typeid(int64_t)) { header << "i"; }
    else if(m_typeInfo == typeid(uint8_t)) { header << "u"; }
    else if(m_typeInfo == typeid(uint16_t)) { header << "u"; }
    else if(m_typeInfo == typeid(uint32_t)) { header << "u"; }
    else if(m_typeInfo == typeid(uint64_t)) { header << "u"; }
    else if(m_typeInfo == typeid(float)) { header << "f"; }
    else if(m_typeInfo == typeid(double)) { header << "f"; }
    else if(m_typeInfo == typeid(long double)) { header << "f"; }
    else {
        throw std::runtime_error("Type is not supported");
    }

    header << m_elementSize;
    header << "', 'fortran_order': ";
    if(m_fortranOrder) {
        header << "True";
    } else {
        header << "False";
    }
    header << ", 'shape': (";
    bool first = true;
    for(size_t dim : shape) {
        if(!first) {
            header << ",";
        }
        header << dim;
        first = false;
    }
    header << "), }";
    // TODO add padding

    ofstream file(m_filename);
    file << magicPrefix;
    int majorVersion = 1;
    int minorVersion = 0;
    file.write(reinterpret_cast<char*>(&majorVersion), 1);
    file.write(reinterpret_cast<char*>(&minorVersion), 1);
    uint16_t headerSize = header.str().size();
    file.write(reinterpret_cast<char*>(&headerSize), 2);
    file << header.str();
    file.write(buffer, elementCount(shape) * m_elementSize);

    return true; // TODO check if write ok
}

bool Writer::fortranOrder() const
{
    return m_fortranOrder;
}

void Writer::setFortranOrder(bool fortranOrder)
{
    m_fortranOrder = fortranOrder;
}

}
}
