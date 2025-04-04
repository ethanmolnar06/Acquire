import pickle
import socket
import threading
import uuid
import traceback as tb
from time import sleep
from datetime import datetime
from typing import Literal

# COMM Protocol
PORT: int = 30545
HEADERSIZE: int = 8
FORMAT: str = "utf-8"
DISCONN: str = "!DISCONNECT!"
KILL: str = "!KILL!"
PING: str = "comms test ping"
DIAGNOSTIC: set[str] = {"comms recv error", "comms hist from"}

class Command:
  def __init__(self, action_obj_key: str, val, ordinal: int | None = None) -> None:
    self.ordinal: None | int = ordinal
    self.timestamp = datetime.now().time()
    action, obj, key = action_obj_key.split()
    # offer support for more granular control later, if deemed necessary
    if action in {"set", "test", "comms",
                  "add", "sub",}:
      self.action = action
    else:
      raise TypeError(f"Invalid Command action {action}")
    
    if obj in {"server", "client", "game", "test", "recv", "hist",
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
    self.inbox: list[Command | Literal["!DISCONNECT!"] | Literal["!KILL!"]] = []
    self.outbox: list[Command | Literal["!DISCONNECT!"] | Literal["!KILL!"]] = []
    self.historian: list[Command] = [Command("set hist start", 0, 0)]
    self._sock: socket.socket | None = None
    self.sock: socket.socket | None = sock
  
  def __str__(self) -> str:
    return f"{self.addr.capitalize()} [{self.uuid}] @ {datetime.now().time()}"
  
  @property
  def sock(self) -> socket.socket | None:
    return self._sock
  
  def _kill_thread(self, thread: KillableThread) -> None:
    if thread is not None:
      thread.kill()
      while thread.is_alive():
        pass
      thread = None
  
  @sock.setter
  def sock(self, sock: socket.socket | None) -> None:
    if sock is not None:
      self._sock = sock
      self._listen_thread = KillableThread(target=self._listen)
      self._listen_thread.start()
      self._send_thread = KillableThread(target=self._send)
      self._send_thread.start()
    else:
      if self._sock is not None:
        self._sock.close()
        self._kill_thread(self._send_thread)
        self._kill_thread(self._listen_thread)
      self._sock = sock
  
  def _error_log(self, err) -> None:
    print(f"[CONNECTION ERROR] Error with {self}")
    print(f"[CONNECTION ERROR] {err}")
  
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
          # catch when connection drops you unexpectedly
          raise err
        except ConnectionAbortedError as err:
          # catch when you quit unexpectedly
          raise err
        
        if not data_len:
          continue
        
        expected_ordinal = self.historian[-1].ordinal + 1
        data: bytes = self.sock.recv(int(data_len))
        try:
          comm: Command | Literal[b"!DISCONNECT!"] | Literal[b"!KILL!"] = pickle.loads(data)
          if not isinstance(comm, Command):
            comm = comm.decode(FORMAT)
          self._network_print("RECV", data_len, comm, str(self).split(" @" )[0])
          
        except pickle.UnpicklingError as err:
          self._error_log("Corrupted Command Recieved, Asking for Relay")
          self.send(Command("comms recv error", True))
        
        if isinstance(comm, Command):
          if comm.dump() in DIAGNOSTIC:
            if comm.dump() == "comms recv error":
              self.send(self.historian[-1])
            
            elif comm.dump() == "comms hist from":
              self.resend(comm.val)
          
          elif comm.ordinal == expected_ordinal:
            self.historian.append(comm)
            self.historian = self.historian[-10:]
            if comm.dump() != PING:
              self.inbox.append(comm)
          elif comm.ordinal > expected_ordinal:
            self._error_log(f"Command {comm.ordinal} Recieved Out of Order, expected {expected_ordinal}")
            self.send(Command("comms hist from", expected_ordinal))
          elif comm.ordinal < expected_ordinal:
            self._error_log(f"Command {comm.ordinal} Recieved Again Unecessarily")
        
        else:
          self._shutdownPrimed = True
          self.inbox.append(comm)
          # if not comm == KILL:
          #   self.send(Command("comms recv error", False))
        
        if comm in {DISCONN, KILL}:
          return
      
    except Exception as err:
      self._error_log(err)
      tb.print_tb(err.__traceback__)
  
  def _send(self, kill_event: threading.Event):
    tries = 1.
    try:
      while not kill_event.is_set():
        if self.sock is None:
          raise ConnectionError("Attempting to Send to Empty Socket")
        if not self.outbox:
          sleep(tries/10.)
          tries += 1.
          if tries > 30:
            tries = 1.
            self.outbox.append(Command(PING, False))
          continue
        
        tries = 1.
        comm = self.outbox.pop(0)
        if isinstance(comm, Command) and comm.ordinal is None and comm.dump() not in DIAGNOSTIC:
          comm.ordinal = self.historian[-1].ordinal + 1
          self.historian.append(comm)
        
        data = comm.pack() if isinstance(comm, Command) else pickle.dumps(comm.encode(FORMAT), 5)
        data_len = f"{len(data)}".encode(FORMAT)
        data_len_padded = data_len + b' ' * (HEADERSIZE - len(data_len))
        
        self._network_print("SEND", data_len_padded.decode(FORMAT), comm, str(self).split(" @" )[0])
        self.sock.sendall(data_len_padded)
        self.sock.sendall(data)
        
        if comm in {DISCONN, KILL}:
          return
      
    except Exception as err:
      self._error_log(err)
      tb.print_tb(err.__traceback__)
  
  def resend(self, ordinal: int) -> list[Command]:
    comms = [comm for comm in self.historian if comm.ordinal <= ordinal]
    for comm in comms:
      self.send(comm)
  
  def syncSendDISCONN(self, inResponse: bool = False) -> None:
    if inResponse:
      print(f"[PLAYER DROPPED] Disconnect Message Recieved from {self}")
    else:
      print(f"[PLAYER DROPPED] Disconnect Initiated with {self}")
    
    if self.sock is None:
      return
    
    waitTime: float = .1
    def err_timer(waitTime):
      sleep(waitTime)
      waitTime += .1
      if waitTime > 1.:
        raise ConnectionAbortedError("Assuming Error, Hard Closing")
      return waitTime
    
    self._shutdownPrimed = False
    try:
      # homemade socket.shutdown() protocol to guarentee proper threaded shutdown
      # wait for OUR inbox == THEIR outbox to clear
      self._network_print("[SOCKET SHUTDOWN STEP 1] Clearing Socket Inbox")
      while self.inbox:
        _ = self.fetch() # temp code until the fetch_updates codeloop becomes it's own thread
      self._network_print("[SOCKET SHUTDOWN STEP 2] Sending DISCONN")
      # add DISCONN to the end of OUR outbox
      self.send(DISCONN if not inResponse else KILL)
      # wait for OUR outbox == THEIR inbox to clear
      # until it is sent and confirmed recieved
      self._network_print("[SOCKET SHUTDOWN STEP 3] Awaiting DISCONN Confirm Reciept")
      while self.outbox or not (self._shutdownPrimed or inResponse):
        # print(self.outbox, self._recieved, inResponse)
        waitTime = err_timer(waitTime)
      # returns down OUR _send and THEIR _recieve
      # wait for reciprocal KILL in OUR inbox
      self._network_print("[SOCKET SHUTDOWN STEP 4] Awaiting KILL")
      while not (self.inbox or inResponse):
        # print(self.inbox, inResponse)
        waitTime = err_timer(waitTime)
      # recieved reciprocal KILL or came late to the party
      self._network_print("[SOCKET SHUTDOWN STEP 5] KILL Recieved, Socket Terminated")
    except ConnectionAbortedError as err:
      self._error_log(err)
    
    self.sock.shutdown(socket.SHUT_RDWR)
    self.sock = None
    print(f"[CONNECTION CLOSED] Disconnected from {self}")
  
  def send(self, command: Command | Literal["!DISCONNECT!"] | Literal["!KILL!"]) -> None:
    self.outbox.append(command)
  
  def fetch(self) -> Command | Literal["!DISCONNECT!"] | Literal["!KILL!"] | None:
    if not self.inbox:
      return
    return self.inbox.pop(0)
