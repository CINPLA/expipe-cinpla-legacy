from PyQt5.QtCore import *
from PyQt5.QtQml import *
import exdir


class ExdirDatasetModel(QAbstractTableModel):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._currentSlice = 0
        self._sliceCount = 0
        self._source = QUrl()
        self.hasData = False
        self._hasUnsavedChanges = False
        self._dataset = ""
        self._datasetObject = None
        self._data = None

    def rowCount(self, parent=QModelIndex()):
        if not self.hasData:
            return 0

        if len(self._data.shape) > 0:
            return self._data.shape[0]
        else:
            return 0

    def columnCount(self, parent=QModelIndex()):
        if not self.hasData:
            return 0

        if len(self._data.shape) > 1:
            return self._data.shape[1]
        else:
            return 1

    def inBounds(self, index):
        if not self.hasData:
            return False

        shape = self._data.shape
        if len(shape) > 0:
            if index.row() < 0 or index.row() >= shape[0]:
                return False
        if len(shape) > 1:
            if index.column() < 0 or index.column() >= shape[1]:
                return False
        return True

    def hasUnsavedChanges(self):
        return self._hasUnsavedChanges

    def currentSlice(self):
        return self._currentSlice

    def sliceCount(self):
        return self._sliceCount

    def data(self, index, role):
        if not self.hasData:
            return QVariant()

        if role == Qt.DisplayRole:
            if self.inBounds(index):
                if len(self._data.shape) > 2:
                    return self._data[index.row(), index.column(), self._currentSlice]
                elif len(self._data.shape) > 1:
                    return self._data[index.row(), index.column()]
                elif len(self._data.shape) > 0:
                    return self._data[index.row()]
                else:
                    return QVariant()
            else:
                print("Requested index out of bounds", index.row(), index.column())
            return QVariant(0.0)
        else:
            return QVariant()

    def setData(self, index, value, role):
        if not index.isValid():
            return False

        if not self.inBounds((index)):
            return False

        try:
            value = float(value)
        except:
            print("WARNING: Value is not a number:", value, type(value))
            return False

        if self.dimensionCount > 2:
            self._data[self.currentSlice, index.row(), index.column()] = value
        elif self.dimensionCount > 1:
            self._data[index.row(), index.column()] = value
        else:
            self._data[index.row()] = value
        
        self._hasUnsavedChanges = True
        self.dataChanged.emit(index, index)
        self.hasUnsavedChangesChanged.emit(self._hasUnsavedChanges)
        return True

    def roleNames(self):
        return {
            Qt.DisplayRole: "value"
        }

    def dataset(self):
        return self._dataset

    def source(self):
        return self._source

    def setDataset(self, dataSet):
        if self._dataset == dataSet:
            return

        self._dataset = dataSet
        self.load()
        self.datasetChanged.emit(dataSet)

    def setSource(self, source):
        if self._source == source:
            return

        self._source = source
        self.load()
        self.sourceChanged.emit(source)

    def setCurrentSlice(self, currentSlice):
        if self._currentSlice == currentSlice:
            return

        self._currentSlice = currentSlice
        self.dataChanged.emit(index(0, 0), index(rowCount() - 1, columnCount() - 1))
        self.currentSliceChanged.emit(currentSlice)

    def setSliceCount(self, sliceCount):
        if self._sliceCount == sliceCount:
            return

        self._sliceCount = sliceCount
        self.sliceCountChanged.emit(sliceCount)

    def load(self):
        self.hasData = False
        self.dimensionCount = 0

        if not self._source.isValid() or self._dataset == "":
            self.dataChanged.emit(QModelIndex(), QModelIndex())
            return

        fileNameString = self.source.toLocalFile()
        datasetName = self._dataset
        file = exdir.File(fileNameString)

        dataset = file[datasetName]
        if isinstance(dataset, exdir.core.Dataset):
            self.hasData = True
            self._datasetObject = dataset
            self._data = dataset.data # TODO point to dataset when exdir doesn't reload file one every read

            shape = dataset.shape
            self.dimensionCount = len(shape)

            if self.dimensionCount == 3:
                self.setSliceCount(shape[0])

        if not self.hasData or self.dimensionCount != 3:
            self.setSliceCount(1)

        self._hasUnsavedChanges = False
        self.sliceCountChanged.emit(self._sliceCount)
        self.dataChanged.emit(QModelIndex(), QModelIndex())
        self.hasUnsavedChangesChanged.emit(self._hasUnsavedChanges)

    @pyqtSlot(result=bool)
    def save(self):
        print("Saving file")
        # # TODO keep working on the same file when loading/saving
        if not self.source.isValid() or not self._dataset:        
            return False
        # 
        fileNameString = self._source.toLocalFile()
        datasetName = self._dataset
        # # qDebug() << "Loading" << self.dataset << "in" << fileNameString
        file = exdir.File(fileNameString)
        # 
        if isinstance(file[datasetName], exdir.core.Dataset):
            dataset = file[datasetName]
            dataset.data = self._data
        #
        self._hasUnsavedChanges = False
        self.hasUnsavedChangesChanged.emit(self.hasUnsavedChanges)
        return True

    datasetChanged = pyqtSignal(str)
    sourceChanged = pyqtSignal(QUrl)
    hasUnsavedChangesChanged = pyqtSignal(bool)
    currentSliceChanged = pyqtSignal(int)
    sliceCountChanged = pyqtSignal(int)

    source = pyqtProperty(QUrl, source, setSource, notify=sourceChanged)
    dataset = pyqtProperty(str, dataset, setDataset, notify=datasetChanged)
    currentSlice = pyqtProperty(int, currentSlice, setCurrentSlice, notify=currentSliceChanged)
    hasUnsavedChanges = pyqtProperty(bool, hasUnsavedChanges, notify=hasUnsavedChangesChanged)
    sliceCount = pyqtProperty(int, sliceCount, notify=sliceCountChanged)
