#ifndef EXDIRATTRIBUTESMODEL_H
#define EXDIRATTRIBUTESMODEL_H

#include <QAbstractTableModel>
#include <QObject>
#include <QUrl>

#include <armadillo>

class ExdirAttributesModel : public QAbstractTableModel
{
    Q_OBJECT
    Q_PROPERTY(QUrl source READ source WRITE setSource NOTIFY sourceChanged)
    Q_PROPERTY(QString path READ path WRITE setPath NOTIFY pathChanged)
    Q_PROPERTY(bool hasUnsavedChanges READ hasUnsavedChanges NOTIFY hasUnsavedChangesChanged)
    Q_PROPERTY(int count READ count WRITE setCount NOTIFY countChanged)

public:
    ExdirAttributesModel(QObject *parent = 0);

    enum class Role {
        Name = Qt::UserRole + 0,
        Value = Qt::UserRole + 1
    };

    virtual int rowCount(const QModelIndex &parent = QModelIndex()) const override;
    virtual int columnCount(const QModelIndex &parent = QModelIndex()) const override;
    virtual QVariant data(const QModelIndex &index, int role) const override;
    virtual bool setData(const QModelIndex &index, const QVariant &value, int role) override;
    virtual QHash<int, QByteArray> roleNames() const;
    QString path() const;
    QUrl source() const;

    bool inBounds(const QModelIndex &index) const;
    bool hasUnsavedChanges() const;

    int count() const;

public slots:
    void setPath(QString path);
    void setSource(QUrl source);
    bool save();

    void setCount(int count);

signals:
    void pathChanged(QString path);
    void sourceChanged(QUrl source);
    void hasUnsavedChangesChanged(bool hasUnsavedChanges);

    void countChanged(int count);

private:
    void load();

    QString m_path;
    QUrl m_source;
    QVariantMap m_data;

    bool m_hasUnsavedChanges;
    QString vectorToString(std::vector<auto> vec);
    int m_count = 0;
};

#endif // EXDIRATTRIBUTESMODEL_H
