import socket
import threading
import uuid

from objects.connection import Command, KillableThread, Connection, DISCONN
from objects.player import Player

# NET Protocol
PORT = 50545

def start_server(conn_dict:dict[uuid.UUID, Connection], newGame: bool, gameState: tuple) -> tuple[KillableThread, dict[uuid.UUID, Connection]]:
  # TCP style
  ip = socket.gethostbyname(socket.gethostname())
  # what ip to use for non-LAN connections?
  # any way to avoid requiring port forwarding?
  # ip = ""
  server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
  server.settimeout(3.0) # time to wait in sec
  server.bind((ip, PORT))
  print(f"[SERVER INITALIZED]")
  
  from common import pack_gameState
  def accept_conn(kill_event:threading.Event, newGame: bool, gameState: tuple):
    server.listen()
    print(f"[LISTENING] Listening at {ip}")
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
    
    print(f"[LISTENING CLOSED] No Longer Listening at {ip}")
    server.close()
    print(f"[SERVER TERMINATED]")
  
  serverThread = KillableThread(target=accept_conn, args=(newGame, gameState))
  serverThread.start()
  
  return serverThread, conn_dict

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
    raise TypeError("Invalid propogation destination")

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
