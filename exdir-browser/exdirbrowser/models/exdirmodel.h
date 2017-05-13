#ifndef EXDIRMODEL_H
#define EXDIRMODEL_H

#include <elegant-exdir/Datatype>
#include <elegant-exdir/Dataset>

#include <QAbstractTableModel>
#include <QObject>
#include <QUrl>

#include <boost/variant.hpp>
#include <armadillo>

class ExdirDatasetModel : public QAbstractTableModel
{
    Q_OBJECT
    Q_PROPERTY(QUrl source READ source WRITE setSource NOTIFY sourceChanged)
    Q_PROPERTY(QString dataset READ dataset WRITE setDataset NOTIFY datasetChanged)
    Q_PROPERTY(bool hasUnsavedChanges READ hasUnsavedChanges NOTIFY hasUnsavedChangesChanged)
    Q_PROPERTY(int currentSlice READ currentSlice WRITE setCurrentSlice NOTIFY currentSliceChanged)
    Q_PROPERTY(int sliceCount READ sliceCount NOTIFY sliceCountChanged)

public:
    ExdirDatasetModel(QObject *parent = 0);

    virtual int rowCount(const QModelIndex &parent = QModelIndex()) const override;
    virtual int columnCount(const QModelIndex &parent = QModelIndex()) const override;
    virtual QVariant data(const QModelIndex &index, int role) const override;
    virtual bool setData(const QModelIndex &index, const QVariant &value, int role) override;
    virtual QHash<int, QByteArray> roleNames() const;
    QString dataset() const;
    QUrl source() const;
    bool inBounds(const QModelIndex &index) const;
    bool hasUnsavedChanges() const;
    int currentSlice() const;
    int sliceCount() const;

public slots:
    void setDataset(QString dataset);
    void setSource(QUrl source);
    bool save();
    void setCurrentSlice(int currentSlice);

signals:
    void datasetChanged(QString dataset);
    void sourceChanged(QUrl source);
    void hasUnsavedChangesChanged(bool hasUnsavedChanges);
    void currentSliceChanged(int currentSlice);
    void sliceCountChanged(int sliceCount);

private:
    void load();

    QString m_dataset;
    QUrl m_source;
//    arma::mat m_data;
    elegant::exdir::Datatype::Type m_currentType = elegant::exdir::Datatype::Type::Unknown;
    bool m_hasData = false;
    int m_dimensionCount = -1;

    using variantType = boost::variant<
    arma::Cube<int>,
    arma::Cube<long int>,
    arma::Cube<float>,
    arma::Cube<double>
    >;

    variantType m_dataPointer;

    bool m_hasUnsavedChanges = false;
    int m_currentSlice = 0;
    int m_sliceCount = 1;
    void setSliceCount(int sliceCount);
};

#endif // EXDIRMODEL_H
