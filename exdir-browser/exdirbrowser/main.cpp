#include <QApplication>
#include <QQmlApplicationEngine>

#include "models/exdirmodel.h"
#include "models/exdirtreemodel.h"
#include "models/exdirattributesmodel.h"
#include "views/matrixview.h"

#include <npy.h>
#include <armadillo>

int main(int argc, char *argv[])
{
    qmlRegisterType<ExdirDatasetModel>("H5Vis", 1, 0, "ExdirDatasetModel");
    qmlRegisterType<ExdirTreeModel>("H5Vis", 1, 0, "ExdirTreeModel");
    qmlRegisterType<ExdirAttributesModel>("H5Vis", 1, 0, "ExdirAttributesModel");
    qmlRegisterType<ExdirTreeItem>("H5Vis", 1, 0, "ExdirTreeItem");
    qmlRegisterType<MatrixView>("H5Vis", 1, 0, "MatrixView");

    QApplication app(argc, argv);

    QQmlApplicationEngine engine;
    engine.load(QUrl(QStringLiteral("qrc:/qml/main.qml")));

    return app.exec();
}
