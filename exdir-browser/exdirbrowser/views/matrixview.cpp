#include "matrixview.h"

#include <QAbstractTableModel>
#include <QQmlContext>
#include <QQmlEngine>
#include <QSGNode>
#include <QtConcurrent/QtConcurrent>
#include <cmath>
#include <sstream>
#include <iomanip>

using std::min;
using std::max;

MatrixView::MatrixView()
{
    reconnectObjects();
    connect(this, &MatrixView::parentChanged, this, &MatrixView::reconnectObjects);
    connect(this, &MatrixView::widthChanged, this, &MatrixView::updateView);
    connect(this, &MatrixView::heightChanged, this, &MatrixView::updateView);
    connect(&m_updateTimer, &QTimer::timeout, this, &MatrixView::updateViewFully);
    m_updateTimer.setInterval(16);
    m_updateTimer.setSingleShot(true);
}

QVariant MatrixView::model() const
{
    return *reinterpret_cast<QVariant*>(m_model);
}

QQmlComponent *MatrixView::delegate() const
{
    return m_delegate;
}

double MatrixView::cellWidth() const
{
    return m_cellWidth;
}

double MatrixView::cellHeight() const
{
    return m_cellHeight;
}

QModelIndex MatrixView::currentIndex() const
{
    return m_currentIndex;
}

void MatrixView::setCellWidth(double cellWidth)
{
    if (m_cellWidth == cellWidth)
        return;

    m_cellWidth = cellWidth;
    updateView();
    emit cellWidthChanged(cellWidth);
}

void MatrixView::setCellHeight(double cellHeight)
{
    if (m_cellHeight == cellHeight)
        return;

    m_cellHeight = cellHeight;
    updateView();
    emit cellHeightChanged(cellHeight);
}

bool MatrixView::shouldSkip(long row, long column) const
{
    for(const CachedItem &item : m_cachedItems) {
        if(item.row == row && item.column == column) {
            return true;
        }
    }
    return false;
}

void MatrixView::setDelegate(QQmlComponent *delegate)
{
    if (m_delegate == delegate)
        return;

    m_delegate = delegate;

    updateView();

    emit delegateChanged(delegate);
}

void MatrixView::setModel(QVariant model)
{
    QObject* modelObject = qvariant_cast<QObject*>(model);
    QAbstractTableModel* tableModel = qobject_cast<QAbstractTableModel*>(modelObject);
    if(!tableModel) {
        return;
    }

    m_model = tableModel;
    connect(m_model, &QAbstractTableModel::dataChanged, this, &MatrixView::handleDataChange);

    updateView();

    emit modelChanged(model);
}

void MatrixView::setCurrentIndex(QModelIndex currentIndex)
{
    if (m_currentIndex == currentIndex)
        return;

    m_currentIndex = currentIndex;
    emit currentIndexChanged(currentIndex);
}

void MatrixView::reconnectObjects()
{
    if(parent()) {
        connect(parent(), SIGNAL(flickableItemChanged()), this, SLOT(reconnectObjects()));
        connect(parent(), SIGNAL(viewportChanged()), this, SLOT(reconnectObjects()));
    }
    m_flickable = nullptr;
    m_viewport = nullptr;
    if(parent()) {
        const QVariant& flickableProperty = parent()->property("flickableItem");
        if(flickableProperty.isValid()) {
            QQuickItem *flickable = qvariant_cast<QQuickItem*>(flickableProperty);
            if(flickable) {
                m_flickable = flickable;
                connect(flickable, SIGNAL(contentXChanged()), this, SLOT(updateView()));
                connect(flickable, SIGNAL(contentYChanged()), this, SLOT(updateView()));
            }
        }
        const QVariant& viewportProperty = parent()->property("viewport");
        if(viewportProperty.isValid()) {
            QQuickItem *viewport = qvariant_cast<QQuickItem*>(viewportProperty);
            if(viewport) {
                m_viewport = viewport;
                connect(viewport, SIGNAL(widthChanged()), this, SLOT(updateView()));
                connect(viewport, SIGNAL(heightChanged()), this, SLOT(updateView()));
            }
        }
    }
}

void MatrixView::clear()
{
    for(auto &element : m_cachedItems) {
        element.item->deleteLater();
    }
    m_cachedItems.clear();
    updateView();
}

