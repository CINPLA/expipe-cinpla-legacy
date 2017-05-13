TEMPLATE = app

QT += qml quick widgets gui
CONFIG += c++14

CONFIG += c++11
LIBS += -lboost_system -lboost_filesystem -lyaml-cpp

RESOURCES += qml.qrc

# Additional import path used to resolve QML modules in Qt Creator's code model
QML_IMPORT_PATH =

# Default rules for deployment.
qnx: target.path = /tmp/$${TARGET}/bin
else: unix:!android: target.path = /opt/$${TARGET}/bin
!isEmpty(target.path): INSTALLS += target

HEADERS += \
    models/exdirattributesmodel.h \
    models/exdirmodel.h \
    models/exdirtreemodel.h \
    views/matrixview.h \
    treemodel.h

SOURCES += \
    main.cpp \
    models/exdirattributesmodel.cpp \
    models/exdirmodel.cpp \
    models/exdirtreemodel.cpp \
    views/matrixview.cpp \
    treemodel.cpp

#CONFIG += conan_basic_setup
#include(conanbuildinfo.pri)
include(../vendor/elegant-exdir/elegant-exdir.pri)

DISTFILES += \
    conanfile.py \
    conanfile.txt
