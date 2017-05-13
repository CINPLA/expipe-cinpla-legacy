#ifndef ELEGANT_EXDIR_FILE_H
#define ELEGANT_EXDIR_FILE_H

#include "utils/logging.h"
#include "group.h"

#include <string>

#include <vector>


namespace elegant {
namespace exdir {

class File : public Group
{
public:
    enum class OpenMode {
        ReadOnly,
        ReadWrite,
        Truncate
    };

    File(std::string fileName,
         File::OpenMode mode = File::OpenMode::ReadWrite,
         File::ConversionFlags conversionFlags = ConversionFlags::NoFlags);
    virtual ~File();

    void close();

private:
    std::string m_fileName; // TODO remove?
};

} // namespace
} // namespace

#endif // ELEGANT_EXDIR_FILE_H
