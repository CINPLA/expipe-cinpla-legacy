#include "file.h"
#include "utils/logging.h"
#include "utils/errorhelper.h"


#include <iostream>
#include <fstream>
#include <boost/filesystem.hpp>

using namespace std;

namespace elegant {
namespace exdir {


File::File(string folderName, File::OpenMode mode, ConversionFlags conversionFlags)
    : Group(conversionFlags)
    , m_fileName(folderName)
{
    m_path = folderName;
    m_type = Type::File;
    bool alreadyExists = boost::filesystem::exists(folderName);
    if (alreadyExists) {
        // TODO check if valid object folder and proper meta.yml
    }
    bool shouldCreateFolder = false;

    if (mode == File::OpenMode::ReadOnly) {
        if(!alreadyExists) {
            throw std::runtime_error("Folder does not exist.");
        }
    } else if(mode == File::OpenMode::Truncate) {
        if(alreadyExists) {
            throw std::runtime_error("Truncation not yet implemented.");
        }
        shouldCreateFolder = true;
    } else if(mode == File::OpenMode::ReadWrite) {
        if(!alreadyExists) {
            shouldCreateFolder = true;
        }
    }
    if(shouldCreateFolder) {
        throw std::runtime_error("Creating folder not yet implemented.");
    }
}

File::~File()
{
    close();
}

void File::close()
{
    // TODO
}

}
}
