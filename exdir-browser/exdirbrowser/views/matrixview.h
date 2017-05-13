#ifndef MATRIXVIEW_H
#define MATRIXVIEW_H

#include <QElapsedTimer>
#include <QQuickItem>
#include <QVariant>
#include <QModelIndex>
#include <QTimer>

class QQmlComponent;
class QAbstractTableModel;

struct CachedItem
{
    CachedItem() {}
    CachedItem(QQuickItem *item_, long int row_, long int column_)
        : item(item_)
        , row(row_)
        , column(column_)
    {
    }
    QQuickItem *item = nullptr;
    long int row = -1;
    long int column = -1;
    bool dummy = true;
};

class MatrixView : public QQuickItem
{
    Q_OBJECT
    Q_PROPERTY(QVariant model READ model WRITE setModel NOTIFY modelChanged)
    Q_PROPERTY(QQmlComponent *delegate READ delegate WRITE setDelegate NOTIFY delegateChanged)
    Q_PROPERTY(double cellWidth READ cellWidth WRITE setCellWidth NOTIFY cellWidthChanged)
    Q_PROPERTY(double cellHeight READ cellHeight WRITE setCellHeight NOTIFY cellHeightChanged)
    Q_PROPERTY(QModelIndex currentIndex READ currentIndex WRITE setCurrentIndex NOTIFY currentIndexChanged)

public:
    MatrixView();

    QVariant model() const;
    QQmlComponent * delegate() const;
    double cellWidth() const;
    double cellHeight() const;

    QModelIndex currentIndex() const;

    void focusItemAt(int row, int column);
    QRectF viewportRect() const;
    QRectF itemRect(int row, int column) const;
signals:
    void modelChanged(QVariant model);
    void delegateChanged(QQmlComponent * delegate);
    void cellWidthChanged(double cellWidth);
    void cellHeightChanged(double cellHeight);

    void currentIndexChanged(QModelIndex currentIndex);

public slots:
    void setModel(QVariant model);
    void setDelegate(QQmlComponent * delegate);
    void setCellWidth(double cellWidth);
    void setCellHeight(double cellHeight);
    void updateView();
    void clear();

    void setCurrentIndex(QModelIndex currentIndex);

private slots:
    void reconnectObjects();
    void handleDataChange(const QModelIndex &topLeft, const QModelIndex &bottomRight, QVector<int> roles = QVector<int>());

    void updateViewFully();
private:
    bool shouldSkip(long int row, long int column) const;
    void updateContextData(int row, int column, QQmlContext *context);

    QAbstractTableModel *m_model = nullptr;
    QQmlComponent * m_delegate;
    QVector<CachedItem> m_cachedItems;

    QRectF m_previousViewportRect;
    QRectF m_previousViewportRectFully;
    QElapsedTimer timer;
    double m_cellWidth = 100;
    double m_cellHeight = 30;

    QQuickItem *m_flickable = nullptr;
    QQuickItem *m_viewport;
    QModelIndex m_currentIndex;

    QTimer m_updateTimer;

    // QQuickItem interface
protected:
    virtual void keyPressEvent(QKeyEvent *event) override;
};

#endif // MATRIXVIEW_H
