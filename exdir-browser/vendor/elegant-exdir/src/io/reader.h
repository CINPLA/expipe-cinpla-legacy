#ifndef ELEGANT_EXDIR_READER_H
#define ELEGANT_EXDIR_READER_H

namespace elegant {
namespace exdir {

class Reader
{
public:
    virtual void read(void *buffer) = 0;
};

} // namespace
} // namespace

#endif // ELEGANT_EXDIR_READER_H
