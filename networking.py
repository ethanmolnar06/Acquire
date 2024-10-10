import pickle
import socket
import threading
import uuid

from common import pack_gameState, find_player
from objects.player import Player

# COMM Protocol
PORT = 50545
HEADERSIZE = 8
FORMAT = "utf-8"
DISCONN = "!DISCONNECT!"

class Command:
  def __init__(self, action_obj_key:str, val) -> None:
    action, obj, key = action_obj_key.split()
    # offer support for more granular control later, if deemed necessary
    if action in {"set", 
                  "add", "sub",}:
      self.action = action
    else:
      raise TypeError
    
    if obj in {"server", "client", "tilebag", "board", "player", "stats", "bank",}:
      self.obj = obj
    else:
      raise NameError
    
    if type(key) == str:
      self.key = key
    else:
      raise KeyError
    
    self.val = val
  
  def pack(self) -> bytes:
    return pickle.dumps(self, 5)
  
  def dump(self) -> str:
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
  def __init__(self, addr: str, socket:socket.socket) -> None:
    self.uuid = uuid.uuid4()
    self.addr = addr
    self.socket = socket
    self.comm: list[Command] | None = None
    
    self.thread = KillableThread(target=self.listen, args=(socket))
    self.thread.start()
  
  def close_socket(self):
    if self.socket is not None:
      self.socket.close()
      self.socket = None
  
  def kill_thread(self):
    if self.thread is not None:
      self.thread.kill()
      self.socket = None
  
  def kill(self):
    self.close_socket()
    self.kill_thread()
  
  def listen(self, kill_event:threading.Event, sock:socket.socket):
    while not kill_event.isSet():
      data_len = sock.recv(HEADERSIZE).decode(FORMAT)
      if data_len:
        data: bytes = sock.recv(int(data_len))
        if self.comm is None:
          self.comm = [pickle.loads(data)]
        else:
          self.comm += pickle.loads(data)
        # print(data)
  
  def send(self, command: Command):
    data = command.pack()
    data_len = f"{len(data)}".encode(FORMAT)
    data_len_padded = data_len + b' ' * (HEADERSIZE - len(data_len))
    self.socket.send(data_len_padded)
    self.socket.send(data)
  
  def fetch(self) -> Command | None:
    comm = None
    if self.comm is not None:
      comm = self.comm.pop(0)
    if len(self.comm) == 0:
      self.comm = None
    return comm

def start_server(conn_dict:dict[uuid.UUID, Connection], newGame: bool, gameState: tuple) -> tuple[Connection, dict[uuid.UUID, Connection]]:
  # TCP style
  ip = socket.gethostbyname(socket.gethostname())
  # what ip to use for non-LAN connections?
  # any way to avoid requiring port forwarding?
  # ip = ""
  server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
  server.bind((ip, PORT))
  
  server.listen()
  print(f"Listening at {ip}.")
  
  def accept_conn(kill_event:threading.Event, newGame: bool, gameState: tuple):
    while not kill_event.isSet():
      client, addr = server.accept()
      addr = f"{addr[0]}:{addr[1]}"
      newConn = Connection(addr, client)
      conn_dict[newConn.uuid] = newConn
      print(f"{addr} connected.")
      
      gameStateUpdate = pack_gameState(*gameState)
      handshake = (newGame, gameStateUpdate)
      propagate(conn_dict, Command("set client connection", handshake))
      
      # print(conn_dict)
    server.close()
  
  serverThread = KillableThread(target=accept_conn, args=(newGame, gameState))
  serverThread.start()
  
  return serverThread, conn_dict

def start_client(ip, conn_dict) -> dict[str, Connection]:
  client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
  client.connect((ip, PORT))
  
  hostConn = Connection("server", client)
  conn_dict["server"] = hostConn
  
  return conn_dict

def extrctConns(collection: dict[uuid.UUID, Connection] | list[Player] | list[Connection]) -> set[Connection]:
  if type(collection) == dict:
    return set(collection.values())
  elif type(collection) == list and type(collection[0]) == Player:
    return set(p.conn for p in collection if p.conn is not None)
  elif type(collection) == list and type(collection[0]) == Connection:
    return set(collection)
  else:
    raise TypeError("Invalid propogation destination")

def propagate(dests: dict[uuid.UUID, Connection] | list[Player] | list[Connection], source: Player | Connection | uuid.UUID |None, command: Command):
  conns = extrctConns(dests)
  for conn in conns:
    if conn is None or (type(source) == uuid.UUID and conn.uuid == source) or conn.uuid == source.uuid:
      continue
    conn.send(command)

def fetch_updates(sources: dict[uuid.UUID, Connection] | list[Player] | list[Connection]) -> list[tuple[uuid.UUID, Command]] | list:
  # command order is preserved within each player but NOT between players
  conns = extrctConns(sources)
  updates: list[tuple[uuid.UUID, Command]] = []
  for conn in conns:
    if conn.comm is None:
      continue
    while conn.comm is not None:
      u = (conn.uuid, conn.fetch())
      updates.append(u)
  return updates
