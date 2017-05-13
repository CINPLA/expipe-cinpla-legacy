#ifndef ELEGANT_EXDIR_DATATYPE_H
#define ELEGANT_EXDIR_DATATYPE_H


namespace elegant {
namespace exdir {

class Datatype
{
public:
    Datatype();

    enum class Type {
        Unknown = -1,
        Int,
        Long,
        Float,
        Double,
        String
    };

    Datatype(Type type);

    Type type() const;

private:
    Type m_type = Type::Unknown;
};

} // exdir
} // elegant

#endif // ELEGANT_EXDIR_DATATYPE_H
