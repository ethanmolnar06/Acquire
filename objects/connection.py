import pickle
import socket
import threading
import uuid
from datetime import datetime

# COMM Protocol
HEADERSIZE = 8
FORMAT = "utf-8"
DISCONN = "!DISCONNECT!"

class Command:
  def __init__(self, action_obj_key:str, val) -> None:
    action, obj, key = action_obj_key.split()
    # offer support for more granular control later, if deemed necessary
    if action in {"set", "test",
                  "add", "sub",}:
      self.action = action
    else:
      raise TypeError(f"Invalid Command action {action}")
    
    if obj in {"server", "client", "game", "test",
               "tilebag", "board", "player", "stats", "bank",}:
      self.obj = obj
    else:
      raise NameError(f"Invalid Command object {obj}")
    
    if type(key) == str:
      self.key = key
    else:
      raise KeyError(f"Invalid Command key {key}")
    
    self.val = val
  
  def __str__(self) -> str:
    command_text = "gameState" if "gameState" in self.key else self.val
    return f"{self.dump()} == {command_text}"
  
  def pack(self) -> bytes:
    return pickle.dumps(self, 5)
  
  def dump(self) -> str:
    return " ".join([self.action, self.obj, self.key])

class KillableThread(threading.Thread):
  def __init__(self, group: None = None, target = None, name: str | None = None, args: tuple | list = (), kwargs: tuple[str | None] | None = None, *, daemon: bool | None = None) -> None:
    self.kill_event = threading.Event()
    if args is None:
      args = (self.kill_event)
    else:
      args = (self.kill_event, *args)
    super().__init__(group, target, name, args, kwargs, daemon=daemon)
  
  def kill(self):
    self.kill_event.set()

class Connection:
  def __init__(self, addr: str, sock:socket.socket | None, my_uuid: uuid.UUID | None = None) -> None:
    self.uuid = uuid.uuid4() if my_uuid is None else my_uuid
    self.addr = addr
    self.sock: socket.socket | None = sock
    self.comm: list[Command] | None = None  
  
  def __str__(self) -> str:
    return f"{self.addr.capitalize()} [{self.uuid}] @ {datetime.now().time()}"
  
  @property
  def sock(self) -> socket.socket | None:
    return self._sock
  
  @sock.setter
  def sock(self, sock: socket.socket | None) -> None:
    # print("setting sockets!")
    self._sock = sock
    if sock is not None:
      self._thread = KillableThread(target=self.listen, args=(self._sock,))
      self._thread.start()
    else:
      self._thread = None
  
  def kill(self) -> None:
    if self.sock is not None:
      self.kill_thread()
      self._sock.close()
      self.sock = None
      print(f"[CONNECTION CLOSED] Disconnected from {self}")
  
  def kill_thread(self) -> None:
    if self._thread is not None:
      self._thread.kill()
      self._thread = None
  
  def _error_log(self, err) -> None:
    print(f"[CONNECTION ERROR] Error with {self}")
    print(f"[CONNECTION ERROR] {err}")
    self.kill()
  
  def listen(self, kill_event:threading.Event, sock:socket.socket):
    while not kill_event.isSet():
      try:
        data_len = sock.recv(HEADERSIZE).decode(FORMAT)
      except ConnectionResetError as err:
        # catch when connection drops you
        if not kill_event.isSet():
          # catch when connection quits unexpectedly!
          self._error_log(err)
        break
      except ConnectionAbortedError as err:
        # catch when you quit
        if not kill_event.isSet():
          # catch when you quit unexpectedly!
          self._error_log(err)
        break
      
      if data_len:
        data: bytes = sock.recv(int(data_len))
        comm: Command = pickle.loads(data)
        if self.comm is None:
          self.comm = [comm,]
        else:
          self.comm.append(comm)
        if comm.val == DISCONN:
          return
        # print(data_len, comm)
  
  def send(self, command: Command):
    data = command.pack()
    data_len = f"{len(data)}".encode(FORMAT)
    data_len_padded = data_len + b' ' * (HEADERSIZE - len(data_len))
    self.sock.send(data_len_padded)
    self.sock.send(data)
  
  def fetch(self) -> Command | None:
    command = None
    if self.comm is not None:
      command = self.comm.pop(0)
    if len(self.comm) == 0:
      self.comm = None
    return command
