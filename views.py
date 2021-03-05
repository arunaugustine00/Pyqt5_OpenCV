import numpy as np
import random, cv2, sys, time, threading
from matplotlib import cm
from PyQt5 import QtMultimedia, QtGui, QtCore, QtWidgets
from PyQt5.QtCore import Qt, QThread, QTimer, QPoint
from PyQt5.QtWidgets import QMainWindow, QWidget, QPushButton, QWidget, \
                QMenu, QVBoxLayout, QHBoxLayout, QApplication, QLabel, QAction, QFileDialog
from PyQt5.QtGui import QFont, QPainter, QImage, QTextCursor
from pyqtgraph import ImageView
import pyqtgraph as pg
import queue as Queue

IMG_SIZE    = 1, 1
IMG_FORMAT  = QImage.Format_RGB888
DISP_MSEC   = 50                # Delay between display cycles
image_queue = Queue.Queue()     # Queue to hold images
capturing   = True              # Flag to indicate capturing

# Grab images from the camera (separate thread)
def grab_images(cam_num, queue):
    cap = cv2.VideoCapture(0)
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, IMG_SIZE[0])
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, IMG_SIZE[1])
    while capturing:
        if cap.grab():
            retval, image = cap.retrieve(0)
            if image is not None and queue.qsize() < 2:
                queue.put(image)
            else:
                time.sleep(DISP_MSEC / 1000.0)
    cap.release()

# Image widget
class ImageWidget(QWidget):
    def __init__(self, parent=None):
        super(ImageWidget, self).__init__(parent)
        self.image = None

    def setImage(self, image):
        self.image = image
        self.setMinimumSize(image.size())
        self.update()

    def paintEvent(self, event):
        qp = QPainter()
        qp.begin(self)
        if self.image:
            qp.drawImage(QPoint(0, 0), self.image)
        qp.end()

class StartWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.capture = None
        
        # self.camera = camera        
        self.central_widget = QWidget()
        self.central_widget.setStyleSheet("background-color:#3A426B");

        #--------------------------button------------------------
        self.button_start = QPushButton('Start Video', self.central_widget)
        self.button_start.setGeometry(QtCore.QRect(110, 40, 161, 61))
        self.button_start.setStyleSheet("background-color: #A2A6B9")
        self.button_start.setStyleSheet("padding-left: 5px; padding-right: 3px;""padding-top: 1px; padding-bottom: 1px;")
        self.button_start.setCheckable(True)
        self.button_start.released.connect(self.stop_movie)

        self.button_part = QPushButton('Part Placed', self.central_widget)
        self.button_part.setGeometry(QtCore.QRect(500, 40, 161, 61))
        self.button_part.setStyleSheet("background-color: #A2A6B9")
        self.button_part.setStyleSheet("padding-left: 5px; padding-right: 3px;""padding-top: 1px; padding-bottom: 1px;")
        
        #-----------------------text------------------------------
        self.part_status  = QLabel("Result :",self.central_widget)
        self.part_status.setGeometry(QtCore.QRect(120, 500, 100, 20))
        self.part_status.setAlignment(Qt.AlignCenter)
        self.part_status.setStyleSheet("background-color: #E1E1E6")
        
        self.text = QLabel(self.central_widget)
        self.text.setGeometry(QtCore.QRect(300, 500, 50, 20))
        self.text.setAlignment(Qt.AlignCenter)
        self.text.setStyleSheet("background-color: #E1E1E6")
                
        self.context = ["Good", "Bad"]

        #-------------------------Video Display------------------------

        self.disp1 = ImageWidget(self.central_widget) 
        self.disp1.setGeometry(QtCore.QRect(110, 150, 300, 300)) 

        self.disp2 = ImageWidget(self.central_widget) 
        self.disp2.setGeometry(QtCore.QRect(440, 150, 300, 300)) 


        # self.image_view1 = ImageView(self.central_widget)
        # self.image_view1.ui.histogram.hide()
        # self.image_view1.ui.roiBtn.hide()
        # self.image_view1.ui.menuBtn.hide()
        # self.image_view1.setGeometry(QtCore.QRect(110, 150, 300, 300))

        # self.image_view2 = ImageView(self.central_widget)
        # self.image_view2.ui.histogram.hide()
        # self.image_view2.ui.roiBtn.hide()
        # self.image_view2.ui.menuBtn.hide()
        # self.image_view2.setGeometry(QtCore.QRect(440, 150, 300, 300))


        #--------------------------Layout------------------------------
        self.setCentralWidget(self.central_widget)
        self.setGeometry(0, 0, 800, 688)


        #------------------button action performance-------------------
        self.button_start.clicked.connect(self.start_movie)
        self.button_part.clicked.connect(self.predict)   

        #---------------------------Menu Bar Tools-----------------------
        # Create new action
        openAction = QAction(QtGui.QIcon('open.png'), '&Open', self)
        openAction.setShortcut('Ctrl+O')
        openAction.setStatusTip('Open movie')
        openAction.triggered.connect(self.openFile)

        # Create exit action
        exitAction = QAction(QtGui.QIcon('exit.png'), '&Exit', self)
        exitAction.setShortcut('Ctrl+Q')
        exitAction.setStatusTip('Exit application')
        exitAction.triggered.connect(self.closeApplication)

        # Create PLC Setting action
        plcSetttingAction = QMenu('&PLC Setting', self)
        plcSetttingAction.setStyleSheet("background-color:#46507F")
        # Create PLC Setting action
        communicationAction = QAction('&Commnication', self)
        communicationAction.triggered.connect(self.communication)
        plcSetttingAction.addAction(communicationAction)
        # Create PLC Setting action 
        parameterAction = QAction('&Parameter', self)
        parameterAction.triggered.connect(self.parameter)
        plcSetttingAction.addAction(parameterAction)
        # Create PLC Setting action 
        axisSettingAction = QAction('&Axis Setting', self)
        axisSettingAction.triggered.connect(self.axis_setting)
        plcSetttingAction.addAction(axisSettingAction)

        # Create History Action 
        historyAction = QMenu('&History', self)
        historyAction.setStyleSheet("background-color:#46507F")
        # Create History Action 
        reportAction = QAction('&Report', self)
        reportAction.triggered.connect(self.report)
        historyAction.addAction(reportAction)
        # Create History Action 
        pictureAction = QAction('&Picture', self)
        pictureAction.triggered.connect(self.report)
        historyAction.addAction(pictureAction)

        # Create Camera Action 
        cameraAction = QAction('&Camera', self)
        cameraAction.setShortcut('Ctrl+K')
        cameraAction.setStatusTip('Camera application')
        cameraAction.triggered.connect(self.kamera)

        # Create Test Case action
        testCaseAction = QMenu('&Test Case', self)
        testCaseAction.setStyleSheet("background-color:#46507F")
        # Create Test Case action
        alignmentAction = QAction('&Alignment', self)
        alignmentAction.triggered.connect(self.alignment)
        testCaseAction.addAction(alignmentAction)
        # Create Test Case action 
        crackAction = QAction('&Crack', self)
        crackAction.triggered.connect(self.crack)
        testCaseAction.addAction(crackAction)
        # Create Test Case action 
        dustAction = QAction('&Dust', self)
        dustAction.triggered.connect(self.dust)
        testCaseAction.addAction(dustAction)

        # Create Recipe Action 
        recipeAction = QAction('&Recipe', self)
        recipeAction.triggered.connect(self.recipe)

        # Create menu bar and add action
        menuBar = self.menuBar()
        menuBar.setStyleSheet("background-color:#46507F")

        fileMenu1 = menuBar.addMenu('&Menu')
        fileMenu2 = menuBar.addMenu('&Help')
        # fileMenu.addAction(newAction)
        fileMenu1.addAction(openAction)
        fileMenu1.addMenu(plcSetttingAction)
        fileMenu1.addMenu(historyAction)
        fileMenu1.addAction(cameraAction)
        fileMenu1.addMenu(testCaseAction)
        fileMenu1.addAction(recipeAction)
        fileMenu1.addAction(exitAction)

    #-------------------------------------Functions------------------------------------ 
    
    def openFile(self):
        fileName, _ = QFileDialog.getOpenFileName(self, "Open",QtCore.QDir.homePath())

        if fileName:
            self.mediaPlayer.setMedia(
                QtMultimedia.QMediaContent(QtCore.QUrl.fromLocalFile(fileName)))
            #self.playButton.setEnabled(True)

    def closeApplication(self):
        choice = QtGui.QMessageBox.question(self, 'Message','Do you really want to exit?',QtGui.QMessageBox.Yes | QtGui.QMessageBox.No)
        if choice == QtGui.QMessageBox.Yes:
            self.close()
        else:
            pass


    def communication(self):
        pass

    def parameter(self):
        pass

    def axis_setting(self):
        pass

    def report(self):
        pass

    def picture(self):
        pass

    def kamera(self):
        pass

    def alignment(self):
        pass

    def crack(self):
        pass

    def dust(self):
        pass

    def recipe(self):
        pass



    def predict(self):
        text = random.choice(self.context)
        if  text == 'Good':
            self.text.setText(text)
            self.text.setStyleSheet("background-color: #00ff00")
            
        else:
            self.text.setText(text)
            self.text.setStyleSheet("background-color: #ff0000")

        
    # Start image capture & display
    def start_movie(self):
        if self.button_start.isCheckable():
            if self.button_start.isChecked():
                global capturing
                capturing = True
                self.button_start.setText("Stop Video")
                self.timer = QTimer(self)           # Timer to trigger display
                self.timer.timeout.connect(lambda: self.show_image(image_queue, self.disp1, 1))
                self.timer.timeout.connect(lambda: self.show_image(image_queue, self.disp2, 1))
                self.timer.start(DISP_MSEC)         
                self.capture_thread = threading.Thread(target=grab_images, args=(0, image_queue))
                self.capture_thread.start()         # Thread to grab images

    def stop_movie(self):
        if self.button_start.isCheckable():
            if not self.button_start.isChecked():
                self.button_start.setText("Start Video")
                global capturing
                capturing = False
                # self.capture_thread.join()

    # Fetch camera image from queue, and display it
    def show_image(self, imageq, display, scale):
        if not imageq.empty():
            image = imageq.get()
            if image is not None and len(image) > 0:
                img = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
                self.display_image(img, display, scale)

    # Display an image, reduce size if required
    def display_image(self, img, display, scale=10):
        disp_size = img.shape[1]//scale, img.shape[0]//scale
        disp_bpl = disp_size[0] * 3
        qimg = QImage(img.data, disp_size[0], disp_size[1], IMG_FORMAT)
        display.setImage(qimg)

    def flush(self):
        pass

    def closeEvent(self, event):
        global capturing
        capturing = False
        self.capture_thread.join()