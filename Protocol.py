import struct
MAGIC_COOKIE = 0xabcddcba
MESSAGE_TYPE_OFFER = 0x2
MSG_TYPE_REQUEST = 0x3
MSG_TYPE_PAYLOAD = 0x4
UDP_PORT = 13122



def offer_Message(server_port,server_name):
    """
        Packs the 'Offer' packet (Server -> Client).
        Format: Magic Cookie (4B), Type (1B), Server Port (2B), Server Name (32B)
        Total size: 4 + 1 + 2 + 32 = 39 bytes
        """
    server_name_bytes = server_name.encode('utf-8')
    server_name_bytes=server_name_bytes.ljust(32, b'\x00')
    return struct.pack('!IBH32s',MAGIC_COOKIE,MESSAGE_TYPE_OFFER,server_port,server_name_bytes)


def unpack_offer(packet):
    """
    Unpacks the 'Offer' packet to get the server port.
    Returns: server_port (int) or None if invalid.
    """
    try:
        # we expect exactly 39 bytes. ff we get less or more itss not our packet
        if len(packet) != 39:
            return None,None
        cookie, msg_type, server_port, name_bytes = struct.unpack('!IBH32s', packet)
        # validation checks
        if cookie != MAGIC_COOKIE:
            return None,None
        if msg_type != MESSAGE_TYPE_OFFER:
            return None,None
        server_name = name_bytes.decode('utf-8').rstrip('\x00')
        return server_port, server_name
    except Exception as e:
        print(f"Error unpacking offer: {e}")
        return None,None

def request_Message(num_of_rounds,client_name):
    """
            Packs the 'request' packet (Client -> Server).
            Format: Magic Cookie (4B), Type (1B), Number Of Rounds (1B), Client Team Name (32B)
            Total size: 4 + 1 + 1 + 32 = 38 bytes
            """
    client_name_bytes = client_name.encode('utf-8')
    client_name_bytes=client_name_bytes.ljust(32, b'\x00')
    return struct.pack("!IBB32s",MAGIC_COOKIE,MSG_TYPE_REQUEST,num_of_rounds,client_name_bytes)

def unpack_request(packet):
    """
     Unpacks the 'request' packet to get the number of rounds.
     Returns: number of rounds (int) or None if invalid.
     """
    if len(packet) != 38:
        return None,None
    cookie, msg_type, rounds, name_bytes = struct.unpack('!IBB32s',packet)
    if cookie != MAGIC_COOKIE or msg_type != MSG_TYPE_REQUEST :
        return None,None
    client_name = name_bytes.decode('utf-8').rstrip('\x00')
    return rounds ,client_name

def pack_Client_Payload(decision):
    """
       Packs the client decision (Client -> Server).
       Format: Magic Cookie (4B), Type (1B), decision (5B)
       Total size: 4 + 1 + 5 = 10 bytes
      """
    if decision == "Hit":
        decision = "Hittt"
    decision_bytes = decision.encode('utf-8')
    return struct.pack('!IB5s', MAGIC_COOKIE, MSG_TYPE_PAYLOAD, decision_bytes)


def unpack_client_payload(packet):
    """
    Unpacks the client's decision.
    Returns: 'Hit' , 'Stand', or None.
    """
    try:
        if len(packet) != 10:
            return None
        cookie, msg_type, decision_bytes = struct.unpack('!IB5s', packet)
        if cookie != MAGIC_COOKIE or msg_type != MSG_TYPE_PAYLOAD:
            return None
        decision = decision_bytes.decode('utf-8')
        if decision == "Hittt":
            return "Hit"
        return decision
    except:
        return None


def pack_server_payload(result, rank, suit):
    """
    Packs the game state (Server -> Client).
    Format: Magic (4B) + Type (1B) + Result (1B) + Rank (2B) + Suit (1B)
    """

    return struct.pack('!IBBHB', MAGIC_COOKIE, MSG_TYPE_PAYLOAD, result, rank, suit)


def unpack_server_payload(packet):
    """
    Unpacks the game state.
    Returns: tuple (result, rank, suit) or None.
    """
    try:
        if len(packet) != 9:  # 4 + 1 + 1 + 2 + 1 = 9 bytes
            return None

        cookie, msg_type, result, rank, suit = struct.unpack('!IBBHB', packet)

        if cookie != MAGIC_COOKIE or msg_type != MSG_TYPE_PAYLOAD:
            return None

        return result, rank, suit
    except:
        return None
def recv_exact(sock, size):
    """Makes sure we receive exactly size bytes."""
    data = b''
    while len(data) < size:
        chunk = sock.recv(size - len(data))
        if not chunk:
            raise ConnectionError("Server disconnected")
        data += chunk
    return data
