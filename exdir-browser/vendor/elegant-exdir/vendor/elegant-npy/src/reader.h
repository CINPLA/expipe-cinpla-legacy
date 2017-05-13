#ifndef ELEGANT_NPY_READER_H
#define ELEGANT_NPY_READER_H

#include <iostream>
#include <string>
#include <vector>
#include <fstream>
#include <sstream>

#include "typehelper.h"
#include "common.h"

namespace elegant {
namespace npy {

class Reader
{
public:
    enum class Conversion {
        AllowLossy,
        RequireSame
    };

    Reader(std::string filename, Conversion conversionMode = Conversion::AllowLossy);

    template<typename T>
    operator T();

    template<typename T>
    T value();

    template<typename T, typename U>
    T valueFromTypeHelper();

    friend std::ostream& operator<<(std::ostream &out, const Reader &array);

    bool isFortranOrder() const;

    bool read(char* buffer, size_t byteCount);

    std::vector<size_t> shape() const;
    NumpyType numpyType() const;

private:
    std::string m_numpyPrecision;

    NumpyType m_numpyType;

    std::vector<size_t> m_shape;
    std::vector<char> m_data;
    size_t m_byteCount = 0;
    std::ifstream m_file;
    bool m_isFortranOrder = false;
    Conversion m_conversionMode = Conversion::AllowLossy;
};

std::ostream &operator<<(std::ostream& out, const Reader& array);

template<typename T, typename U>
T Reader::valueFromTypeHelper()
{
    TypeHelper<T, U> typeHelper;
    if(!typeHelper.isLossyConvertible()) {
        std::stringstream error;
        error << "Cannot convert from numpy type. "
              << "The current conversion policy would allow it, but there is no known conversion available.";
        throw std::runtime_error(error.str());
    } else if(m_conversionMode == Conversion::RequireSame && !typeHelper.isSame()) {
        std::stringstream error;
        error << "Cannot convert from numpy type. "
              << "The current conversion policy requires equal types.";
        throw std::runtime_error(error.str());
    }
    return typeHelper.fromFile(m_shape, *this);
}

template<typename T>
T Reader::value()
{
    if(false) {
    } else if(m_numpyType == NumpyType::Byte) {
        return valueFromTypeHelper<T, bool>();
    } else if(m_numpyType == NumpyType::Float && m_byteCount == 4) {
        return valueFromTypeHelper<T, float>();
    } else if(m_numpyType == NumpyType::Float && m_byteCount == 8) {
        return valueFromTypeHelper<T, double>();
    } else if(m_numpyType == NumpyType::Integer && m_byteCount == 1) {
        return valueFromTypeHelper<T, int8_t>();
    } else if(m_numpyType == NumpyType::Integer && m_byteCount == 2) {
        return valueFromTypeHelper<T, int16_t>();
    } else if(m_numpyType == NumpyType::Integer && m_byteCount == 4) {
        return valueFromTypeHelper<T, int32_t>();
    } else if(m_numpyType == NumpyType::Integer && m_byteCount == 8) {
        return valueFromTypeHelper<T, int64_t>();
    } else if(m_numpyType == NumpyType::UnsignedInteger && m_byteCount == 1) {
        return valueFromTypeHelper<T, uint8_t>();
    } else if(m_numpyType == NumpyType::UnsignedInteger && m_byteCount == 2) {
        return valueFromTypeHelper<T, uint16_t>();
    } else if(m_numpyType == NumpyType::UnsignedInteger && m_byteCount == 4) {
        return valueFromTypeHelper<T, uint32_t>();
    } else if(m_numpyType == NumpyType::UnsignedInteger && m_byteCount == 8) {
        return valueFromTypeHelper<T, uint64_t>(); }
    else {
        std::stringstream error;
        error << "Unknown NumPy type." << std::endl;
        throw std::runtime_error(error.str());
    }
}

template<typename T>
Reader::operator T()
{
    return value<T>();
}

}
}

#endif // ELEGANT_NPY_READER_H
