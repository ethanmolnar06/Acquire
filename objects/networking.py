import socket
import threading
import uuid
import subprocess
import shutil
import re
from random import randint
from io import BytesIO
from typing import Callable
from requests import get

from objects.connection import Command, KillableThread, Connection, PORT, DISCONN
from objects.player import Player

class Proxy():
  prox: dict[str, dict[str, str | re.Pattern]] = {
      "serveo.net": { # https://groups.google.com/g/serveo & https://github.com/u1i/tools/blob/master/serveo.md
        "subdom": "",
        "port": str(randint(13948, 58472)),
        "success": re.compile(r"Forwarding (?P<p>\w+) \w+ from (?:\w+?:\/\/)?(?P<u>\w+?.serveo.net|[\w.]+?:\d+)"),
      }, 
      # "localhost.run": { # https://localhost.run/docs/ 
      #   "subdom": "",
      #   "port": f"80",
      #   "success": re.compile(r"\w+?\.lhr\.life tunneled with tls termination, (?P<p>\w+?):\/\/(?P<u>\w+?.\.lhr\.life)"),
      # },
    }
  
  def __init__(self):
    self.tunnelBuilt = False
    self.protocol = None
    self.hostname = None
    self.addr = None
    self.port = None
    
    for px in self.prox.keys():
      self.port = self.prox[px]["port"]
      ssh_cmd = f"ssh -o ServerAliveInterval=60 -R {self.prox[px]["subdom"] + self.port}:127.0.0.1:{PORT} nokey@{px}".split()
      
      def validate(stdout: bytes) -> tuple[str] | None:
        self._proxy_print("stdout ==", stdout.strip().decode())
        match = self.prox[px]["success"].search(stdout.strip().decode())
        self._proxy_print("matchObj ==", match)
        if match is None:
          return
        protocol_url = (match.group("p").upper(), match.group("u"))
        self._proxy_print("groups ==", protocol_url)
        return protocol_url
      
      try:
        testrun = del_ansi(subprocess.run(ssh_cmd, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, timeout=2).stdout)
      except subprocess.TimeoutExpired as e:
        testrun = del_ansi(e.stdout)
      cleaned_std = [l for l in BytesIO(testrun).readlines() if l]
      lastline = len(cleaned_std)
      self._proxy_print(cleaned_std, lastline)
      
      if validate(testrun):
        print("[PROXY] Opening Reverse Proxy for Public Clients")
        break
    
    self.process = subprocess.Popen(ssh_cmd, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, process_group=0)
    self.thread = KillableThread(target=self.reverse_proxy, args=(validate, lastline))
    self.thread.start()
  
  def _proxy_print(self, *var):
    from common import PRINT_PROXY_DEBUG
    if PRINT_PROXY_DEBUG:
      print(*var)
  
  def kill(self):
    self.process.kill()
    self.thread.kill()
  
  def fetch_ip(self):
    if self.protocol == "TCP":
      self.addr = socket.gethostbyname(self.hostname)
    elif self.protocol == "HTTPS":
      self.addr = socket.gethostbyname(self.hostname)
    self._proxy_print(" [[", self.protocol, self.hostname, self.addr, self.port, "]] ")
  
  def reverse_proxy(self, kill_event: threading.Event, validate: Callable[[str], tuple[str] | None], lastline: int):
    i = 1
    while self.process.poll() is None:
      if kill_event.is_set():
        self.process.kill()
      cur_line = del_ansi(self.process.stdout.readline())
      response = validate(cur_line)
      self._proxy_print(response)
      if i == lastline and not self.tunnelBuilt and response is None:
        break
      elif response is None:
        i += 1 if cur_line else 0
        continue
      
      self.protocol = response[0]
      self.hostname = response[1].removesuffix(f":{self.port}")
      try:
        self.fetch_ip()
        if not self.tunnelBuilt:
          print("[PROXY SUCCESS] Reverse Proxy Established")
          self.tunnelBuilt = True
          continue
        else:
          print(f"[PROXY REFRESHED] New Reverse Proxy Link {self.addr}")
      except socket.error as e:
        self.hostname = None
        self.kill()
        raise e
    
    if self.hostname is None:
      print("[PROXY FAILURE] Reverse Proxy Not Online, Try Port Forwarding")
    else:
      print("[PROXY CLOSED] Reverse Proxy Link Deactivated")
    
    self.process.kill()

def start_server(conn_dict:dict[uuid.UUID, Connection], newGame: bool, gameState: tuple) -> tuple[KillableThread, Proxy | None, dict[uuid.UUID, Connection]]:
  server = socket.socket(socket.AF_INET, socket.SOCK_STREAM) # TCP style
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
      while reverseProxy.thread.is_alive():
        if reverseProxy.tunnelBuilt and reverseProxy.addr is not None:
          listening_str += f" & {reverseProxy.addr}:{reverseProxy.port} (public)"
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
    server.settimeout(.5) # time to wait in sec
    while not kill_event.is_set():
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

def start_client(ip: str, conn_dict: dict[str, Connection]) -> dict[str, Connection]:
  client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
  if ":" in ip:
    ip, port = ip.split(":")
    client.connect((ip, int(port)))
  else:
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

def propagate(dests: dict[uuid.UUID, Connection] | list[Player] | list[Connection],
              source: uuid.UUID | Player | Connection | None, command: Command):
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
    if not conn.outbox:
      continue
    while conn.inbox:
      # print([str(comm) for comm in conn.inbox])
      u = (conn.uuid, conn.fetch())
      updates.append(u)
  return updates

def del_ansi(line: bytes) -> bytes:
  ansi_pat = re.compile(rb"(\x9B|\x1B\[)[0-?]*[ -\/]*[@-~]")
  return ansi_pat.sub(b"", line)
