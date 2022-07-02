from UI_Build import Ui_MainWindow
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
import receiver
import sender
import tqdm
import psutil
import socket
import sys
import os
import time,traceback,sys

class WorkerSignals(QObject):
    finished=pyqtSignal()
    error=pyqtSignal(tuple)
    result=pyqtSignal(object)
    progress=pyqtSignal(int)

class send_file_thread(QThread):
    SendercountChanged = pyqtSignal(list)

    def __init__(self,*args,**kwargs):
        super(send_file_thread,self).__init__()
        self.args=args
        self.kwargs=kwargs
        self.signals=WorkerSignals()

        self.kwargs['progress_callback']=self.signals.progress

    def run(self):

        self.args=self.args[0]
        filesize = os.path.getsize(self.args[0])
        self.args[1].send(f"{self.args[0]}{self.args[2]}{filesize}".encode())

        progress = tqdm.tqdm(range(filesize), f"Sending {self.args[0]}", unit="B", unit_scale=True, unit_divisor=1024)
        with open(self.args[0], "rb") as f:
            while True:

                bytes_read = f.read(self.args[3])
                if not bytes_read:
                    break
                self.args[1].sendall(bytes_read)
                progress.update(len(bytes_read))
                print(round(progress.miniters*10,3)/10**6)
                self.args[4]=round(progress.miniters*10,3)/10**6
                self.args[5]=round((progress.n)/filesize*100)
                print('')
                self.SendercountChanged.emit([self.args[4], self.args[5]])

class Connection_Thread_Receiver(QRunnable):
    def __init__(self,fn,*args,**kwargs):
        super(Connection_Thread_Receiver, self).__init__()
        self.fn=fn
        self.args=args
        self.kwargs=kwargs
        self.signals=WorkerSignals()

        self.kwargs['progress_callback']=self.signals.progress
    @pyqtSlot()
    def run(self):
        try:
            result=self.fn()
        except:
            traceback.print_exc()
            exctype,value=sys.exc_info()[:2]
            self.signals.error.emit((exctype,value,traceback.format_exc()))

        else:
            self.signals.result.emit(result)
        finally:
            self.signals.finished.emit()

class receive_Thread(QThread):

    ReceivercountChanged = pyqtSignal(list)

    def __init__(self,*args,**kwargs):
        super(receive_Thread,self).__init__()
        self.args=args
        self.kwargs=kwargs
        self.signals=WorkerSignals()
        self.kwargs['progress_callback']=self.signals.progress


    def run(self):
        blu_conn_success=receiver.bluetooth_server()
        if blu_conn_success:
            SERVER_HOST = psutil.net_if_addrs()['Wi-Fi'][1][1]
            SERVER_PORT = 6050
            BUFFER_SIZE = 10485760 // 2  # 10mb
            SEPARATOR = "<SEPARATOR>"
            s = socket.socket()
            s.bind((SERVER_HOST, SERVER_PORT))
            s.listen(5)
            print(f"[*] Listening as {SERVER_HOST}:{SERVER_PORT}")
            client_socket, address = s.accept()
            print(f"[+] {address} is connected.")
            received = client_socket.recv(BUFFER_SIZE).decode()
            filename, filesize = received.split(SEPARATOR)
            filename = os.path.basename(filename)
            filesize = int(filesize)
            progress = tqdm.tqdm(range(filesize), f"", unit="B", unit_scale=True, unit_divisor=1024)
            t = time.time()
            with open(filename, "wb") as f:
                while True:
                    bytes_read = client_socket.recv(BUFFER_SIZE)
                    if not bytes_read:
                        break
                    f.write(bytes_read)
                    progress.update(len(bytes_read))
                    PERCENTAGE = round((progress.n) / filesize * 100)
                    SPEED = round(progress.miniters * 10,3) / 10 ** 6
                    self.ReceivercountChanged.emit([PERCENTAGE,SPEED])
                    print('')
            print(time.time() - t)
            client_socket.close()
            s.close()


