from PyQt5.QtCore import *
import exdir


class ExdirAttributesModel(QAbstractTableModel):
    class Role:
        Name = Qt.UserRole + 0
        Value = Qt.UserRole + 1

    def __init__(self, parent=None):
        super().__init__(parent)
        self._path = ""
        self._source = QUrl()
        self._data = {}
        self._hasUnsavedChanges = False
        self._count = 0

    def rowCount(self, parent):
        return len(self._data)

    def columnCount(self, parent):
        return 1

    def inBounds(self, index):
        if index.row() >= 0 and index.column() >= 0 and index.column() < 1 and index.row() < len(self._data):
            return True
        return False

    def hasUnsavedChanges(self):
        return self._hasUnsavedChanges

    def count(self):
        return self._count

    def data(self, index, role):
        if not self.inBounds(index):
            return QVariant()

        if role == self.Role.Name:
            return list(self._data.keys())[index.row()]

        if role == self.Role.Value:
            return list(self._data.values())[index.row()]

        return QVariant()

    def setData(self, index, value, role):
        if not index.isValid():
            return False

        if not self.inBounds(index):
            return False

        if not isinstance(value, float):
            return False

        doubleValue = value
        self._data[self._data.keys().at(index.row())] = doubleValue
        self._hasUnsavedChanges = True
        dataChanged.emit(index, index)
        hasUnsavedChangesChanged.emit(self._hasUnsavedChanges)
        return True

    def roleNames(self):
        return {
            self.Role.Name: b"name",
            self.Role.Value: b"value",
        }

    def path(self):
        return self._path

    def source(self):
        return self._source

    def setPath(self, dataSet):
        if self._path == dataSet:
            return

        self._path = dataSet
        self.load()
        self.pathChanged.emit(dataSet)

    def setSource(self, source):
        if self._source == source:
            return

        self._source = source
        self.load()
        self.sourceChanged.emit(source)

    def vectorToString(self, vec):
        return "[" + ", ".join(vec) + "]"

    def load(self):
        if not self._source.isValid() or not self._path:
            self.beginRemoveRows(QModelIndex(), 0, len(self._data))
            self._data.clear()
            self.endRemoveRows()
            self.dataChanged.emit(QModelIndex(), QModelIndex())
            return

        fileNameString = self._source.toLocalFile()
        path = self._path
        file = exdir.File(fileNameString)

        self.beginRemoveRows(QModelIndex(), 0, len(self._data) - 1)
        self._data.clear()
        self.endRemoveRows()
        object = file[path]
        self.beginInsertRows(QModelIndex(), 0, len(object.attrs) - 1)
        for key in object.attrs:
            # TODO handle complex attributes
            self._data[key] = str(object.attrs[key])
        self.endInsertRows()
        self.setCount(len(self._data))
        self._hasUnsavedChanges = False
        self.dataChanged.emit(QModelIndex(), QModelIndex())
        self.hasUnsavedChangesChanged.emit(self._hasUnsavedChanges)


    def save(self):
        # TODO keep working on the same file when loading/saving

    #    qDebug() << "Saving file"
    #    if not self._source.isValid() or self._path.isEmpty():#        return False
    #
    #    fileNameString = QQmlFile.urlToLocalFileOrQrc(self._source)
    #    datasetName = self._path.toStdString()
    #    qDebug() << "Loading" << self._path << "in" << fileNameString
    #    File file(fileNameString.toStdString(), h5cpp.File.OpenMode.ReadWrite)

    #    qDebug() << file[datasetName].isDataset()
    #    if file[datasetName].isDataset():#        file[self._path.toStdString()] = self._data
    #
    #    self._hasUnsavedChanges = False
    #    hasUnsavedChangesChanged.emit(self._hasUnsavedChanges)
        return True


    def setCount(self, count):
        if self._count == count:
            return

        self._count = count
        self.countChanged.emit(count)

    pathChanged = pyqtSignal(str, arguments=["path"])
    sourceChanged = pyqtSignal(QUrl, arguments=["source"])
    hasUnsavedChangesChanged = pyqtSignal(bool, arguments=["hasUnsavedChanges"])
    countChanged = pyqtSignal(int, arguments=["count"])

    source = pyqtProperty(QUrl, source, setSource, notify=sourceChanged)
    path = pyqtProperty(str, path, setPath, notify=pathChanged)
    hasUnsavedChanges = pyqtProperty(bool, hasUnsavedChanges, notify=hasUnsavedChangesChanged)
    count = pyqtProperty(int, count, setCount, notify=countChanged)
