#include "exdirattributesmodel.h"

//#include "exdirmodel.h"

#include <QDebug>
#include <QStringBuilder>
#include <QQmlFile>
#include <QUrl>

#include <iostream>

#include <npy.h>

#include <elegant-exdir/Attribute>
#include <elegant-exdir/File>

using namespace std;
using namespace arma;
using namespace elegant::exdir;

ExdirAttributesModel::ExdirAttributesModel(QObject* parent) : QAbstractTableModel(parent)
{

}

int ExdirAttributesModel::rowCount(const QModelIndex &parent) const
{
    Q_UNUSED(parent);
    return m_data.count();
}

int ExdirAttributesModel::columnCount(const QModelIndex &parent) const
{
    Q_UNUSED(parent);
    return 1;
}

bool ExdirAttributesModel::inBounds(const QModelIndex &index) const
{
    if(index.row() >= 0
            && index.column() >= 0
            && index.column() < 1
            && index.row() < m_data.count()) {
        return true;
    }
    return false;
}

bool ExdirAttributesModel::hasUnsavedChanges() const
{
    return m_hasUnsavedChanges;
}

int ExdirAttributesModel::count() const
{
    return m_count;
}

QVariant ExdirAttributesModel::data(const QModelIndex &index, int role) const
{
    if(!inBounds(index)) {
        return QVariant();
    }
    if(role == int(Role::Name)) {
        return m_data.keys().at(index.row());
    }
    if(role == int(Role::Value)) {
        return m_data.values().at(index.row());
    }
    return QVariant();
}


bool ExdirAttributesModel::setData(const QModelIndex &index, const QVariant &value, int role)
{
    (void)role;
    if(!index.isValid()) {
        return false;
    }
    if(!inBounds((index))) {
        return false;
    }
    if(!value.canConvert<double>()) {
        return false;
    }
    double doubleValue = value.toDouble();
    m_data[m_data.keys().at(index.row())] = doubleValue;
    m_hasUnsavedChanges = true;
    emit dataChanged(index, index);
    emit hasUnsavedChangesChanged(m_hasUnsavedChanges);
    return true;
}

QHash<int, QByteArray> ExdirAttributesModel::roleNames() const
{
    QHash<int, QByteArray> roles;
    roles[int(Role::Name)] = "name";
    roles[int(Role::Value)] = "value";
    return roles;
}

QString ExdirAttributesModel::path() const
{
    return m_path;
}

QUrl ExdirAttributesModel::source() const
{
    return m_source;
}

void ExdirAttributesModel::setPath(QString dataSet)
{
    if (m_path == dataSet)
        return;

    m_path = dataSet;
    load();
    emit pathChanged(dataSet);
}

void ExdirAttributesModel::setSource(QUrl source)
{
    if (m_source == source)
        return;

    m_source = source;
    load();
    emit sourceChanged(source);
}

QString ExdirAttributesModel::vectorToString(vector<auto> vec)
{
    QString string = "[";
    bool first = true;
    for(const auto &val : vec) {
        if(!first) {
            string += ", ";
        }
        string += QString::number(val);
        first = false;
    }
    string += "]";
    return string;
}

template<typename T>
QVariant vectorAttributeToQVariant(const Attribute& attribute)
{
    return QVariant::fromValue(QVector<T>::fromStdVector(attribute.value<vector<T>>()).toList());
}

void ExdirAttributesModel::load()
{
    if(!m_source.isValid() || m_path.isEmpty()) {
        beginRemoveRows(QModelIndex(), 0, m_data.values().count());
        m_data.clear();
        endRemoveRows();
        emit dataChanged(QModelIndex(), QModelIndex());
        return;
    }

    QString fileNameString = QQmlFile::urlToLocalFileOrQrc(m_source);
    std::string path = m_path.toStdString();
    File file(fileNameString.toStdString(), File::OpenMode::ReadWrite);

    beginRemoveRows(QModelIndex(), 0, m_data.count() - 1);
    m_data.clear();
    endRemoveRows();
    Object object = file[path];
    beginInsertRows(QModelIndex(), 0, object.attributes().size() - 1);
    for(const Attribute &attribute : object.attributes()) {
        QString key = QString::fromStdString(attribute.name());
        m_data[key] = "N/A";
        if(attribute.isScalar()) {
            switch(attribute.datatype()) {
            case Datatype::Type::Int:
                m_data[key] = QVariant::fromValue(attribute.value<int>());
                break;
            case Datatype::Type::Long:
                m_data[key] = QVariant::fromValue(attribute.value<long int>());
                break;
            case Datatype::Type::Float:
                m_data[key] = QVariant::fromValue(attribute.value<double>());
                break;
            case Datatype::Type::Double:
                m_data[key] = QVariant::fromValue(attribute.value<double>());
                break;
            case Datatype::Type::String:
                m_data[key] = QString::fromStdString(attribute.value<std::string>());
                break;
            default:
                break;
            }
        } else if(attribute.isSimple()) {
            if(attribute.dimensionCount() > 1) {
                if(attribute.dimensionCount() == 2) {
                    m_data[key] = QString("%1 x %2 matrix")
                            .arg(attribute.extents()[0])
                            .arg(attribute.extents()[1]);
                } else if(attribute.dimensionCount() == 2) {
                    m_data[key] = QString("%1 x %2 x %3 cube")
                            .arg(attribute.extents()[0])
                            .arg(attribute.extents()[1])
                            .arg(attribute.extents()[2]);
                } else {
                    m_data[key] = QString("%1 dimensional object").arg(attribute.dimensionCount());
                }
            } else {
                switch(attribute.datatype()) {
                case Datatype::Type::Int:
                    m_data[key] = vectorAttributeToQVariant<int>(attribute);
                    break;
                case Datatype::Type::Long:
                    m_data[key] = vectorAttributeToQVariant<long int>(attribute);
                    break;
                case Datatype::Type::Float:
                    m_data[key] = vectorAttributeToQVariant<float>(attribute);
                    break;
                case Datatype::Type::Double:
                    m_data[key] = vectorAttributeToQVariant<double>(attribute);
                    break;
                default:
                    break;
                }
            }
        }
        // TODO add more datatypes
    }
    endInsertRows();
    setCount(m_data.count());
    m_hasUnsavedChanges = false;
    emit dataChanged(QModelIndex(), QModelIndex());
    emit hasUnsavedChangesChanged(m_hasUnsavedChanges);
}

bool ExdirAttributesModel::save()
{
    // TODO keep working on the same file when loading/saving

//    qDebug() << "Saving file";
//    if(!m_source.isValid() || m_path.isEmpty()) {
//        return false;
//    }
//    QString fileNameString = QQmlFile::urlToLocalFileOrQrc(m_source);
//    std::string datasetName = m_path.toStdString();
//    qDebug() << "Loading" << m_path << "in" << fileNameString;
//    File file(fileNameString.toStdString(), h5cpp::File::OpenMode::ReadWrite);

//    qDebug() << file[datasetName].isDataset();
//    if(file[datasetName].isDataset()) {
//        file[m_path.toStdString()] = m_data;
//    }
//    m_hasUnsavedChanges = false;
//    emit hasUnsavedChangesChanged(m_hasUnsavedChanges);
    return true;
}

void ExdirAttributesModel::setCount(int count)
{
    if (m_count == count)
        return;

    m_count = count;
    emit countChanged(count);
}
