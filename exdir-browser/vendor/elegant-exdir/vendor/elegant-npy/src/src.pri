CONFIG += c++14

LIBS += -lboost_regex

SOURCES += \
    $$PWD/writer.cpp \
    $$PWD/reader.cpp \
    $$PWD/common.cpp

HEADERS += \
    $$PWD/writer.h \
    $$PWD/reader.h \
    $$PWD/common.h \
    $$PWD/typehelper.h \
    $$PWD/typehelpers.h \
    $$PWD/npy.h
