"""
Client that sends the file (uploads)
psutil.net_if_addrs()['Bluetooth Network Connection'][0][1]
"""

import socket
import tqdm
import os
import argparse
import bluetooth
class bluetoothsender:
    def __init__(self):
        self.port=15
        self.sender_bluetooth_server=socket.socket(socket.AF_BLUETOOTH, socket.SOCK_STREAM, socket.BTPROTO_RFCOMM)

    def bluetooth_scanning(self):
        port=15
        restart=True
        devices=bluetooth.discover_devices(lookup_names=True,flush_cache=True)
        return devices

    def bluetooth_connecting(self,device,devices):
        bluetooth_dev=device
        bluetooth_dev_add=devices[bluetooth_dev][0]
        print(f"connecting to device {devices[bluetooth_dev][1]}")
        self.sender_bluetooth_server.connect((bluetooth_dev_add,self.port))
        print("bluetooth device connected")
        serveradd=self.sender_bluetooth_server.recv(1024)
        serveradd=serveradd.decode()
        print("we got the server addr as ",serveradd)
        self.sender_bluetooth_server.close()
        return serveradd

class wifisender():
    def __init__(self):
        self.SEPERATOR="<SEPARATOR>"
        self.BUFFER_SIZE=10485760
        self.sender_client=socket.socket()
        self.port=6050
        self.PERCENTAGE=0
        self.SPEED=0

    def wifi_connect(self,host):
        print(f"[+] Connecting to {host}:{self.port}")
        try:
            self.sender_client.connect((host, self.port))
            print("[+] Connected.")
            return True
        except(Exception):
            print(Exception)
            return False


    def file_receiving(self,filename):
        filesize = os.path.getsize(filename)
        self.sender_client.send(f"{filename}{self.SEPERATOR}{filesize}".encode())
        progress = tqdm.tqdm(range(filesize), f"Sending {filename}", unit="B", unit_scale=True, unit_divisor=1024)
        with open(filename, "rb") as f:
            while True:

                bytes_read = f.read(self.BUFFER_SIZE)
                if not bytes_read:
                    break
                self.sender_client.sendall(bytes_read)
                progress.update(len(bytes_read))
                print(round(progress.miniters*10,3)/10**6)
                self.SPEED=round(progress.miniters*10,3)/10**6
                self.PERCENTAGE=round((progress.n)/filesize*100)
                print('')
                self.ui.sender_progress_bar.setValue(self.PERCENTAGE)

        self.sender_client.close()


if __name__=='__main__':
    filename=r'D:\movies\Reminiscence.2021.720p.English.Esubs.MoviesVerse.Co.mkv'
    bconn=bluetoothsender()
    restart=1
    while restart:
        devices = bconn.bluetooth_scanning()
        for i in devices:
            print(i[1])
        restart=int(input("restart?"))
    device=int(input("enter device"))
    serveradd=bconn.bluetooth_connecting(device,devices)
    print(serveradd)


    wificonn=wifisender()
    wificonn.wifi_connect(serveradd)
    wificonn.file_receiving(filename)