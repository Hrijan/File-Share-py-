import socket
import threading
import ipaddress
import os

discoveredDevices = []

def print_progress(completed, total, message_prefix):
    width = 50  # Width of the progress bar
    progress_percentage = int((completed * 100) / total)
    progress = (progress_percentage * width) // 100
    
    bar = f"{message_prefix} ["
    for i in range(width):
        if i < progress:
            bar += "#"
        else:
            bar += " "
    bar += f"] {progress_percentage}%"
    print("\r" + bar, end='')
    if completed == total:
        print()  # Print a new line after completion

def handleClient(clientSocket):
    try:
        fileNameSize = int(clientSocket.recv(10).decode('utf-8'))
        fileName = clientSocket.recv(fileNameSize).decode('utf-8')
        
        fileSize = int(clientSocket.recv(10).decode('utf-8'))

        currentDir = os.path.dirname(os.path.realpath(__file__))

        filePath = os.path.join(currentDir, fileName)

        with open(filePath, 'wb') as f:
            bytesReceived = 0
            while bytesReceived < fileSize:
                chunk = clientSocket.recv(4096)
                if not chunk:
                    break
                f.write(chunk)
                bytesReceived += len(chunk)
                print_progress(bytesReceived, fileSize, "Receiving")
            print(f"\nFile {fileName} and saved in {currentDir}.\n")
    except Exception as e:
        print(f"")

def listenOnPort(port=3000):
    #https://docs.python.org/3/howto/sockets.html
    serverSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    serverSocket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1) 
    serverSocket.bind(('', port))
    serverSocket.listen()
    print(f"Listening on port {port} for incoming files...")
    while True:
        clientSocket, address = serverSocket.accept()
        threading.Thread(target=handleClient, args=(clientSocket,)).start()

def sendFile(targetIp, filePath, port=3000):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        try:
            sock.connect((targetIp, port))
            fileName = os.path.basename(filePath)
            fileSize = os.path.getsize(filePath)

            # a bytes-like object is required, not 'str' error
            #https://stackoverflow.com/questions/33054527/typeerror-a-bytes-like-object-is-required-not-str-when-handling-file-conte
        
            sock.send(str(len(fileName)).zfill(10).encode('utf-8'))
            sock.send(fileName.encode('utf-8'))

            sock.send(str(fileSize).zfill(10).encode('utf-8'))

            with open(filePath, 'rb') as f:
                bytesSent = 0
                while True:
                    chunk = f.read(4096)
                    if not chunk:
                        break
                    sock.sendall(chunk)
                    bytesSent += len(chunk)
                    print_progress(bytesSent, fileSize, "Sending")
            print("File sent successfully.")
        except Exception as e:
            print(f"Could not send file to {targetIp}: {e}")

#Error scanning 192.168.0.0: str, bytes or bytearray expected, not IPv4Address
#Not even touching the errors, just hard code the port each time

def scanPort(ip, port=3000):
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(1)
        result = sock.connect_ex((ip, port)) 
        if result == 0: 
            discoveredDevices.append(ip)
        sock.close()
    except Exception as e:
        print(f"Error scanning {ip}: {e}")

def scanNetwork(network, port=3000):
    for ip in ipaddress.IPv4Network(network):
        threading.Thread(target=scanPort, args=(str(ip), port)).start()

def userInterface():
    while True:
        print("\nOptions:")
        print("1. Send a file")
        print("2. Exit")
        choice = input("Select an option: ")
        if choice == "1":
            if not discoveredDevices:
                print("No devices discovered on the network.")
            else:
                print("Discovered Devices:")
                for id, ip in enumerate(discoveredDevices, start=1):
                    print(f"{id}. {ip}")
                try:
                    selection = int(input("Select a device to send file to by number: ")) - 1
                    targetIp = discoveredDevices[selection]
                    filePath = input("Enter the full path of the file to send: ")
                    sendFile(targetIp, filePath)
                except (IndexError):
                    print("Invalid selection. Please enter a valid number.")
        elif choice == "2":
            print("Exiting...")
            break
        else:
            print("Invalid option, please try again.")

if __name__ == "__main__":
    os.system('cls' if os.name == 'nt' else 'clear')
    print ("Welcome to DirectShare!")
    scanNetwork('192.168.0.0/24')
    threading.Thread(target=listenOnPort, daemon = True).start()
    #https://stackoverflow.com/questions/4330111/meaning-of-daemon-property-on-python-threads
    userInterface()
