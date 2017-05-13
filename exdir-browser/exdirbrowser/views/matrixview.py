from PyQt5 import QtCore
from PyQt5.QtCore import *
from PyQt5.QtQml import *
from PyQt5.QtQuick import *
import sip

class CachedItem:
    def __init__(self, item=None, row=-1, column=-1, context=None):
        self.item = item
        self.row = row
        self.column = column
        self.dummy = True
        self.context = context


class MatrixView(QQuickItem):
    def __init__(self, parent=None):
        super().__init__(parent)

        self._model = None
        self._delegate = None
        self._cellWidth = 64
        self._cellHeight = 64
        self._currentIndex = QModelIndex()
        self.previousViewportRect = QRectF()
        self.previousViewportRectFully = QRectF()
        self.cachedItems = []

        self.reconnectObjects()
        self.parentChanged.connect(self.reconnectObjects)
        self.widthChanged.connect(self.updateView)
        self.heightChanged.connect(self.updateView)
        self.updateTimer = QTimer()
        self.updateTimer.timeout.connect(self.updateViewFully)
        self.updateTimer.setInterval(16)
        self.updateTimer.setSingleShot(True)

    def model(self):
        return self._model

    def delegate(self):
        return self._delegate

    def cellWidth(self):
        return self._cellWidth

    def cellHeight(self):
        return self._cellHeight

    def currentIndex(self):
        return self._currentIndex

    def setCellWidth(self, cellWidth):
        if self._cellWidth == cellWidth:
            return

        self._cellWidth = cellWidth
        self.updateView()
        self.cellWidthChanged.emit(cellWidth)

    def setCellHeight(self, cellHeight):
        if self._cellHeight == cellHeight:
            return

        self._cellHeight = cellHeight
        self.updateView()
        self.cellHeightChanged.emit(cellHeight)

    def shouldSkip(self, row, column):
        for item in self.cachedItems:
            if item.row == row and item.column == column:
                return True
        return False

    def setDelegate(self, delegate):
        print("Delegate", delegate)
        if self._delegate == delegate:
            return

        self._delegate = delegate

        self.updateView()

        self.delegateChanged.emit(delegate)


    def setModel(self, model):
        modelObject = model
        tableModel = modelObject
        
        # TODO verify tablemodel type
        
        if not tableModel:
            return
            
        self._model = tableModel
        self._model.dataChanged.connect(self.handleDataChange)

        self.updateView()
        self.modelChanged.emit(model)


    def setCurrentIndex(self, currentIndex):
        if self._currentIndex == currentIndex:
            return

        self._currentIndex = currentIndex
        self.currentIndexChanged.emit(currentIndex)


    def reconnectObjects(self):
        if self.parent():
            self.parent().flickableItemChanged.connect(self.reconnectObjects)
            self.parent().viewportChanged.connect(self.reconnectObjects)

        self.flickable = None
        self.viewport = None
        if self.parent():
            sip.enableautoconversion(QVariant, False) # NOTE QQuickFlickable conversion doesn't work
            flickableProperty = self.parent().property("flickableItem")
            if flickableProperty.isValid():
                self.flickable = self.parent() 
                self.flickable.contentXChanged.connect(self.updateView)
                self.flickable.contentYChanged.connect(self.updateView)
        
            viewportProperty = self.parent().property("viewport")
            if viewportProperty.isValid():
                self.viewport = viewportProperty.value()
                self.viewport.widthChanged.connect(self.updateView)
                self.viewport.heightChanged.connect(self.updateView)
            sip.enableautoconversion(QVariant, True)

    def clear(self):
        for element in self.cachedItems:
            element.item.deleteLater()

        self.cachedItems.clear()
        self.updateView()


    def updateContextData(self, row, column, context):
        modelIndex = self._model.index(row, column)
        if not modelIndex.isValid():        
            print("ERROR modelIndex is not valid")
            return

        if not context:
            print("ERROR got no context")
            return
            
        context.setContextProperty("index", modelIndex)  # TODO: Change to proper index and modelData
        context.setContextProperty("row", QVariant(row))
        context.setContextProperty("column", QVariant(column))

        value = self._model.data(modelIndex, Qt.DisplayRole)
        formattedValue = ""
        formattedValue = str(value)
        # if value.canConvert(QVariant.Double):        
        #     ok = False
        #     numericValue = value
        #     formattedValue = QString.number(numericValue)
        #     if ok:
        #         if numericValue == 0.0:
        #             formattedValue = "0.0"
        #         elif fabs(numericValue) < 1e7 and fabs(numericValue) >= 0.001:                
        #             pass
        #             # TODO fix these
        #             # the following skips the least significant character in a double
        #             # because self will show the round off error due to double precision
        #             # i.e. we want, 0.2 rather than 0.200000000000001
        #             #out << std.setprecision(14) << numericValue
        #             #formattedValue = QString.fromStdString(out.str())
        #         else:
        #             #out << std.scientific << std.setprecision(14) << numericValue
        #             formattedValue = QString.fromStdString(out.str())
        #             formattedValue = formattedValue.replace(QRegularExpression("0+e"), "e")
        #             formattedValue = formattedValue.replace(QRegularExpression("\\.e"), ".0e")
        # 
        #     else:
        #         print("WARNING: Could not convert QVariant to double for an unknown reason:", value)

        context.setContextProperty("value", formattedValue); # TODO: Change to role index


    def handleDataChange(self, topLeft, bottomRight, roles):
        if not topLeft.isValid() or not bottomRight.isValid():        
            self.clear()
            return
        context = None
        for element in self.cachedItems:
            if element.row >= topLeft.row() and element.column >= topLeft.column() and element.row <= bottomRight.row() and element.column <= bottomRight.column():
                item = element.item
                context = QQmlEngine.contextForObject(item).parentContext()
                self.updateContextData(element.row, element.column, context)

    def viewportRect(self):
        viewportWidth = 0
        viewportHeight = 0
        contentX = 0
        contentY = 0
        if self.flickable:        
            contentX = self.flickable.property("contentX")
            contentY = self.flickable.property("contentY")

        if self.viewport:        
            viewportWidth = self.viewport.width()
            viewportHeight = self.viewport.height()
        else:
            viewportWidth = self.width()
            viewportHeight = self.height()

        return QRectF(contentX, contentY, viewportWidth, viewportHeight)


    def updateView(self):
        if not self._model or not self._delegate:
            return

        currentRect = self.viewportRect()
        xDiff = currentRect.x() - self.previousViewportRect.x()
        yDiff = currentRect.y() - self.previousViewportRect.y()

        self.setX(self.x() + xDiff)
        self.setY(self.y() + yDiff)

        if not self.updateTimer.isActive():        
            self.updateTimer.start()

        self.previousViewportRect = self.viewportRect()


    def updateViewFully(self):
        self.setX(0)
        self.setY(0)

        if not self._model or not self._delegate:        
            return

        rowCount = self._model.rowCount()
        columnCount = self._model.columnCount()

        itemWidth = self._cellWidth
        itemHeight = self._cellHeight
        viewport = self.viewportRect()

        cacheContainsValidItems = self.previousViewportRectFully.intersects(viewport)
        if not cacheContainsValidItems:   
            for element in self.cachedItems:
                element.row = -1
                element.column = -1
                element.item.setVisible(False)
        else:
            for element in self.cachedItems:
                item = element.item
                if not QRectF(item.x(), item.y(), item.width(), item.height()).intersects(viewport):
                    element.row = -1
                    element.column = -1
                    element.item.setVisible(False)

        firstColumn = int(viewport.left() / itemWidth)
        firstRow = int(viewport.top() / itemHeight)
        lastColumn = int(viewport.right() / itemWidth + 1)
        lastRow = int(viewport.bottom() / itemHeight + 1)

        lastColumn = min(lastColumn, columnCount)
        lastRow = min(lastRow, rowCount)

        for row in range(firstRow, lastRow):
            for column in range(firstColumn, lastColumn):
                x = column * itemWidth
                y = row * itemHeight

                if cacheContainsValidItems:
                    shouldSkip = False
                    for item in self.cachedItems:
                        if item.row == row and item.column == column:
                            shouldSkip = True
                    if shouldSkip:
                        continue

                item = None
                context = None
                foundReusable = False
                for element in self.cachedItems:
                    if element.row == -1 and element.column == -1:
                        foundReusable = True
                        item = element.item
                        element.row = row
                        element.column = column
                        context = element.context
                        break

                if not foundReusable:        
                    parentContext = self._delegate.creationContext()
                    assert(parentContext)
                    context = QQmlContext(parentContext)

                    item = self._delegate.beginCreate(context)
                    assert(context.engine().objectOwnership(item) == QQmlEngine.CppOwnership)

                    if not item:
                        print("WARNING: Could not instantiate object!")

                    self.cachedItems.append(CachedItem(item, row, column, context))


                item.setParentItem(self)
                item.setVisible(True)

                item.setX(x)
                item.setY(y)
                item.setHeight(itemHeight)
                item.setWidth(itemWidth)
                self.updateContextData(row, column, context)

                if not foundReusable:
                    self._delegate.completeCreate()
                    
        self.setImplicitHeight(itemHeight * rowCount)
        self.setImplicitWidth(itemWidth * columnCount)
        self.previousViewportRectFully = self.viewportRect()

    def itemRect(self, row, column):
        return QRectF(column * self._cellWidth, * self._cellHeight,
                      self._cellWidth, self._cellHeight)

    def focusItemAt(self, row, column):
        row = max(0, row)
        row = min(self._model.rowCount() - 1, row)
        column = max(0, column)
        column = min(self._model.columnCount() - 1, column)
        newIndex = self._model.index(row, column)
        if newIndex.isValid():        
            setCurrentIndex(newIndex)
            if self.flickable:             
                viewport = self.viewportRect()
                item = itemRect(row, column)
                intersection = item.intersected(viewport)
                if intersection.size() != item.size():
                    if item.left() < viewport.left():
                        self.flickable.setProperty("contentX", item.left())
                    elif item.right() > viewport.right():                    
                        self.flickable.setProperty("contentX", item.right() - viewport.width())
                    if item.top() < viewport.top():
                        self.flickable.setProperty("contentY", item.top())
                    elif item.bottom() > viewport.bottom():
                        self.flickable.setProperty("contentY", item.bottom() - viewport.height())
                    self.updateView()

            for element in self.cachedItems:
                if element.row == row and element.column == column:
                    item = element.item
                    if item:
                        item.forceActiveFocus()

    def keyPressEvent(self, *event):
        index = self.currentIndex
        currentRow = index.row()
        currentColumn = index.column()

        stepSize = 1
        # if event.modifiers() & Qt.ControlModifier:        
            # stepSize = 10

        # switch(event.key())    case Qt.Key_Up:
        #     focusItemAt(currentRow - stepSize, currentColumn)
        #     break
        # case Qt.Key_Down:
        #     focusItemAt(currentRow + stepSize, currentColumn)
        #     break
        # case Qt.Key_Left:
        #     focusItemAt(currentRow, currentColumn - stepSize)
        #     break
        # case Qt.Key_Right:
        #     focusItemAt(currentRow, currentColumn + stepSize)
        #     break
        # case Qt.Key_PageUp:
        #     focusItemAt(currentRow - viewportRect().height() / self._cellHeight, currentColumn)
        #     break
        # case Qt.Key_PageDown:
        #     focusItemAt(int(currentRow + viewportRect().height() / self._cellHeight), currentColumn)
        #     break
        
    modelChanged = pyqtSignal(QVariant)
    delegateChanged = pyqtSignal(QQmlComponent)
    cellWidthChanged = pyqtSignal(float)
    cellHeightChanged = pyqtSignal(float)
    currentIndexChanged = pyqtSignal(QModelIndex)

    model = pyqtProperty(QVariant, model, setModel, notify=modelChanged)
    delegate = pyqtProperty(QQmlComponent, delegate, setDelegate, notify=delegateChanged)
    cellWidth = pyqtProperty(float, cellWidth, setCellWidth, notify=cellWidthChanged)
    cellHeight = pyqtProperty(float, cellHeight, setCellHeight, notify=cellHeightChanged)
    currentIndex = pyqtProperty(QModelIndex, currentIndex, setCurrentIndex, notify=currentIndexChanged)
