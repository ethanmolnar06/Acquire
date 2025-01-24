import socket
import threading
import uuid
import subprocess
import shutil
from requests import get

from objects.connection import Command, KillableThread, Connection, PORT, DISCONN
from objects.player import Player

class Proxy():
  def __init__(self):
    self.tunnelBuilt = False
    self.proxy_url = None
    self.processKilled = False
    self.thread = KillableThread(target=self.reverse_proxy)
    self.thread.start()
  
  def kill(self):
    self.thread.kill()
  
  def reverse_proxy(self, kill_event:threading.Event):
    lhrun = f"ssh -o ServerAliveInterval=60 -R 80:127.0.0.1:{PORT} nokey@localhost.run".split()
    output_filter = {b"\x1b", b"authenticated", b"https://localhost.run/docs/forever-free/", b"mobile"}
    
    process = subprocess.Popen(lhrun, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL)
    print("[PROXY] Opening Reverse Proxy for Public Clients")
    
    while not kill_event.isSet():
      if process.poll() is not None:
        kill_event.set()
      
      if process.stdout:
        response = process.stdout.readline().strip().decode()
        if response and not any([fil in response.encode() for fil in output_filter]):
          # expecting https://XXXXXXXXXXXXXX.lhr.life
          self.proxy_url = "https://" + response.split("https://")[-1]
          if not self.tunnelBuilt:
            print("[PROXY SUCCESS] Reverse Proxy Open for Public Clients")
            self.tunnelBuilt = True
          else:
            print("[PROXY REFRESHED] New Reverse Proxy Link")
          
    
    if self.proxy_url is None:
      print("[PROXY FAILURE] Reverse Proxy Failed to Connect")
    else:
      print("[PROXY CLOSED] Reverse Proxy Disconnected")
    
    process.kill()
    self.processKilled = True

def start_server(conn_dict:dict[uuid.UUID, Connection], newGame: bool, gameState: tuple) -> tuple[KillableThread, Proxy | None, dict[uuid.UUID, Connection]]:
  server = socket.socket(socket.AF_INET, socket.SOCK_STREAM) # TCP style
  server.settimeout(3.0) # time to wait in sec
  server.bind(("", PORT))
  print(f"[SERVER INITALIZED]")
  
  # region Get IPs
  from common import ALLOW_PUBLIC_IP, ALLOW_REVERSE_PROXY
  ip = None
  possibleips = [ip for ip in socket.gethostbyname_ex(socket.gethostname())[2] if not ip.startswith("127.")]
  ipFilterPrio = ["192.168.0.", "172.16.0.", "10.0.0.",
                  "192.168.1.", "172.16.1.", "10.0.1.",
                  "192.168.",   "172.16.",   "10.0.",
                  "192.",       "172.",      "10."]
  for filter in ipFilterPrio:
    try:
      ip = [ip for ip in possibleips if ip.startswith(filter)][0]
      break
    except IndexError:
      continue
  if ip is None:
    ip = socket.gethostbyname(socket.gethostname())
  listening_str = f"[LISTENING] Listening at {ip} (local)"
  
  reverseProxy = None
  if ALLOW_PUBLIC_IP:
    # region localhost.run reverse proxy
    if ALLOW_REVERSE_PROXY and shutil.which("ssh"):
      reverseProxy = Proxy()
      while reverseProxy.tunnelBuilt is None:
        if reverseProxy.tunnelBuilt and reverseProxy.proxy_url is not None:
          listening_str += f" & {reverseProxy.proxy_url} (public)"
          break
    # endregion
    
    if not ALLOW_REVERSE_PROXY or reverseProxy is None:
      publicip = get('https://api.ipify.org').text
      listening_str += f" & {publicip} (public)"
  # endregion
  
  server.listen()
  print(listening_str)
  
  from common import pack_gameState
  def accept_conn(kill_event:threading.Event, newGame: bool, gameState: tuple):
    while not kill_event.isSet():
      try:
        client, addr = server.accept()
      except TimeoutError:
        # no connections arrived in the time limit
        continue
      
      addr = f"{addr[0]}:{addr[1]}"
      newConn = Connection(addr, client)
      conn_dict[newConn.uuid] = newConn
      print(f"[CONNECTION SUCCESS] New Client Connection from {newConn}")
      
      gameStateUpdate = pack_gameState(*gameState)
      handshake = (newConn.uuid, newGame, gameStateUpdate)
      propagate(conn_dict, None, Command("set client connection", handshake))
    
    print(f"[LISTENING CLOSED] No Longer Listening for New Connections at {ip}")
    server.close()
  
  serverThread = KillableThread(target=accept_conn, args=(newGame, gameState))
  serverThread.start()
  
  return serverThread, reverseProxy, conn_dict

def start_client(ip, conn_dict) -> dict[str, Connection]:
  client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
  client.connect((ip, PORT))
  
  hostConn = Connection("server", client, "AWAITING HANDSHAKE")
  conn_dict["server"] = hostConn
  
  return conn_dict

def extrctConns(collection: dict[uuid.UUID, Connection] | list[Player] | list[Connection]) -> set[Connection]:
  if isinstance(collection, dict):
    return set(collection.values())
  elif isinstance(collection, list) and isinstance(collection[0], Player):
    return set(p.conn for p in collection if p.conn is not None)
  elif isinstance(collection, list) and isinstance(collection[0], Connection):
    return set(collection)
  else:
    raise TypeError("Invalid Source of Connections")

def propagate(dests: dict[uuid.UUID, Connection] | list[Player] | list[Connection], source: uuid.UUID | Player | Connection | None, command: Command):
  conns = extrctConns(dests)
  for conn in conns:
    # should be safe to just drop in for hostLocal
    if conn is None or conn.sock is None:
      continue
    elif isinstance(source, uuid.UUID) and conn.uuid == source:
      continue
    elif isinstance(source, (Player, Connection)) and conn.uuid == source.uuid:
      continue
    # print(conn)
    conn.send(command)

def fetch_updates(sources: dict[uuid.UUID, Connection] | list[Player] | list[Connection]) -> list[tuple[uuid.UUID, Command]]:
  # command order is preserved within each player but NOT between players
  conns = extrctConns(sources)
  updates: list[tuple[uuid.UUID, Command]] = []
  # print([str(conn) for conn in conns])
  for conn in conns:
    if conn.comm is None:
      continue
    while conn.comm is not None:
      # print([str(comm) for comm in conn.comm])
      u = (conn.uuid, conn.fetch())
      updates.append(u)
  return updates