void MatrixView::updateContextData(int row, int column, QQmlContext* context)
{
    QModelIndex modelIndex = m_model->index(row, column);
    if(!modelIndex.isValid()) {
        qFatal("Requested to update context data for invalid index");
        return;
    }

    context->setContextProperty("index", modelIndex); // TODO: Change to proper index and modelData
    // context->setContextProperty("row", QVariant::fromValue(row));
    // context->setContextProperty("column", QVariant::fromValue(column));

    QVariant value = m_model->data(modelIndex, Qt::DisplayRole);
    QString formattedValue;
    if(value.canConvert(QVariant::Double)) {
        bool ok = false;
        double numericValue = value.toDouble(&ok);
        formattedValue = QString::number(numericValue);
        if(ok) {
            std::ostringstream out;
            if(numericValue == 0.0) {
                formattedValue = "0.0";
            } else if(fabs(numericValue) < 1e7 && fabs(numericValue) >= 0.001) {
                // the following skips the least significant character in a double
                // because this will show the round off error due to double precision
                // i.e. we want, 0.2 rather than 0.200000000000001
                out << std::setprecision(14) << numericValue;
                formattedValue = QString::fromStdString(out.str());
            } else {
                out << std::scientific << std::setprecision(14) << numericValue;
                formattedValue = QString::fromStdString(out.str());
                formattedValue = formattedValue.replace(QRegularExpression("0+e"), "e");
                formattedValue = formattedValue.replace(QRegularExpression("\\.e"), ".0e");
            }
        } else {
            qWarning() << "Could not convert QVariant to double for an unknown reason:" << value;
        }
    }
    context->setContextProperty("value", formattedValue); // TODO: Change to role index
}

void MatrixView::handleDataChange(const QModelIndex &topLeft, const QModelIndex &bottomRight, QVector<int> roles)
{
    Q_UNUSED(roles);
    if(!topLeft.isValid() || !bottomRight.isValid()) {
        clear();
        return;
    }
    QQmlContext *context = nullptr;
    for(CachedItem &element : m_cachedItems) {
        if(element.row >= topLeft.row() && element.column >= topLeft.column()
                && element.row <= bottomRight.row() && element.column <= bottomRight.column()) {
            QQuickItem *item = element.item;
            context = QQmlEngine::contextForObject(item)->parentContext();
            updateContextData(element.row, element.column, context);
        }
    }
}

QRectF MatrixView::viewportRect() const
{
    double viewportWidth = 0;
    double viewportHeight = 0;
    double contentX = 0;
    double contentY = 0;
    if(m_flickable) {
        contentX = m_flickable->property("contentX").toDouble();
        contentY = m_flickable->property("contentY").toDouble();
    }
    if(m_viewport) {
        viewportWidth = m_viewport->width();
        viewportHeight = m_viewport->height();
    } else {
        viewportWidth = width();
        viewportHeight = height();
    }
    return QRectF(contentX, contentY, viewportWidth, viewportHeight);
}

void MatrixView::updateView()
{
    if(!m_model || !m_delegate) {
        return;
    }

    QRectF currentRect = viewportRect();
    double xDiff = currentRect.x() - m_previousViewportRect.x();
    double yDiff = currentRect.y() - m_previousViewportRect.y();

    setX(x() + xDiff);
    setY(y() + yDiff);

    if(!m_updateTimer.isActive()) {
        m_updateTimer.start();
    }

    m_previousViewportRect = viewportRect();
}

