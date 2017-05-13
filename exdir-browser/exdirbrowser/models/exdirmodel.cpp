#include "exdirmodel.h"

#include <elegant-exdir/Attribute>
#include <elegant-exdir/Dataset>
#include <elegant-exdir/File>

#include <boost/variant/get.hpp>

#include <QDebug>
#include <QStringBuilder>
#include <QQmlFile>
#include <QUrl>

#include <iostream>
#include <functional>

using namespace std;
using namespace arma;
using namespace elegant::exdir;


class transpose_visitor : public boost::static_visitor<>
{
public:
    template<typename eT>
    void operator()(Cube<eT>& m) const
    {
        Cube<eT> a(m.n_cols, m.n_rows, m.n_slices);
        a.slice(0) = m.slice(0).t();
        m = a;
    }
};

class row_count_visitor : public boost::static_visitor<int>
{
public:
    result_type operator()(const auto& m) const
    {
        return m.n_rows;
    }
};

class column_count_visitor : public boost::static_visitor<int>
{
public:
    result_type operator()(const auto& m) const
    {
        return m.n_cols;
    }
};

class in_bounds_visitor : public boost::static_visitor<bool>
{
public:
    in_bounds_visitor(const QModelIndex& index, int currentSlice)
        : m_index(index)
        , m_currentSlice(currentSlice)
    {
    }

    result_type operator()(const auto& m) const
    {
        if(m_index.row() >= 0
                && m_index.column() >= 0
                && m_currentSlice >= 0
                && m_index.column() < int(m.n_cols)
                && m_index.row() < int(m.n_rows)
                && m_currentSlice < int(m.n_slices)) {
            return true;
        } else {
            return false;
        }
    }
    QModelIndex m_index;
    int m_currentSlice;
};

class data_visitor : public boost::static_visitor<QVariant>
{
public:
    data_visitor(const QModelIndex& index, int currentSlice)
        : m_index(index)
        , m_currentSlice(currentSlice)
    {
    }

    result_type operator()(const auto& m) const
    {
        return QVariant::fromValue(m(m_index.row(), m_index.column(), m_currentSlice));
    }
    QModelIndex m_index;
    int m_currentSlice;
};

class set_data_visitor : public boost::static_visitor<>
{
public:
    set_data_visitor(const QModelIndex& index, int currentSlice, QVariant value)
        : m_index(index)
        , m_currentSlice(currentSlice)
        , m_value(value)
    {
    }

    result_type operator()(auto& m) const
    {
        double doubleValue = m_value.toDouble();
        m(m_index.row(), m_index.column(), m_currentSlice) = doubleValue;
    }
    QModelIndex m_index;
    int m_currentSlice;
    QVariant m_value;
};

class save_visitor : public boost::static_visitor<>
{
public:
    save_visitor(Dataset *dataset, int dimensionCount)
        : m_dataset(dataset)
        , m_dimensionCount(dimensionCount)
    {
    }

    template<typename eT>
    result_type operator()(Cube<eT>& m) const
    {
        if(m_dimensionCount == 0) {
            eT element = m(0, 0, 0);
            *m_dataset = element;
        } else if(m_dimensionCount == 1) {
            arma::Col<eT> col = m.slice(0).col(0); // write column because we transpose on load
            *m_dataset = col;
        } else if(m_dimensionCount == 2) {
            arma::Mat<eT> matrix = m.slice(0);
            *m_dataset = matrix;
        } else if(m_dimensionCount == 3) {
            *m_dataset = m;
        } else {
            qWarning() << "Cannot save object with" << m_dimensionCount << "dimensions";
        }
    }
    Dataset *m_dataset;
    int m_dimensionCount;
};

ExdirDatasetModel::ExdirDatasetModel(QObject* parent) : QAbstractTableModel(parent)
{

}

int ExdirDatasetModel::rowCount(const QModelIndex &parent) const
{
    Q_UNUSED(parent);
    if(!m_hasData) {
        return 0;
    }
    return boost::apply_visitor(row_count_visitor(), m_dataPointer);
}

int ExdirDatasetModel::columnCount(const QModelIndex &parent) const
{
    Q_UNUSED(parent);
    if(!m_hasData) {
        return 0;
    }
    return boost::apply_visitor(column_count_visitor(), m_dataPointer);
}

bool ExdirDatasetModel::inBounds(const QModelIndex &index) const
{
    if(!m_hasData) {
        return false;
    }
    return boost::apply_visitor(in_bounds_visitor(index, m_currentSlice), m_dataPointer);
}

bool ExdirDatasetModel::hasUnsavedChanges() const
{
    return m_hasUnsavedChanges;
}

int ExdirDatasetModel::currentSlice() const
{
    return m_currentSlice;
}

int ExdirDatasetModel::sliceCount() const
{
    return m_sliceCount;
}

