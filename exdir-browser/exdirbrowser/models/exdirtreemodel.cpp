#include "exdirtreemodel.h"

#include <elegant-exdir/File>

#include <QDebug>

#include <QElapsedTimer>
#include <QFile>
#include <QFileInfo>
#include <QQmlFile>

using namespace elegant::exdir;

ExdirTreeModel::ExdirTreeModel(QObject *parent)
    : QAbstractItemModel(parent)
{
}

ExdirTreeModel::~ExdirTreeModel()
{
    if(m_root) {
        delete m_root;
    }
}

QModelIndex ExdirTreeModel::index(int row, int column, const QModelIndex &parent) const
{
    if(!hasIndex(row, column, parent)) {
        return QModelIndex();
    }

    const ExdirTreeItem* parentNode = nullptr;
    if(!parent.isValid()) {
        if(m_root == nullptr) {
            return QModelIndex();
        }
        parentNode = m_root;
    } else {
        parentNode = item(parent);
    }

    ExdirTreeItem* childItem = parentNode->child(row);
    if(childItem) {
        return createIndex(row, column, childItem);
    } else {
        return QModelIndex();
    }
}

QModelIndex ExdirTreeModel::parent(const QModelIndex &index) const
{
    if(!index.isValid()) {
        return QModelIndex();
    }

    ExdirTreeItem* childItem = item(index);
    ExdirTreeItem* parentItem = childItem->parentItem;

    if(parentItem == m_root) {
        return QModelIndex();
    }
    return createIndex(parentItem->row, 0, parentItem);
}

int ExdirTreeModel::rowCount(const QModelIndex &parent) const
{
    if(parent.column() > 0) {
        return 0;
    }
    if(!parent.isValid()) {
        if(m_root == nullptr) {
            return 0;
        }
        return m_root->children().count();
    }
    ExdirTreeItem* parentItem = item(parent);
    if(parentItem->needsChildIteration) {
        QString filePath = QQmlFile::urlToLocalFileOrQrc(m_source);
        File file(filePath.toStdString(), File::OpenMode::ReadWrite);
        Object object = file[parentItem->path().toStdString()];
        if(object.isGroup()) {
            Group group = object;
            addChildObjects(parentItem, group, parentItem->depth + 1);
        }
        parentItem->needsChildIteration = false;
    }
    return parentItem->children().count();;
}

int ExdirTreeModel::columnCount(const QModelIndex &parent) const
{
    if(parent.column() > 0) {
        return 0;
    }
    return 1;
}

QVariant ExdirTreeModel::data(const QModelIndex &index, int role) const
{
    if(!index.isValid()) {
        return QVariant();
    }
    ExdirTreeItem* indexNode = item(index);
    if(!indexNode) {
        return QVariant();
    }
    QString value;
    switch(role) {
    case int(Role::Name):
        value = indexNode->name();
        break;
    case int(Role::Path):
        value = indexNode->path();
        break;
    case int(Role::Type):
        value = indexNode->type();
        break;
    default:
        value = "";
        break;
    }
    return QVariant::fromValue(value);
}

QHash<int, QByteArray> ExdirTreeModel::roleNames() const
{
    QHash<int, QByteArray> roles;
    roles[int(Role::Name)] = "name";
    roles[int(Role::Path)] = "path";
    roles[int(Role::Type)] = "type";
    return roles;
}

QString ExdirTreeModel::path(const QModelIndex &index) const
{
    if(!index.isValid()) {
        return "";
    }
    ExdirTreeItem* indexNode = item(index);
    return indexNode->m_path;
}

ExdirTreeItem *ExdirTreeModel::item(const QModelIndex &index) const
{
    if(!index.isValid()) {
        return nullptr;
    }
    return static_cast<ExdirTreeItem*>(index.internalPointer());
}

QUrl ExdirTreeModel::source() const
{
    return m_source;
}

void ExdirTreeModel::setSource(QUrl source)
{
    if (m_source == source)
        return;

    m_source = source;
    loadFile();
    emit sourceChanged(source);
}

