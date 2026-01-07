import socket
from Protocol import unpack_offer
from ClientGameSession import ClientGameSession


UDP_PORT = 13122


class Client:
    """Handles network discovery and connection to the server."""

    def __init__(self):
        self.server_ip = None
        self.server_port = None

    def listen_for_offers(self):
        """
        Listen for a server offer to play black jack.
        """
        print("Client started, listening for offer requests...")
        # we create our socket, since its UDP socket we dont need any connection setup
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        sock.bind(("", UDP_PORT))

        try:
            while True:
                # the buffer size is exactly 39 bytes becuase we know that the offer message is supposed to be 39
                # bytes long.
                data, addr = sock.recvfrom(39)
                server_tcp_port, server_name = unpack_offer(data)
                if server_tcp_port and server_name:
                    self.server_ip = addr[0]
                    self.server_port = server_tcp_port
                    print(f"Received offer from {self.server_ip}, attempting to connect...")
                    sock.close()
                    return server_name
                else:
                    print("Received invalid packet, ignoring...")
        finally:
            sock.close()

    def connect_and_play(self,server_name):
        """Establishes TCP connection and runs the black jack game session."""
        tcp_sock = None
        try:
            tcp_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            # to prevent any connections issues we wait up to 5 seconds to connect. in case we dont we give up and look for offers agim.
            tcp_sock.settimeout(5.0)
            tcp_sock.connect((self.server_ip, self.server_port))
            print(f'Connected to {self.server_ip}:{self.server_port}\n')
            game_session = ClientGameSession(tcp_sock,server_name)
            game_session.play()
        except Exception as e:
            print(f"Client error: {e}")
        finally:
            if tcp_sock:
                try:
                    tcp_sock.close()
                except:
                    pass


if __name__ == "__main__":
    client = Client()
    while True:
        server_name =client.listen_for_offers()
        client.connect_and_play(server_name)