class MainWindow(QMainWindow,QDialog):
    def __init__(self):
        QMainWindow.__init__(self)
        QDialog.__init__(self)
        self.main_win=QMainWindow()
        self.ui=Ui_MainWindow()
        self.ui.setupUi(self.main_win)

        self.ui.stackedWidget.setCurrentWidget(self.ui.startpage)
        self.ui.sendbutton.clicked.connect(self.send_page_event)
        self.ui.receivebutton.clicked.connect(self.receive_page_events)
        self.threadpool=QThreadPool()


        self.scannedDevices=[]
        self.bluetoothObj=sender.bluetoothsender()
        self.wifiobj=sender.wifisender()


    def show(self):
        self.main_win.show()
    def send_page_event(self):
        self.ui.stackedWidget.setCurrentWidget(self.ui.sendpage)
        self.ui.sender_backbutton.clicked.connect(lambda:self.ui.stackedWidget.setCurrentWidget(self.ui.startpage))
        self.ui.sender_scan_button.clicked.connect(self.start_scan)
        self.ui.sender_scan_for_devices_label.hide()
        self.ui.sender_listWidget.hide()
        QCoreApplication.processEvents()

    def start_scan(self):
        self.ui.sender_scan_for_devices_label.show()
        self.ui.sender_backbutton.hide()
        self.ui.sender_scan_button.hide()
        cts=Connection_Thread_Receiver(self.bluetoothObj.bluetooth_scanning)
        cts.signals.result.connect(self.finished_scanning)
        cts.signals.result.connect(self.done)
        cts.signals.finished.connect(self.com)
        self.threadpool.start(cts)


    def receive_page_events(self):
        self.ui.stackedWidget.setCurrentWidget(self.ui.receivepage)
        self.ui.receiver_backbutton.clicked.connect(lambda:self.ui.stackedWidget.setCurrentWidget(self.ui.startpage))
        self.ui.receiver_start_connection_button.clicked.connect(self.start_receive)
        self.ui.receiver_waiting_for_connections_label.hide()

        QCoreApplication.processEvents()


    def start_receive(self):
        if self.ui.receiver_start_connection_button.text()=="start connection":
            self.ui.receiver_backbutton.hide()
            self.ui.receiver_start_connection_button.show()
            self.ui.receiver_start_connection_button.setText("stop")
            self.ui.receiver_waiting_for_connections_label.show()
            self.rec = receive_Thread()
            self.rec.start()
            self.rec.ReceivercountChanged.connect(self.onCountChanged_receiver)


            QCoreApplication.processEvents()
        else:
            self.ui.receiver_waiting_for_connections_label.hide()
            self.ui.receiver_backbutton.show()
            self.ui.receiver_start_connection_button.setText("start connection")

            QCoreApplication.processEvents()


    def done(self):
        print("bluetooth scanning successfully completed")
    def finished_scanning(self,msg):
        self.ui.sender_scan_for_devices_label.setText("Found Devices")
        self.scannedDevices=msg
        for i in msg:
            self.ui.sender_listWidget.addItem(i[1])
        self.ui.sender_listWidget.show()
        self.ui.sender_listWidget.doubleClicked.connect(self.receiver_selection)
    def com(self):
        print("completed")


    def receiver_selection(self,item):
        receiver_dev=self.ui.sender_listWidget.currentItem().text()
        pos=list(zip(*self.scannedDevices))[1].index(receiver_dev)


        receiverAddress=self.bluetoothObj.bluetooth_connecting(pos,self.scannedDevices)
        connection_flag=self.wifiobj.wifi_connect(receiver_dev)
        if connection_flag:
            self.ui.sender_listWidget.hide()
            self.ui.sender_scan_button.hide()
            self.ui.sender_scan_for_devices_label.adjustSize()
            self.ui.sender_scan_for_devices_label.setText("connected to device")
            self.ui.stackedWidget.setCurrentWidget(self.ui.sender_progression_page)
            self.ui.sender_progress_bar.hide()
            self.ui.sender_speed_label.hide()
            self.ui.sender_receiver_label.setText(receiver_dev)
            self.ui.sender_select_file_button.clicked.connect(self.filechoose)
        else:
            self.ui.sender_listWidget.hide()
            self.ui.sender_scan_for_devices_label.setText("connection failed")


    def filechoose(self):
        file=QFileDialog.getOpenFileName(self,"Open File",".")
        print(file[0])
        filesize=os.path.getsize(file[0])
        args=[file[0],self.wifiobj.sender_client,self.wifiobj.SEPERATOR,self.wifiobj.BUFFER_SIZE,self.wifiobj.SPEED,self.wifiobj.PERCENTAGE]
        self.send_file_t=send_file_thread(args)
        print(args[0])
        self.ui.sender_progress_bar.show()
        self.ui.sender_speed_label.show()
        self.send_file_t.start()
        self.send_file_t.SendercountChanged.connect(self.onCountChanged)

        QCoreApplication.processEvents()

    def receiveprogress(self):
        self.rec_thread=receive_Thread()
        self.rec_thread.start()
        self.rec_thread.ReceivercountChanged.connect(self.onCountChanged_receiver)
    def onCountChanged(self,value):
        self.ui.sender_progress_bar.setValue(value[1])
        self.ui.sender_speed_label.adjustSize()
        self.ui.sender_speed_label.setText(str(round(value[0],1))+"MB/s")
    def onCountChanged_receiver(self,value):
        self.ui.receiver_waiting_for_connections_label.hide()
        self.ui.receiver_progress_bar.setValue(value[0])
        self.ui.receiver_speed_label.setText(str(round(value[1],1))+"MB/s")

if __name__=="__main__":
    app=QApplication(sys.argv)
    main_win=MainWindow()
    main_win.show()
    sys.exit(app.exec_())