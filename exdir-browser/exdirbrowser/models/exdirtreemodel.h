#ifndef EXDIRTREEMODEL_H
#define EXDIRTREEMODEL_H

#include <QAbstractTableModel>
#include <QUrl>
#include <npy.h>

#include <elegant-exdir/Group>

class ExdirTreeItem : public QObject
{
    Q_OBJECT
    Q_PROPERTY(QString name READ name WRITE setName NOTIFY nameChanged)
    Q_PROPERTY(QString path READ path WRITE setPath NOTIFY pathChanged)
    Q_PROPERTY(QString type READ type WRITE setType NOTIFY typeChanged)
    Q_PROPERTY(QString info READ info WRITE setInfo NOTIFY infoChanged)

    QString m_info;

public:
    ExdirTreeItem();
    ExdirTreeItem(int row_, int column_, int depth_, QString name_, QString path_, QString type, ExdirTreeItem* parent);

    ~ExdirTreeItem();

    ExdirTreeItem* child(int row) const;

    int row = 0;
    int column = 0;
    int depth = 0;
    bool needsChildIteration = false;
    QString m_name;
    QString m_path;
    QString m_type;
    ExdirTreeItem* parentItem = nullptr;
    QString name() const;
    QString path() const;
    QString type() const;
    QString info() const;

public slots:
    void setName(QString name);
    void setPath(QString path);
    void setType(QString type);

    void setInfo(QString info);

signals:
    void nameChanged(QString name);
    void pathChanged(QString path);
    void typeChanged(QString type);
    void infoChanged(QString info);
};

class ExdirTreeModel : public QAbstractItemModel
{
    Q_OBJECT
    Q_ENUMS(Role)
    Q_PROPERTY(QUrl source READ source WRITE setSource NOTIFY sourceChanged)

public:
    explicit ExdirTreeModel(QObject *parent = 0);
    ~ExdirTreeModel();

    enum class Role {
        Name = Qt::UserRole + 0,
        Path = Qt::UserRole + 1,
        Type = Qt::UserRole + 2
    };

    // QAbstractItemModel interface
public:
    virtual QModelIndex index(int row, int column, const QModelIndex &parent) const override;
    virtual QModelIndex parent(const QModelIndex &child) const override;
    virtual int rowCount(const QModelIndex &parent) const override;
    virtual int columnCount(const QModelIndex &parent) const override;
    virtual QVariant data(const QModelIndex &index, int role) const override;
    virtual QHash<int, QByteArray> roleNames() const override;
    Q_INVOKABLE QString path(const QModelIndex &index) const;
    Q_INVOKABLE ExdirTreeItem* item(const QModelIndex& index) const;
    QUrl source() const;
public slots:
    void setSource(QUrl source);
    void loadFile();
signals:
    void sourceChanged(QUrl source);

private:
    ExdirTreeItem* m_root = nullptr;
    QUrl m_source;
    void addChildObjects(ExdirTreeItem *item, const elegant::exdir::Group &group, int depth) const;
};

#endif // EXDIRTREEMODEL_H
