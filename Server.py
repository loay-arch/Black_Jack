import socket
import time
import threading
from Protocol import offer_Message, unpack_request, recv_exact
from ServerGameSession import ServerGameSession
BROADCAST_PORT = 13122


class Server:
    """Handles network connections and client management."""
    def __init__(self):
        # TCP socket which listens for players request to play black jack.
        self.tcp_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.tcp_socket.bind(('0.0.0.0', 0))  # 0 means the OS picks an available port number
        self.tcp_socket.listen()
        self.tcp_port = self.tcp_socket.getsockname()[1]
        self.server_name = "DefinitelyNotRigged"

        # UDP socket which broadcasts offers to play black jack
        self.udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.udp_socket.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        self.udp_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        # we bind the UDP socket to our actual local IP address.
        # this is important because it forces the broadcast to go out through our
        # physical network card (like WiFi) instead of staying inside a virtual interface like WSL.
        self.udp_socket.bind((self.get_local_ip(), 0))
        print(f"Server started, listening on IP address {self.get_local_ip()}")

    def get_local_ip(self):
        """returns the local IP address."""
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))
            ip = s.getsockname()[0]
            s.close()
            return ip
        except:
            return "127.0.0.1"

    def broadcast_offers(self):
        """Sends UDP offers so clients know where to connect."""
        print(f"Server broadcasting on UDP port {BROADCAST_PORT}...")
        while True:
            message = offer_Message(self.tcp_port,self.server_name)
            self.udp_socket.sendto(message, ('<broadcast>', BROADCAST_PORT))
            time.sleep(1)


    def handle_client(self, client_sock):
        """Handle an individual client connection."""
        try:
            original_timeout = client_sock.gettimeout()  # save current socket timeout (could be None = blocking)
            client_sock.settimeout(5.0)

            try:
                data = recv_exact(client_sock, 38)  # block waiting for exactly 38 bytes from client
            except (socket.timeout, ConnectionError):  # client too slow or disconnected
                return
            finally:
                client_sock.settimeout(original_timeout)  # restore original timeout for rest of connection

            rounds , client_name = unpack_request(data)
            if not rounds or not client_name:  # if invalid or malformed request
                return

            game = ServerGameSession(client_sock, rounds, client_name,self.server_name)
            game.play()

        finally:
            client_sock.close()

    def start(self):
        """Starts the server broadcast offers and accept connections."""
        # start broadcasting in background
        threading.Thread(target=self.broadcast_offers, daemon=True).start()

        while True:
            client_sock, addr = self.tcp_socket.accept()
            client_thread = threading.Thread(target=self.handle_client, args=(client_sock,))
            client_thread.start()


if __name__ == "__main__":
    server = Server()
    server.start()