void ExdirTreeModel::addChildObjects(ExdirTreeItem* parent, const Group& parentGroup, int depth) const
{
    int row = 0;
    for(const std::string& key : parentGroup.keys()) {
        Object object = parentGroup[key];

        QString type = "";
        QString info = "";
        switch(object.type()) {
        case Object::Type::Attribute:
            type = "Attribute";
            break;
        case Object::Type::Dataset:
        {
            type = "Dataset";
            Dataset dataset = object;
            if(dataset.dimensionCount() == 1) {
                info = QString("vector of size %1").arg(dataset.extents()[0]);
            } else if(dataset.dimensionCount() == 2) {
                info = QString("%1x%2 matrix")
                        .arg(dataset.extents()[0])
                        .arg(dataset.extents()[1]);
            } else if(dataset.dimensionCount() == 3) {
                info = QString("%1x%2x%3 cube")
                        .arg(dataset.extents()[0])
                        .arg(dataset.extents()[1])
                        .arg(dataset.extents()[2]);
            } else {
                info = QString("%1 dimensional object").arg(dataset.dimensionCount());
            }
            break;
        }
        case Object::Type::Dataspace:
            type = "Dataspace";
            break;
        case Object::Type::Datatype:
            type = "Datatype";
            break;
        case Object::Type::File:
            type = "File";
            break;
        case Object::Type::Group:
        {
            type = "Group";
            Group group = object;
            info = QString("%1 objects").arg(group.keys().size());
            break;
        }
        default:
            qDebug() << "Got unknown type";
            type = "Unknown type";
            break;
        }

        ExdirTreeItem* node = new ExdirTreeItem(row, 0, depth + 1,
                                            QString::fromStdString(key),
                                            parent->m_path + "/" + QString::fromStdString(key),
                                            type,
                                            parent);
        node->setInfo(info);

        if(object.isGroup()) {
            node->needsChildIteration = true;
        }
        row += 1;
    }
}

void ExdirTreeModel::loadFile()
{
    QElapsedTimer timer;
    timer.start();
    qDebug() << "Loading tree";
    if(!m_source.isValid() || m_source.isEmpty()) {
        qDebug() << "Not loading because" << m_source;
        return;
    }
    QString filePath = QQmlFile::urlToLocalFileOrQrc(m_source);
    QString filenameOnly = filePath;
    QFileInfo fileInfo(filePath);
    if(fileInfo.exists()) {
        filenameOnly = fileInfo.fileName();
    }
    File file(filePath.toStdString(), File::OpenMode::ReadWrite);
    if(m_root) {
        delete m_root;
    }
    m_root = new ExdirTreeItem(0, 0, 0, "", "", "", 0);
    beginInsertRows(QModelIndex(), 0, 0);
    ExdirTreeItem *fileItem = new ExdirTreeItem(0, 0, 1, filenameOnly, "", "File", m_root);
    endInsertRows();
    addChildObjects(fileItem, file, 0);
    emit dataChanged(QModelIndex(), QModelIndex());

    qDebug() << "Done loading tree:" << timer.elapsed();
}

ExdirTreeItem::ExdirTreeItem() {}

ExdirTreeItem::ExdirTreeItem(int row_, int column_, int depth_, QString name_, QString path_, QString type, ExdirTreeItem *parent)
    : QObject(parent)
    , row(row_)
    , column(column_)
    , depth(depth_)
    , m_name(name_)
    , m_path(path_)
    , m_type(type)
    , parentItem(parent) {}

ExdirTreeItem::~ExdirTreeItem() {
    qDeleteAll(children());
}

ExdirTreeItem *ExdirTreeItem::child(int row) const {
    return static_cast<ExdirTreeItem*>(children().at(row));
}

QString ExdirTreeItem::name() const
{
    return m_name;
}

QString ExdirTreeItem::path() const
{
    return m_path;
}

QString ExdirTreeItem::type() const
{
    return m_type;
}

QString ExdirTreeItem::info() const
{
    return m_info;
}

void ExdirTreeItem::setName(QString name)
{
    if (m_name == name)
        return;

    m_name = name;
    emit nameChanged(name);
}

void ExdirTreeItem::setPath(QString path)
{
    if (m_path == path)
        return;

    m_path = path;
    emit pathChanged(path);
}

void ExdirTreeItem::setType(QString type)
{
    if (m_type == type)
        return;

    m_type = type;
    emit typeChanged(type);
}

void ExdirTreeItem::setInfo(QString info)
{
    if (m_info == info)
        return;

    m_info = info;
    emit infoChanged(info);
}
