import pickle
import socket
import threading
import uuid
import traceback as tb
from time import sleep
from datetime import datetime

# COMM Protocol
PORT = 30545
HEADERSIZE = 8
FORMAT = "utf-8"
DISCONN = "!DISCONNECT!"

class Command:
  def __init__(self, action_obj_key:str, val) -> None:
    self.timestamp = datetime.now().time()
    action, obj, key = action_obj_key.split()
    # offer support for more granular control later, if deemed necessary
    if action in {"set", "test", "comms",
                  "add", "sub",}:
      self.action = action
    else:
      raise TypeError(f"Invalid Command action {action}")
    
    if obj in {"server", "client", "game", "test", "recv",
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
    command_text = "gameState" if "gameState" in self.key else ("handshake" if isinstance(self.val, tuple) else self.val)
    return f"{self.dump()} == {command_text} @ {self.timestamp}"
  
  def pack(self) -> bytes:
    return pickle.dumps(self, 5)
  
  def dump(self) -> str:
    return " ".join([self.action, self.obj, self.key])

class KillableThread(threading.Thread):
  def __init__(self, group: None = None, target = None, name: str | None = None, args: tuple | list = (), kwargs: tuple[str | None] | None = None, *, daemon: bool | None = None) -> None:
    self.kill_event = threading.Event()
    if not args:
      args = (self.kill_event,)
    else:
      args = (self.kill_event, *args)
    super().__init__(group, target, name, args, kwargs, daemon=daemon)
  
  def kill(self):
    self.kill_event.set()

class Connection:
  def __init__(self, addr: str, sock:socket.socket | None, my_uuid: uuid.UUID | None = None) -> None:
    self.uuid = uuid.uuid4() if my_uuid is None else my_uuid
    self.addr = addr
    self.inbox: list[Command] = []
    self.outbox: list[Command] = []
    self.sock: socket.socket | None = sock
  
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
      self._listen_thread = KillableThread(target=self._listen)
      self._listen_thread.start()
      self._send_thread = KillableThread(target=self._send)
      self._send_thread.start()
    else:
      self._listen_thread = None
      self._send_thread = None
  
  def _error_log(self, err) -> None:
    print(f"[CONNECTION ERROR] Error with {self}")
    print(f"[CONNECTION ERROR] {err}")
    self.kill()
  
  def _network_print(self, *var):
    from common import PRINT_NETWORKING_DEBUG
    if PRINT_NETWORKING_DEBUG:
      print(*var)
  
  def _listen(self, kill_event: threading.Event):
    try:
      while not kill_event.is_set():
        try:
          data_len = self.sock.recv(HEADERSIZE).decode(FORMAT)
        except ConnectionResetError as err:
          # catch when connection drops you
          if not kill_event.is_set():
            # catch when connection quits unexpectedly!
            self._error_log(err)
          break
        except ConnectionAbortedError as err:
          # catch when you quit
          if not kill_event.is_set():
            # catch when you quit unexpectedly!
            self._error_log(err)
          break
        
        if not data_len:
          continue
        
        data: bytes = self.sock.recv(int(data_len))
        try:
          comm: Command = pickle.loads(data)
          self._network_print("RECV", data_len, comm)
          if comm.val == DISCONN:
            return
          if comm.dump() == "comms recv error":
            self._recieved = not comm.val
          else:
            self.send(Command("comms recv error", False))
            self.inbox.append(comm)
          
        except pickle.UnpicklingError as err:
          self._error_log("Corrupted Command Recieved, Asking for Relay")
          self.send(Command("comms recv error", True))
      
    except Exception as err:
      self._error_log(err)
      tb.print_tb(err.__traceback__)
      self.kill_send_thread()
  
  def _send(self, kill_event: threading.Event):
    try:
      while not kill_event.is_set():
        if self.sock is None:
          self._error_log("Attempting to Send to Empty Socket")
        if not self.outbox:
          sleep(.1)
          continue
        
        comm = self.outbox.pop(0)
        data = comm.pack()
        data_len = f"{len(data)}".encode(FORMAT)
        data_len_padded = data_len + b' ' * (HEADERSIZE - len(data_len))
        
        # retry sending until command confirmed recieved
        while self._listen_thread and not kill_event.is_set():
          tries = 1.
          self._network_print(self)
          self._network_print("SEND", data_len_padded.decode(FORMAT), comm)
          self._recieved = None
          self.sock.sendall(data_len_padded)
          self.sock.sendall(data)
          
          # region await confirm command
          if comm.val == DISCONN or comm.dump() == "comms recv error":
            break
          while self._recieved is None and self._listen_thread and not kill_event.is_set():
            sleep(tries/10.)
            tries += 1.
          if self._recieved:
            break
          # endregion
        
        if comm.val == DISCONN:
          return
      
    except Exception as err:
      self._error_log(err)
      tb.print_tb(err.__traceback__)
      self.kill_listen_thread()
  
  def kill_listen_thread(self) -> None:
    if self._listen_thread is not None:
      self._listen_thread.kill()
      self._listen_thread = None
  
  def kill_send_thread(self) -> None:
    if self._send_thread is not None:
      self._send_thread.kill()
      self._send_thread = None
  
  def kill(self) -> None:
    if self.sock is not None:
      self.kill_listen_thread()
      self.kill_send_thread()
      self._sock.close()
      self.sock = None
      print(f"[CONNECTION CLOSED] Disconnected from {self}")
  
  def send(self, command: Command) -> None:
    self.outbox.append(command)
  
  def fetch(self) -> Command | None:
    if not self.inbox:
      return
    return self.inbox.pop(0)
