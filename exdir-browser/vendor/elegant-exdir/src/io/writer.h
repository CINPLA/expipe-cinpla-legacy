#ifndef ELEGANT_EXDIR_WRITER_H
#define ELEGANT_EXDIR_WRITER_H

namespace elegant {
namespace exdir {

class Writer
{
public:
    virtual void write(const void *buffer) = 0;
};

} // namespace
} // namespace

#endif // WRITER_H
