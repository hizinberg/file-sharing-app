"""
Server receiver of the file
"""
import socket
import tqdm
import os
import time
import psutil

SERVER_HOST = psutil.net_if_addrs()['Wi-Fi'][1][1]


def bluetooth_server():
    SERVER_HOST = psutil.net_if_addrs()['Wi-Fi'][1][1]
    hostMACAddress = psutil.net_if_addrs()['Bluetooth Network Connection'][0][1]
    hostMACAddress=hostMACAddress.replace('-',':')
    port = 15
    backlog = 1
    size = 1024
    s = socket.socket(socket.AF_BLUETOOTH, socket.SOCK_STREAM, socket.BTPROTO_RFCOMM)
    s.bind((hostMACAddress,port))
    s.listen(backlog)
    print("litening for bluetooth connections")

    client, address = s.accept()
    print(f"connection request from {client}")
    print(client,address)
    client.send(SERVER_HOST.encode('utf-8'))
    client.close()
    print("Closing socket")
    s.close()
    return True




def receive_file():
    SERVER_HOST = psutil.net_if_addrs()['Wi-Fi'][1][1]

    SERVER_PORT = 6050

    BUFFER_SIZE = 10485760//2 #10mb
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
    t=time.time()
    with open(filename, "wb") as f:
        while True:
           
            bytes_read = client_socket.recv(BUFFER_SIZE)
            if not bytes_read:    
               
                break
           
            f.write(bytes_read)
            aspeed=len(bytes_read)//1048576
            print(aspeed)
            progress.update(len(bytes_read))
            print('')
    print(time.time()-t)

    client_socket.close()

    s.close()

if __name__=="__main__":
    bluetooth_server()
    receive_file()
    