void MatrixView::updateViewFully()
{
    setX(0);
    setY(0);

    if(!m_model || !m_delegate) {
        return;
    }

    long int rowCount = m_model->rowCount();
    long int columnCount = m_model->columnCount();

    double itemWidth = m_cellWidth;
    double itemHeight = m_cellHeight;
    const QRectF &viewport = viewportRect();

    bool cacheContainsValidItems = m_previousViewportRectFully.intersects(viewport);
    if(!cacheContainsValidItems) {
        for(CachedItem &element : m_cachedItems) {
            element.row = -1;
            element.column = -1;
            element.item->setVisible(false);
        }
    } else {
        QMutableVectorIterator<CachedItem> cachedIterator(m_cachedItems);
        while(cachedIterator.hasNext()) {
            CachedItem &element = cachedIterator.next();
            QQuickItem* item = element.item;
            if(!item->boundingRect().intersects(viewport)) {
                element.row = -1;
                element.column = -1;
                element.item->setVisible(false);
            }
        }
    }

    long int firstColumn = viewport.left() / itemWidth;
    long int firstRow = viewport.top() / itemHeight;
    long int lastColumn = viewport.right() / itemWidth + 1;
    long int lastRow = viewport.bottom() / itemHeight + 1;

    lastColumn = min(lastColumn, columnCount);
    lastRow = min(lastRow, rowCount);

    for(long int row = firstRow; row < lastRow; row++) {
        for(long int column = firstColumn; column < lastColumn; column++) {
            double x = column * itemWidth;
            double y = row * itemHeight;

            if(cacheContainsValidItems) {
                bool shouldSkip = false;
                for(const CachedItem &item : m_cachedItems) {
                    if(item.row == row && item.column == column) {
                        shouldSkip = true;
                    }
                }
                if(shouldSkip) {
                    continue;
                }
            }

            QQuickItem* item = nullptr;
            QQmlContext* context = nullptr;
            bool foundReusable = false;
            for(CachedItem &element : m_cachedItems) {
                if(element.row == -1 && element.column == -1) {
                    foundReusable = true;
                    item = element.item;
                    element.row = row;
                    element.column = column;
                    context = QQmlEngine::contextForObject(item)->parentContext();
                    break;
                }
            }

            if(!foundReusable) {
                QQmlContext* parentContext = m_delegate->creationContext();
                Q_ASSERT(parentContext);
                context = new QQmlContext(parentContext);

                QObject *itemObject = delegate()->beginCreate(context);
                Q_ASSERT(context->engine()->objectOwnership(itemObject) == QQmlEngine::CppOwnership);

                item = qobject_cast<QQuickItem*>(itemObject);

                if(!item) {
                    qFatal("Could not instantiate object!");
                }
                m_cachedItems.append(CachedItem(item, row, column));
            }

            item->setParentItem(this);
            item->setVisible(true);

            item->setX(x);
            item->setY(y);
            item->setHeight(itemHeight);
            item->setWidth(itemWidth);
            updateContextData(row, column, context);

            if(!foundReusable) {
                delegate()->completeCreate();
            }
        }
    }

    setImplicitHeight(itemHeight * rowCount);
    setImplicitWidth(itemWidth * columnCount);
    m_previousViewportRectFully = viewportRect();
}

QRectF MatrixView::itemRect(int row, int column) const
{
    return QRectF(column * m_cellWidth, row * m_cellHeight,
                  m_cellWidth, m_cellHeight);
}

void MatrixView::focusItemAt(int row, int column)
{
    row = max(0, row);
    row = min(m_model->rowCount() - 1, row);
    column = max(0, column);
    column = min(m_model->columnCount() - 1, column);
    QModelIndex newIndex;
    newIndex = m_model->index(row, column);
    if(newIndex.isValid()) {
        setCurrentIndex(newIndex);
        if(m_flickable) {
            const QRectF &viewport = viewportRect();
            const QRectF &item = itemRect(row, column);
            QRectF intersection = item.intersected(viewport);
            if(intersection.size() != item.size()) {
                if(item.left() < viewport.left()) {
                    m_flickable->setProperty("contentX", item.left());
                } else if(item.right() > viewport.right()) {
                    m_flickable->setProperty("contentX", item.right() - viewport.width());
                }
                if(item.top() < viewport.top()) {
                    m_flickable->setProperty("contentY", item.top());
                } else if(item.bottom() > viewport.bottom()) {
                    m_flickable->setProperty("contentY", item.bottom() - viewport.height());
                }
                updateView();
            }
        }
        for(const CachedItem &element : m_cachedItems) {
            if(element.row == row && element.column == column) {
                QQuickItem *item = element.item;
                if(item) {
                    item->forceActiveFocus();
                }
            }
        }
    }
}

void MatrixView::keyPressEvent(QKeyEvent *event)
{
    const QModelIndex &index = currentIndex();
    int currentRow = index.row();
    int currentColumn = index.column();

    int stepSize = 1;
    if(event->modifiers() & Qt::ControlModifier) {
        stepSize = 10;
    }
    switch(event->key()) {
    case Qt::Key_Up:
        focusItemAt(currentRow - stepSize, currentColumn);
        break;
    case Qt::Key_Down:
        focusItemAt(currentRow + stepSize, currentColumn);
        break;
    case Qt::Key_Left:
        focusItemAt(currentRow, currentColumn - stepSize);
        break;
    case Qt::Key_Right:
        focusItemAt(currentRow, currentColumn + stepSize);
        break;
    case Qt::Key_PageUp:
        focusItemAt(currentRow - viewportRect().height() / m_cellHeight, currentColumn);
        break;
    case Qt::Key_PageDown:
        focusItemAt(int(currentRow + viewportRect().height() / m_cellHeight), currentColumn);
        break;
    }
}
