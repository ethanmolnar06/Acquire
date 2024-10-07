import pickle
import socket
import threading
import uuid

# COMM Protocol
PORT = 50545
HEADERSIZE = 8
FORMAT = "utf-8"
DISCONN = "!DISCONNECT!"

class Command:
  def __init__(self, action:str, obj:str, key:str, val:str) -> None:
    if action in {"set", "add", "sub", "rep",}:
      self.action = action
    else:
      raise TypeError
    
    if obj in {"server", "bank", "board", "player", "stats", "tilebag",}:
      self.obj = obj
    else:
      raise NameError
    
    if type(key) == str:
      self.key = key
    else:
      raise KeyError
    
    self.val = val
  
  def pack(self):
    return pickle.dumps(self, 5)
  
  def dump(self):
    return " ".join(self.action, self.obj, self.key)

class KillableThread(threading.Thread):
  def __init__(self, group: None = None, target = None, name: str | None = None, args: tuple | list = (), kwargs: tuple[str | None] | None = None, *, daemon: bool | None = None) -> None:
    self.kill_event = threading.Event()
    print(args)
    if args is None:
      args = (self.kill_event)
    else:
      args = (self.kill_event, *args)
    super().__init__(group, target, name, args, kwargs, daemon=daemon)
  
  def kill(self):
    self.kill_event.set()
    self.join()

class Connection:
  def __init__(self, addr: str, socket:socket.socket = None, thread:KillableThread = None) -> None:
    self.uuid = uuid.uuid4()
    self.addr = addr
    self.socket = socket
    self.thread = thread
    self.data: Command | bytes | None = None
  
  def kill(self):
    if self.socket is not None:
      self.socket.close()
    if self.thread is not None:
      self.thread.kill()

def start_server(conn_dict:dict[uuid.UUID, Connection], saveData: bytes) -> tuple[Connection, dict[uuid.UUID, Connection]]:  
  # TCP style
  ip = socket.gethostbyname(socket.gethostname())
  # ip = ""
  server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
  server.bind((ip, PORT))
  
  server.listen()
  print(f"Listening at {ip}.")
  
  def accept_conn(kill_event:threading.Event, saveData: bytes):
    while not kill_event.isSet():
      client, addr = server.accept()
      client.send(saveData)
      addr = f"{addr[0]}:{addr[1]}"
      print(f"{addr} connected.")
      listen_thread = KillableThread(target=listen, args=(client, addr, conn_dict))
      newConn = Connection(addr, client, listen_thread)
      conn_dict[newConn.uuid] = newConn
      # print(conn_dict)
      listen_thread.start()
    server.close()
  
  accept_conn_thread = KillableThread(target=accept_conn, args=(saveData))
  serverConn = Connection("host", server, accept_conn_thread)
  accept_conn_thread.start()
  
  return serverConn, conn_dict

def start_client(ip, conn_dict) -> dict[str, Connection]:
  client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
  client.connect((ip, PORT))
  
  listen_thread = KillableThread(target=listen, args=(client, "host", conn_dict))
  hostConn = Connection("host", client, listen_thread)
  conn_dict["Server"] = hostConn
  listen_thread.start()
  
  return conn_dict

def listen(kill_event:threading.Event, sock:socket.socket, addr: str, conn_dict: dict[Connection]):
  while not kill_event.isSet():
    data_len, data_type = sock.recv(HEADERSIZE).decode(FORMAT).split()
    if data_len:
      data: bytes = sock.recv(int(data_len))
      unpack = pickle.loads(data) if "Command" in data_type else data
      conn_dict[addr].data = unpack
      # print(data)
  sock.close()

def send(dest:socket.socket, data: Command | bytes):
  pack = data.pack() if type(data) is Command else data
  data_len = f"{len(pack)} {type(data)}".encode(FORMAT)
  data_len_padded = data_len + b' ' * (HEADERSIZE - len(data_len))
  dest.send(data_len_padded)
  dest.send(data)

def propagate(conn_dict:dict[uuid.UUID, Connection], source_socket:socket.socket | None, data):
  for conn in conn_dict:
    if conn["socket"] != source_socket:
      send(conn["socket"], data)

def fetch_updates(conn_dict: dict[uuid.UUID, Connection]) -> list[tuple[uuid.UUID, Command | bytes]]:
  updates: list[tuple[uuid.UUID, Command | bytes]] = []
  for id, d in conn_dict.items():
    if d.data is not None:
      updates.append((id, d.data))
  return updates
