# A simple version of my Copy Random Files program. 
# Set the number of files you want to copy, the folder you want to copy from (root), and the folder you want to copy to (destination).
# See the advanced version here: https://github.com/jang-w/Copy-Random-Files-Advanced

import os
import sys
import shutil
import random
import inspect
import datetime
import collections
from pathlib import Path
from time import perf_counter, time
from PySide2.QtWidgets import *
from PySide2.QtGui import *
from PySide2.QtCore import *

class WorkerSignals(QObject):
    countSignal = Signal()
    logSignal = Signal(object)
    timeSignal = Signal()
    finishedSignal = Signal()

class RunMandalaWorker(QRunnable):
    def run(self):
        window.runMandala()

class MainWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.noWrap = '<p style="white-space:pre">'
        self.wasEnabled = {}
        self.listOfPaths = collections.defaultdict(bool)

        self.threadpool = QThreadPool()
        self.mandala = RunMandalaWorker()
        self.mandala.setAutoDelete(False)

        self.setupUi()
        self.setupSignals()

        self.settings = QSettings('Jang', 'MandalaLite')
        self.globalSettingsRestore()
        
    def setupSignals(self):
        self.signals = WorkerSignals()
        self.signals.countSignal.connect(lambda: self.progressBar.setValue(self.count))
        self.signals.logSignal.connect(lambda s: self.logBlock.append(s))

    def makeSpin(self, lo, hi, enabled):
        name = QSpinBox()
        name.setRange(lo, hi)
        name.setMaximumWidth(60)
        name.setEnabled(enabled)
        return name
    
    def createGroupLabel(self, name):
        label = QLabel(name)
        label.setObjectName('groupLabel')
        return label
    
    # SETUP UI PARTS
            
    def setupFileCountUi(self): # self.fileCountG
        self.fileCountLabel = QLabel('Count')

        self.numFilesCount = self.makeSpin(1, 1000000000, True)

        countL = QHBoxLayout()
        countL.addWidget(self.fileCountLabel)
        countL.addWidget(self.numFilesCount)
        
        self.fileCountG = QGroupBox('File count')
        self.fileCountG.setLayout(countL)

    def setupRootUi(self): # self.rootG
        self.rootLabel = self.createGroupLabel('Root')

        self.root = QDir.rootPath()
        self.rootDirectory = self.root

        self.rootCombo = QComboBox()
        self.rootCombo.addItem(self.root)

        self.browseRootButton = QPushButton(' Browse')

        self.rootCombo.currentTextChanged.connect(self.changeRoot)
        self.browseRootButton.clicked.connect(self.browseRoot)

        rootControls = QHBoxLayout()
        rootControls.addWidget(self.rootCombo)
        rootControls.addWidget(self.browseRootButton)

        rootL = QVBoxLayout()
        rootL.addWidget(self.rootLabel)
        rootL.addLayout(rootControls)

        self.rootG = QGroupBox()
        self.rootG.setLayout(rootL)

    def setupDestUi(self): # self.destG
        self.destLabel = self.createGroupLabel('Destination')

        self.dest = QDir.homePath()
        self.destDirectory = self.dest

        self.destCombo = QComboBox()
        self.destCombo.addItem(self.dest)

        self.browseDestButton = QPushButton(' Browse')

        self.destCombo.currentTextChanged.connect(self.changeDestination)
        self.browseDestButton.clicked.connect(self.browseDestination)

        destLabelL = QHBoxLayout()
        destLabelL.addWidget(self.destLabel)
        destLabelL.addStretch()

        destControls = QHBoxLayout()
        destControls.addWidget(self.destCombo)
        destControls.addWidget(self.browseDestButton)

        destL = QVBoxLayout()
        destL.addLayout(destLabelL)
        destL.addLayout(destControls)

        self.destG = QGroupBox()
        self.destG.setLayout(destL)

    def setupRunSection(self): # self.runSection
        # PROGRESS BAR
        self.runLabel = QLabel('Run')

        self.progressBar = QProgressBar()
        self.progressBar.setValue(0)
        self.progressBar.setFormat('%v')
        self.progressBar.setTextVisible(True)
        self.progressBar.setAlignment(Qt.AlignCenter)

        # RUN BUTTON
        self.runButton = QPushButton('Start')
        self.runButton.clicked.connect(self.runMandalaPush)

        # STOP BUTTON
        self.stopButton = QPushButton('Stop')
        self.stopButton.clicked.connect(self.stopMandalaPush)
        self.stopButton.setVisible(False)
        self.stopTracker = False

        # LOG DISPLAY
        self.logLabel = QLabel('Log')

        self.logBlock = QTextBrowser()
        self.logBlock.setMinimumHeight(175)
        self.logBlock.setMaximumHeight(175)
        self.logBlock.setLineWrapMode(QTextEdit.NoWrap)

        runRow = QHBoxLayout()
        runRow.addWidget(self.progressBar)
        runRow.addWidget(self.runButton)
        runRow.addWidget(self.stopButton) 

        self.runSection = QVBoxLayout()
        self.runSection.addWidget(self.logBlock)
        self.runSection.addLayout(runRow)

    # SETUP UI

    def setupUi(self):
        self.setupFileCountUi()
        self.setupRootUi()
        self.setupDestUi()
        self.setupRunSection()

        masterLayout = QVBoxLayout()
        masterLayout.addWidget(self.fileCountG)
        masterLayout.addWidget(self.rootG)
        masterLayout.addWidget(self.destG)
        masterLayout.addLayout(self.runSection)

        self.setLayout(masterLayout)
        self.setWindowTitle('Default - Copy Random Files')
        self.show()

    ### ROOT AND DESTINATION METHODS ###

    def resetPathToStart(self):
        os.chdir(self.root)
        return Path.cwd()

    def changeRoot(self):
        self.root = Path(self.rootCombo.currentText())

    def changeDestination(self):
        self.dest = Path(self.destCombo.currentText())

    def browseRoot(self):
        self.rootDirectory = QFileDialog.getExistingDirectory(self, "Select Root Folder", str(self.root))

        if self.rootDirectory:
            if self.rootCombo.findText(self.rootDirectory) == -1:
                self.rootCombo.addItem(self.rootDirectory)
            self.rootCombo.setCurrentIndex(self.rootCombo.findText(self.rootDirectory))
            self.root = Path(self.rootDirectory)

    def browseDestination(self):
        self.destDirectory = QFileDialog.getExistingDirectory(self, "Select Destination Folder",
                str(self.dest))

        if self.destDirectory:
            if self.destCombo.findText(self.destDirectory) == -1:
                self.destCombo.addItem(self.destDirectory)
            self.destCombo.setCurrentIndex(self.destCombo.findText(self.destDirectory))
            self.dest = Path(self.destDirectory)

    ### RUN METHODS ###

    def assignGlobalVariables(self):
        # File Count Variables
        self.numberOfFiles = self.numFilesCount.value()

        # Root and Destination
        self.root = Path(self.rootCombo.currentText())
        self.dest = Path(self.destCombo.currentText())

        self.startAbsolute = os.path.abspath(self.root)
        self.rename2 = ' '
        self.isAppendLog = False
        self.count = 0
        self.bytesInCurrentFolder = 0
        self.stallLimit = 30
        self.startFolderTime = perf_counter() 
        self.startStallTime = perf_counter()

    def runMandala(self):
        self.assignGlobalVariables()
        
        self.touchedFiles = collections.defaultdict(bool)  # type: ignore
        self.touchedFolders = collections.defaultdict(bool)  # type: ignore

        if self.stopTracker:
            self.stopMandala()
            return

        self.dest = Path(self.destCombo.currentText())

        self.count = 0
        self.dest = self.createFolders(self.dest)
        
        self.startFolderTime = perf_counter() 
        self.startStallTime = perf_counter()
        mainPath = self.resetPathToStart() 

        self.progressBar.setRange(0, self.numberOfFiles)

        for currFile in range(self.numberOfFiles):
            if self.stopTracker:
                self.stopMandala()
                return
            if self.touchedFolders[self.startAbsolute] and self.isTimedOut(self.startStallTime):
                break

            while not self.touchedFolders[self.startAbsolute] and not self.isTimedOut(self.startStallTime):
                if self.stopTracker:
                    self.stopMandala()
                    return
                mainPathAbsolute = os.path.abspath(mainPath)
                # Try to get main path
                try:
                    if not self.listOfPaths[mainPathAbsolute]:
                        self.listOfPaths[mainPathAbsolute] = os.listdir(mainPath)
                except PermissionError:
                    self.touchedFolders[mainPathAbsolute] = True 
                    mainPath = self.resetPathToStart()
                    continue
                    
                # If folder is empty
                if (len(self.listOfPaths[mainPathAbsolute]) == 0):
                    self.touchedFolders[mainPathAbsolute] = True
                    mainPath = self.resetPathToStart()
                    
                # If the folder is not empty
                else: 
                    # Chooses random path and stores absolute path
                    randomPath = Path(random.choice(self.listOfPaths[mainPathAbsolute]))
                    randomPathAbsolute = os.path.abspath(randomPath)

                    # If touched, try again:
                    if self.touchedFiles[randomPathAbsolute] or self.touchedFolders[randomPathAbsolute]:
                        self.touchFolderIfAllFilesTouched(self.listOfPaths[mainPathAbsolute], mainPathAbsolute)
                        mainPath = self.resetPathToStart()  

                    # If random path is folder
                    if randomPath.is_dir():
                        try:
                            os.chdir(randomPath)
                            mainPath = Path.cwd()

                        except PermissionError:
                            self.touchedFolders[randomPathAbsolute] = True 
                            mainPath = self.resetPathToStart()

                    # If random path is file:
                    elif randomPath.is_file():
                        # Get size
                        self.touchedFiles[randomPathAbsolute] = True
                        randomPathSize = os.path.getsize(randomPath)
                        randomPathRelative = os.path.relpath(randomPath, self.root)
                        # If file copy is valid
                        if self.copyFilesToTarget(currFile, randomPath, self.dest, randomPathSize):
                            if not self.isAppendLog:
                                self.log.write(f'{currFile+1}: {randomPathRelative}\n')
                                self.signals.logSignal.emit(f'{currFile+1}: {randomPathRelative}')
                            else:
                                self.dummyLog.write(f'{currFile+1}: {randomPathRelative}\n')
                                self.signals.logSignal.emit(f'{currFile+1}: {randomPathRelative}')
                                
                            self.bytesInCurrentFolder += randomPathSize
                            self.count += 1
                            self.signals.countSignal.emit()
                            self.startStallTime = perf_counter()
                            self.signals.timeSignal.emit()
                            
                            mainPath = self.resetPathToStart()                               
                            break
                        # If file is invalid
                        else: 
                            mainPath = self.resetPathToStart()      

        ##################################################   END OF FOLDER  ##################################################           
        # Create and write log at the end of folder
        self.stopMandala()

    def copyFilesToTarget(self, fileNum, source, dest, sourceSize):
        sourceAbsolute = os.path.abspath(source)
        sourceName = source.name
        try:
            x = 2
            while (dest / f'{sourceName}').exists():
                if sourceSize == os.path.getsize(dest / f'{sourceName}'):
                    return False
                sourceName = source.stem + f' ({x})' + source.suffix
                x += 1
            shutil.copy(sourceAbsolute, dest / f'{sourceName}')
            return True
        except PermissionError:
            return False

    def createFolders(self, target):
        if Path(target/f'!{target.name}_log.txt').exists():
            self.isAppendLog = True
        else:
            self.isAppendLog = False
        self.log = open(target/f'!{target.name}_log.txt', 'a', encoding='utf-8')
        self.dummyFile = self.log.name + '.bak'
        self.dummyLog = open(target/self.dummyFile, 'a', encoding='utf-8')
        return target
    
    def touchFolderIfAllFilesTouched(self, listOfPath, absolutePath):
        for fileFolder in listOfPath:
            path = os.path.abspath(fileFolder)
            if self.touchedFiles[path] or self.touchedFolders[path]:
                pass
            else:
                return
        self.touchedFolders[absolutePath] = True
    

    ### PROGRESS, TIMER METHODS ###

    def isTimedOut(self, startStallTime):
        endStallTime = perf_counter()
        if endStallTime - startStallTime > self.stallLimit: 
            return True
        else: 
            return False

    def runMandalaPush(self):
        for name, obj in inspect.getmembers(self):
            if isinstance(obj, QWidget) and not (name in ['stopButton', 'logBlock']):
                self.wasEnabled[name] = obj.isEnabled()

        for name, obj in inspect.getmembers(self):
            if isinstance(obj, QWidget) and not (name in ['stopButton', 'logBlock']):
                obj.setEnabled(False)

        self.progressBar.reset()

        self.runButton.setVisible(False)
        self.stopButton.setVisible(True)
        self.stopTracker = False

        self.threadpool.globalInstance().start(self.mandala)

    def stopMandalaPush(self):
        self.stopTracker = True

    def stopMandala(self):
        self.signals.finishedSignal.emit()
        
        self.dummyLog.close()
        self.log.close()
        statusLog, statusLogApp = self.writeStatusLog()
        self.prependStatusToLog(statusLog)
        self.signals.logSignal.emit(statusLogApp)

        self.runButton.setVisible(True)
        self.stopButton.setVisible(False)
        self.dest = Path(self.destCombo.currentText())
        for name, obj in inspect.getmembers(self):
            if isinstance(obj, QWidget) and not (name in ['stopButton', 'logBlock']):
                obj.setEnabled(self.wasEnabled[name])
            

    ### LOG METHODS ###

    def writeStatusLog(self):
        endFolderTime = perf_counter()
        endStallTime = perf_counter()
        currentDate = datetime.datetime.now().strftime('%B %d, %Y')
        currentTime = datetime.datetime.now().strftime('%I:%M:%S%p')
        status = ''
        timeOut = self.isTimedOut(self.startStallTime)

        if self.count == self.numberOfFiles:
            status = f'SUCCESS: {self.count}/{self.numberOfFiles} files copied'
        elif timeOut and self.count == 0 and self.isCreateFolders: 
            status = f'NO FILES FOUND: timed out | folder deleted'
        elif self.touchedFolders[self.startAbsolute] and self.count == 0 and self.isCreateFolders: 
            status = f'NO FILES FOUND: all files searched | folder deleted'
        elif self.touchedFolders[self.startAbsolute]: 
            status = f'ALL FILES SEARCHED: {self.count}/{self.numberOfFiles} files copied'
        elif timeOut: 
            status = f'TIMED OUT: {self.count}/{self.numberOfFiles} files copied'
        elif self.stopTracker:
            status = f'STOPPED: {self.count}/{self.numberOfFiles} files copied'       
        statusLog = f'''------------------------------------------------------------------------
    {status}
    ------------------------------------------------------------------------
    Date:\t\t{currentDate}
    Time:\t\t{currentTime}
    Start:\t\t{self.root} 
    Destination:\t{self.dest}
    Total size:\t{self.byteToMbGb(self.bytesInCurrentFolder)}
    Total runtime:\t{round(endFolderTime - self.startFolderTime, 2)}s      
    ------------------------------------------------------------------------'''
        statusLogApp = f'''------------------------------------------------------------------------
    {status}
    ------------------------------------------------------------------------
    Date:\t{currentDate}
    Time:\t{currentTime}
    Start:\t{self.root} 
    Destination:\t{self.dest}
    Total size:\t{self.byteToMbGb(self.bytesInCurrentFolder)}
    Total runtime:\t{round(endFolderTime - self.startFolderTime, 2)}s      
    ------------------------------------------------------------------------'''
        return statusLog, statusLogApp

    def prependStatusToLog(self, status):
        # IF ITS A NEW LOG, APPEND STATUS
        dummyLogAbsolute = os.path.abspath(self.dummyLog.name)
        logAbsolute = os.path.abspath(self.log.name)
        if not self.isAppendLog:
            with open(logAbsolute, 'r', encoding='utf-8') as read_obj, open(dummyLogAbsolute, 'w', encoding='utf-8') as write_obj:
                write_obj.write(status + '\n')
                for status in read_obj:
                    write_obj.write(status)
            os.remove(logAbsolute)
            os.rename(dummyLogAbsolute, logAbsolute)
        else:
            with open(dummyLogAbsolute, 'r', encoding='utf-8') as read_obj, open(logAbsolute, 'a', encoding='utf-8') as write_obj:
                write_obj.write(status + '\n')
                for status in read_obj:
                    write_obj.write(status)
            os.remove(dummyLogAbsolute)

    def byteToMbGb(self, bytesInCurrentFolder):
            BYTE_TO_MEGABYTE = 9.53674316406 * 10**(-7)
            BYTE_TO_GIGABYTE = 9.31322575 * 10**(-10)
            byteInGigabyte = 1073741824
            if bytesInCurrentFolder < byteInGigabyte - 1:
                return f'{round(bytesInCurrentFolder * BYTE_TO_MEGABYTE, 2)} MB'
            else:
                return f'{round(bytesInCurrentFolder * BYTE_TO_GIGABYTE, 2)} GB'

    ### SETTINGS METHODS ###

    def closeEvent(self, event):
        # Saves geometry, help, invalid and tab position
        self.globalSettingsSave()

    def globalSettingsSave(self):
        # Save geometry
        self.settings.setValue('size', self.size())
        self.settings.setValue('pos', self.pos())

        for name, obj in inspect.getmembers(self):
            if isinstance(obj, QComboBox):
                items = []
                for item in range(obj.count()):
                    items.append(obj.itemText(item))
                self.settings.setValue(name, items)  # save combobox selection to registry

                index = obj.currentIndex()  # get current index from combobox
                text = obj.itemText(index)  # get the text for current index
                self.settings.setValue(f'current{name}', text)
            
            if isinstance(obj, QSpinBox):
                value = obj.value()
                self.settings.setValue(name, value)

    def globalSettingsRestore(self):
        # Restore geometry  
        self.resize(self.settings.value('size', QSize(500, 500)))
        self.move(self.settings.value('pos', QPoint(60, 60)))

        for name, obj in inspect.getmembers(self):
            if isinstance(obj, QComboBox):
                obj.clear()
                allItems = (self.settings.value(name))
                if allItems != None:
                    obj.addItems(allItems)
                
                value = (self.settings.value(f'current{name}'))
                if obj.findText(value) == -1:
                    obj.addItem(value)
                obj.setCurrentIndex(obj.findText(value))
            
            if isinstance(obj, QSpinBox):
                value = self.settings.value(name)
                if value != None:
                    try:
                        obj.setValue(value)
                    except TypeError:
                        obj.setValue(int(value))

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = MainWindow()
    #with open('CRFStyleSheet.qss', 'r') as f:
    #    style = f.read()
    #    window.setStyleSheet(style)
    sys.exit(app.exec_())