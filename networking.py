import socket, threading

# COMM Protocol
PORT = 50545
HEADERSIZE = 8
FORMAT = "utf-8"
DISCONN = "!DISCONNECT!"

def start_server(conn_dict:dict):  
  # TCP style
  SERVER = socket.gethostbyname(socket.gethostname())
  server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
  server.bind((SERVER, PORT))
  
  server.listen()
  print(f"Listening at {SERVER}.")
  
  def accept_conn():
    while True:
      client, addr = server.accept()
      addr = f"{addr[0]}:{addr[1]}"
      print(f"{addr} connected.")
      listen_thread = threading.Thread(target=listen, args=(client, addr, conn_dict))
      conn_dict[addr] = {"socket": client,
                         "thread": listen_thread,
                         "data": None}
      print(conn_dict)
      listen_thread.start()
  
  accept_conn_thread = threading.Thread(target=accept_conn)
  accept_conn_thread.start()
  
  return server, accept_conn_thread, conn_dict

def start_client(ip):
  client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
  client.connect((ip, PORT))
  
  data = {"Server": {"data": None}}
  listen_thread = threading.Thread(target=listen, args=(client, "Server", data))
  listen_thread.start()
  
  return client, listen_thread, data

def listen(sock:socket.socket, addr, conn_dict):
  connected = True
  while connected:
    msg_len = sock.recv(HEADERSIZE).decode(FORMAT)
    if msg_len:
      data = sock.recv(int(msg_len)).decode(FORMAT)
      if data == DISCONN:
        connected = False
      else:
        conn_dict[addr]["data"] = data
      # print(data)
  
  print(f"{addr} disconnected.")
  sock.close()

def send(dest:socket.socket, data: str):
  # format to str here
  data = str(data)
  msg = data.encode(FORMAT)
  msg_len = str(len(msg)).encode(FORMAT)
  msg_len_padded = msg_len + b' ' * (HEADERSIZE - len(msg_len))
  dest.send(msg_len_padded)
  dest.send(msg)

def fetch_updates(conn_dict):
  updates = []
  for addr, d in conn_dict.items():
    if d["data"] is not None:
      updates.append((addr, d))
  return updates

def propagate(conn_dict, source_socket:socket.socket | None, data):
  for conn in conn_dict:
    if conn["socket"] != source_socket:
      send(conn["socket"], data)

class Command:
  def __init__(self, action:str, obj:str, key:str, val:str) -> None:
    if action in {"set", "add", "sub", "rep", }:
      self.action = action
    else:
      raise TypeError
    
    if obj in {"server", "bank", "board", "player", "stats", "tilebag"}:
      self.obj = obj
    else:
      raise NameError
    
    if type(key) == str:
      self.key = key
    else:
      raise KeyError
    
    self.val = val