QVariant ExdirDatasetModel::data(const QModelIndex &index, int role) const
{
    if(!m_hasData) {
        return QVariant();
    }
    if(role == Qt::DisplayRole) {
        if(inBounds(index)) {
            return boost::apply_visitor(data_visitor(index, m_currentSlice), m_dataPointer);
        } else {
            qWarning() << "Requested index out of bounds" << index;
        }
        return QVariant::fromValue(0.0);
    } else {
        return QVariant();
    }
}


bool ExdirDatasetModel::setData(const QModelIndex &index, const QVariant &value, int role)
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
    boost::apply_visitor(set_data_visitor(index, m_currentSlice, value), m_dataPointer);
    m_hasUnsavedChanges = true;
    emit dataChanged(index, index);
    emit hasUnsavedChangesChanged(m_hasUnsavedChanges);
    return true;
}

QHash<int, QByteArray> ExdirDatasetModel::roleNames() const
{
    QHash<int, QByteArray> roles;
    roles[Qt::DisplayRole] = "value";
    return roles;
}

QString ExdirDatasetModel::dataset() const
{
    return m_dataset;
}

QUrl ExdirDatasetModel::source() const
{
    return m_source;
}

void ExdirDatasetModel::setDataset(QString dataSet)
{
    if (m_dataset == dataSet)
        return;

    m_dataset = dataSet;
    load();
    emit datasetChanged(dataSet);
}

void ExdirDatasetModel::setSource(QUrl source)
{
    if (m_source == source)
        return;

    m_source = source;
    load();
    emit sourceChanged(source);
}

void ExdirDatasetModel::setCurrentSlice(int currentSlice)
{
    if (m_currentSlice == currentSlice)
        return;

    m_currentSlice = currentSlice;
    emit dataChanged(index(0, 0), index(rowCount() - 1, columnCount() - 1));
    emit currentSliceChanged(currentSlice);
}

void ExdirDatasetModel::setSliceCount(int sliceCount)
{
    if (m_sliceCount == sliceCount)
        return;

    m_sliceCount = sliceCount;
    emit currentSliceChanged(sliceCount);
}

void ExdirDatasetModel::load()
{
    m_hasData = false;
    m_dimensionCount = 0;

    if(!m_source.isValid() || m_dataset.isEmpty()) {
        emit dataChanged(QModelIndex(), QModelIndex());
        return;
    }

    QString fileNameString = QQmlFile::urlToLocalFileOrQrc(m_source);
    std::string datasetName = m_dataset.toStdString();
    File file(fileNameString.toStdString(), File::OpenMode::ReadWrite);
    if(file[datasetName].isDataset()) {
        Dataset dataset = file[datasetName];
        m_hasData = true;
        m_currentType = dataset.datatype();
        m_dimensionCount = dataset.dimensionCount();
        auto extents = dataset.extents();
        if(m_dimensionCount == 3) {
            setSliceCount(extents[0]);
        }
        switch(m_currentType) {
        case Datatype::Type::Int:
            m_dataPointer = dataset.value<arma::Cube<int>>(Object::ConversionFlags::GreaterThanOrEqualDimensionCount);
            break;
        case Datatype::Type::Long:
            m_dataPointer = dataset.value<arma::Cube<long int>>(Object::ConversionFlags::GreaterThanOrEqualDimensionCount);
            break;
        case Datatype::Type::Float:
            m_dataPointer = dataset.value<arma::Cube<float>>(Object::ConversionFlags::GreaterThanOrEqualDimensionCount);
            break;
        case Datatype::Type::Double:
            m_dataPointer = dataset.value<arma::Cube<double>>(Object::ConversionFlags::GreaterThanOrEqualDimensionCount);
            break;
        default:
            qWarning() << "Could not read this type of data";
            m_hasData = false;
            m_dimensionCount = 0;
            break;
        }
        if(m_dimensionCount == 1) {
            // transpose to visualize 1D as column instead of row
            boost::apply_visitor(transpose_visitor(), m_dataPointer);
        }
    }
    if(!m_hasData || m_dimensionCount != 3) {
        setSliceCount(1);
    }
    m_hasUnsavedChanges = false;
    emit sliceCountChanged(m_sliceCount);
    emit dataChanged(QModelIndex(), QModelIndex());
    emit hasUnsavedChangesChanged(m_hasUnsavedChanges);
}

bool ExdirDatasetModel::save()
{
    // TODO keep working on the same file when loading/saving

    qDebug() << "Saving file";
    if(!m_source.isValid() || m_dataset.isEmpty()) {
        return false;
    }
    QString fileNameString = QQmlFile::urlToLocalFileOrQrc(m_source);
    std::string datasetName = m_dataset.toStdString();
    qDebug() << "Loading" << m_dataset << "in" << fileNameString;
    File file(fileNameString.toStdString(), File::OpenMode::ReadWrite);

    if(file[datasetName].isDataset()) {
        Dataset dataset = file[datasetName];
        boost::apply_visitor(save_visitor(&dataset, m_dimensionCount), m_dataPointer);
    }
    m_hasUnsavedChanges = false;
    emit hasUnsavedChangesChanged(m_hasUnsavedChanges);
    return true;
}
