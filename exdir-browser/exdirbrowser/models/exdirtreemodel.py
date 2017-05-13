import exdir
from PyQt5.QtCore import *
from PyQt5.QtQml import *

class ExdirTreeModel(QAbstractItemModel):
    class Role:
        Name = Qt.UserRole + 0
        Path = Qt.UserRole + 1
        Type = Qt.UserRole + 2
    Q_ENUMS(Role)
    
    def __init__(self, parent):
        super().__init__(parent)
        self._source = None
        self.root = None

    def index(self, row, column, parent):
        if not self.hasIndex(row, column, parent):
            return QModelIndex()
        parentNode = None
        if not parent.isValid():
            if self.root is None:
                return QModelIndex()
            parentNode = self.root
        else:
            parentNode = self.item(parent)

        childItem = parentNode.child(row)
        if childItem:
            index = self.createIndex(row, column, childItem)
            # index = QPersistentModelIndex(self.createIndex(row, column, childItem))
            # index = QModelIndex(row, column, childItem, self)
            return index
        else:
            return QModelIndex()
    
    @pyqtSlot(QAbstractItemModel, QAbstractItemModel, result=str)
    def check(self, model1, model2):
        return "blah"

    def parent(self, index):
        if not index.isValid():
            return QModelIndex()
            
        childItem = self.item(index)
        parentItem = childItem.parentItem

        if parentItem == self.root:
            return QModelIndex()

        return self.createIndex(parentItem.row, 0, parentItem)

    def rowCount(self, parent):
        if parent.column() > 0:
            return 0

        if not parent.isValid():
            if self.root == None:
                return 0
            return len(self.root.children())

        parentItem = self.item(parent)
        if parentItem.needsChildIteration:
            filePath = self.source.toLocalFile()
            # TODO replace with Python exdir file
            file = exdir.File(filePath)
            object = file[parentItem.path]
            if isinstance(object, exdir.core.Group):
                group = object
                self.addChildObjects(parentItem, group, parentItem.depth + 1)
            parentItem.needsChildIteration = False
        return len(parentItem.children())

    def columnCount(self, parent):
        if parent.column() > 0:
            return 0
        return 1
    
    def data(self, index, role):
        if not index.isValid():     
            return QVariant()

        indexNode = self.item(index)
        if not indexNode:        
            return QVariant()

        value = {
            self.Role.Name: indexNode.name,
            self.Role.Path: indexNode.path,
            self.Role.Type: indexNode.type
        }.get(role, "")

        return QVariant(value)

    def roleNames(self):
        roles = {
            self.Role.Name: b"name",
            self.Role.Path: b"path",
            self.Role.Type: b"type",
        }
        return roles

    def path(self, index):
        if not index.isValid():        
            return ""

        indexNode = self.item(index)
        return indexNode.path
        
    @pyqtSlot(QModelIndex, result=QObject)
    def item(self, index):
        if not index.isValid():
            return None
        return index.internalPointer()

    def source(self):
        return self._source

    def setSource(self, source):
        if self._source == source:
            return

        self._source = source
        self.loadFile()
        self.sourceChanged.emit(source)

    def addChildObjects(self, parent, parentGroup, depth):
        row = 0
        for key in parentGroup.keys():
            object = parentGroup[key]

            type = ""
            info = ""

            # TODO needs major rewrite
            # if isinstance(object, exdir.Attribute):
                # type = "Attribute"
            if isinstance(object, exdir.core.Dataset):
                type = "Dataset"
            # elif isinstance(object, exdir.core.Datatype):
                # type = "Datatype"
            elif isinstance(object, exdir.core.File):
                type = "File"
            elif isinstance(object, exdir.core.Group):
                type = "Group"
                
            # group = object
            # info = QString("%1 objects").arg(group.keys().size())
                
            # dataset = object
            # if dataset.dimensionCount() == 1:                
            #     info = QString("vector of size %1").arg(dataset.extents()[0])
            # elif dataset.dimensionCount() == 2:
            #     info = QString("%1x%2 matrix")
            #             .arg(dataset.extents()[0])
            #             .arg(dataset.extents()[1])
            # elif dataset.dimensionCount() == 3:                
            #     info = QString("%1x%2x%3 cube")
            #             .arg(dataset.extents()[0])
            #             .arg(dataset.extents()[1])
            #             .arg(dataset.extents()[2])
            # else:
            #     info = QString("%1 dimensional object").arg(dataset.dimensionCount())

            node = ExdirTreeItem(row, 0, depth + 1,
                                                key,
                                                parent.path + "/" + key,
                                                type,
                                                parent)
            node.setInfo(info)

            if isinstance(object, exdir.core.Group):            
                node.needsChildIteration = True

            row += 1



    def loadFile(self):
        if not self.source.isValid() or self.source.isEmpty():        
            print("Not loading because", self.source)
            return

        filePath = self.source.toLocalFile()
        filenameOnly = filePath
        fileInfo = QFileInfo(filePath)
        if fileInfo.exists():
            filenameOnly = fileInfo.fileName()

        file = exdir.File(filePath)
        self.root = ExdirTreeItem(0, 0, 0, "", "", "", None)
        self.beginInsertRows(QModelIndex(), 0, 0)
        fileItem = ExdirTreeItem(0, 0, 1, filenameOnly, "", "File", self.root)
        self.endInsertRows()
        self.addChildObjects(fileItem, file, 0)
        self.dataChanged.emit(QModelIndex(), QModelIndex())
        
    sourceChanged = pyqtSignal(QUrl)
    source = pyqtProperty(QUrl, source, setSource, notify=sourceChanged)

class ExdirTreeItem(QObject):
    def __init__(self, row_, column_, depth_, name_, path_, type, parent):
        super().__init__(parent)
        self.row = row_
        self.column = column_
        self.depth = depth_
        self._name = name_
        self._path = path_
        self._type = type
        self._info = ""
        self.parentItem = parent
        self.needsChildIteration = False
        
    def child(self, row):
        return self.children()[row]

    def name(self):
        return self._name

    def path(self):
        return self._path

    def type(self):
        return self._type

    def info(self):
        return self._info

    def setName(self, name):
        if self._name == name:
            return

        self._name = name
        self.nameChanged.emit()

    def setPath(self, path):
        if self._path == path:
            return

        self._path = path
        self.pathChanged.emit()

    def setType(self, type):
        if self._type == type:
            return

        self._type = type
        self.typeChanged.emit()

    def setInfo(self, info):
        if self._info == info:
            return

        self._info = info
        self.infoChanged.emit()

    nameChanged = pyqtSignal()
    pathChanged = pyqtSignal()
    typeChanged = pyqtSignal()
    infoChanged = pyqtSignal()
    name = pyqtProperty(str, name, setName, notify=nameChanged)
    path = pyqtProperty(str, path, setPath, notify=pathChanged)
    type = pyqtProperty(str, type, setType, notify=typeChanged)
    info = pyqtProperty(str, info, setInfo, notify=infoChanged)
