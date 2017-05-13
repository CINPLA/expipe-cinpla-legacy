#include "reader.h"
#include "common.h"
#include <boost/regex.hpp>

using namespace boost;

using namespace std;

namespace elegant {
namespace npy {

Reader::Reader(string filename, Reader::Conversion conversionMode)
    : m_conversionMode(conversionMode)
{
    m_file.open(filename);

    int magicPrefixLength = magicPrefix.size();

    vector<char> magicBuffer(magicPrefixLength);
    m_file.read(&magicBuffer[0], magicBuffer.size());
    string resultingString(magicBuffer.begin(), magicBuffer.end());
    if(resultingString != magicPrefix) {
        cout << "Magic string: " << resultingString << endl;
        throw runtime_error("The magic string is not correct");
    }
    uint8_t majorVersion = 0;
    uint8_t minorVersion = 0;
    m_file.read(reinterpret_cast<char*>(&majorVersion), 1);
    m_file.read(reinterpret_cast<char*>(&minorVersion), 1);

    size_t headerLength = 0;
    if(majorVersion == 1 && minorVersion == 0) {
        uint16_t headerLength16 = 0;
        m_file.read(reinterpret_cast<char*>(&headerLength16), 2);
        headerLength = headerLength16;
    } else if(majorVersion == 2 && minorVersion == 0) {
        uint32_t headerLength32 = 0;
        m_file.read(reinterpret_cast<char*>(&headerLength32), 4);
        headerLength = headerLength32;
    }

    vector<char> headerBuffer(headerLength);
    m_file.read(&headerBuffer[0], headerLength);
    string header(headerBuffer.begin(), headerBuffer.end());

    // {'descr': '<i8', 'fortran_order': True, 'shape': (8,), }

    string::const_iterator start = header.begin();
    string::const_iterator end = header.end();

    // match parts on the form "'key': value,"
    smatch keyPairMatch;
    while(regex_search(start, end, keyPairMatch, regex("('(.*?)'\\s*?:\\s*((\\(.*?\\)|.*?)*?),)"))) {
        string key = keyPairMatch[2];
        string value = keyPairMatch[3];
        if(key == "descr") {
            smatch descrMatch;
            if(regex_search(value, descrMatch, regex("'(<|>|\\|)([a-zA-Z]+)([0-9]+)'"))) {
                string endian = descrMatch[1];
                string typeString = descrMatch[2];
                if(typeString == "f") {
                    m_numpyType = NumpyType::Float;
                } else if(typeString == "i") {
                    m_numpyType = NumpyType::Integer;
                } else if(typeString == "b") {
                    m_numpyType = NumpyType::Byte;
                } else if(typeString == "u") {
                    m_numpyType = NumpyType::UnsignedInteger;
                } else {
                    cerr << "Type: " << typeString << endl;
                    throw std::runtime_error("Type not implemented");
                }
                m_byteCount = stoi(descrMatch[3]);
                if(endian == ">") {
                    throw runtime_error("Big endian not supported");
                }
            }
        }
        if(key == "fortran_order") {
            if(value == "False") {
                m_isFortranOrder = false;
            } else {
                m_isFortranOrder = true;
            }
        }
        if(key == "shape") {
            smatch shapeMatch;
            string::const_iterator shapeStart = value.begin();
            string::const_iterator shapeEnd = value.end();
            while(regex_search(shapeStart, shapeEnd, shapeMatch, regex("([0-9]+?)(?:\\s*(?:,|\\)))"))) {
                string shapeValue = shapeMatch[1];
                m_shape.push_back(stoi(shapeValue));
                shapeStart = shapeMatch[0].second;
            }
        }
        start = keyPairMatch[0].second; // move on to the next match
    }
}

bool Reader::isFortranOrder() const
{
    return m_isFortranOrder;
}

bool Reader::read(char *buffer, size_t byteCount) {
    m_file.read(buffer, byteCount);
    return true; // TODO check if read ok
}

std::vector<size_t> Reader::shape() const
{
    return m_shape;
}

NumpyType Reader::numpyType() const
{
    return m_numpyType;
}

std::ostream &operator<<(std::ostream &out, const Reader &array) {
    out << "Numpy array (dtype: '[TODO]', "
        << "fortranOrder: " << array.m_isFortranOrder << ", "
        << "shape: (";
    for(size_t dim : array.m_shape) {
        out << dim << ", ";
    }
    out << "))";
    return out;
}

}
}
