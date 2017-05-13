#include "datatype.h"


namespace elegant {
namespace exdir {

Datatype::Datatype()
{

}

Datatype::Datatype(Datatype::Type type)
    : m_type(type)
{

}

Datatype::Type Datatype::type() const
{
    return m_type;
}

} // exdir
} // elegant
