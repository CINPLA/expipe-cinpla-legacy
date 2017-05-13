include($$PWD/../vendor/elegant-npy/elegant-npy.pri)

HEADERS += \
    $$PWD/attribute.h \
    $$PWD/dataset.h \
    $$PWD/datatype.h \
    $$PWD/object.h \
    $$PWD/dataset_p.h \
    $$PWD/file.h \
    $$PWD/group.h \
    $$PWD/converters/armadillo-converters.h \
    $$PWD/converters/native-converters.h \
    $$PWD/converters/std-converters.h \
    $$PWD/io/reader.h \
    $$PWD/io/typehelper.h \
    $$PWD/io/writer.h \
    $$PWD/utils/demangle.h \
    $$PWD/utils/errorhelper.h \
    $$PWD/utils/logging.h

SOURCES += \
    $$PWD/object.cpp \
    $$PWD/attribute.cpp \
    $$PWD/attribute.tpp \
    $$PWD/dataset.cpp \
    $$PWD/dataset.tpp \
    $$PWD/errorhelper.cpp \
    $$PWD/file.cpp \
    $$PWD/group.cpp \
    $$PWD/object.tpp \
    $$PWD/datatype.cpp
