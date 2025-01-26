import string
import pygame

def is_letter(key: int) -> bool:
  return pygame.key.name(key) in string.ascii_letters

def is_digit(key: int) -> bool:
  # .strip("[]") enables numbpad digits
  return pygame.key.name(key).strip("[]") in string.digits

def unpack_event(event: pygame.event.Event) -> tuple[str, int, int]:
  # event is pygame.KEYDOWN
  return event.dict["unicode"], event.dict["key"], event.dict["mod"]

def ctrl_handler(key: int, txtbx:str, allowed_char: str | None = None) -> str:
  if key == pygame.K_c:
    pygame.scrap.put(pygame.SCRAP_TEXT, txtbx.encode())
    return txtbx
  elif key == pygame.K_x:
    pygame.scrap.put(pygame.SCRAP_TEXT, txtbx.encode())
    return ""
  elif key == pygame.K_v:
    paste = pygame.scrap.get(pygame.SCRAP_TEXT).strip(b"\x00").decode()
    if allowed_char is not None:
      pastestr = []
      for char in paste:
        if char in allowed_char:
          pastestr.append(char)
      paste = ''.join(pastestr)
    return txtbx + paste
  return txtbx

def nav_handler(event: pygame.event.Event, fields: list | tuple, selected_field_int: int, num_col: int = None) -> int:
  txt, key, mods = unpack_event(event)
  if key in {pygame.K_TAB, pygame.K_RETURN, pygame.K_KP_ENTER, pygame.K_RIGHT}:
    return (selected_field_int + 1) % len(fields)
  elif key == pygame.K_LEFT:
    return (selected_field_int - 1) % len(fields)
  elif num_col is not None:
    if key == pygame.K_UP:
      return (selected_field_int - num_col) % len(fields)
    elif key == pygame.K_DOWN:
      return (selected_field_int + num_col) % len(fields)
  return selected_field_int

def crunch_playername(event: pygame.event.Event, playernameTxtbx: str) -> str:
  txt, key, mods = unpack_event(event)
  # handle specific key interactions
  if key == pygame.K_BACKSPACE:
    return playernameTxtbx[:-1]
  elif key == pygame.K_DELETE:
    return ''
  # general char add
  elif is_letter(key):
    # handle copy/cut/paste
    if mods & pygame.KMOD_CTRL:
      return ctrl_handler(key, playernameTxtbx, string.ascii_letters)
    else:
      # txt handles shift
      return playernameTxtbx + txt
  return playernameTxtbx

def crunch_ip(event: pygame.event.Event, ipTxtbx: str) -> str:
  # max ip length 255.255.255.255 == 15
  maxlen = 15
  _, key, mods = unpack_event(event)
  # handle specific key interactions
  if key == pygame.K_BACKSPACE:
    return ipTxtbx[:-1]
  elif key == pygame.K_DELETE:
    return ''
  # handle copy/cut/paste
  elif is_letter(key):
    if mods & pygame.KMOD_CTRL:
      return ctrl_handler(key, ipTxtbx, string.digits + ".")[:maxlen]
  # general char add
  elif is_digit(key) or (key == pygame.K_PERIOD and ipTxtbx.count(".") < 3):
    if len(ipTxtbx) < maxlen:
      # .strip("[]") enables numbpad digits
      return ipTxtbx + pygame.key.name(key).strip("[]")
  return ipTxtbx[:maxlen]

def crunch_customSettings_nav(event: pygame.event.Event, settings: dict[str], clicked_textbox_key: str, drawnSettingsKeys: list[str]) -> tuple[dict[str], str]:
  i = drawnSettingsKeys.index(clicked_textbox_key)
  i = nav_handler(event, drawnSettingsKeys, i, 2)
  clicked_textbox_key = drawnSettingsKeys[(i)%len(drawnSettingsKeys)]
  
  if clicked_textbox_key == "Stock Pricing Function":
    choices = ["Classic", "Linear", "Logarithmic", "Exponential"]
    i = choices.index(settings["bank"][clicked_textbox_key])
    settings["bank"][clicked_textbox_key] = choices[(i + 1) % len(choices)]
    return settings, clicked_textbox_key
  
  if i < len(settings["board"].keys()):
    outerkey = "board"
  elif i < len(settings["board"].keys()) + len(settings["player"].keys()):
    outerkey = "player"
  elif i < len(settings["board"].keys()) + len(settings["player"].keys()) + len(settings["bank"].keys()):
    outerkey = "bank"
  else:
    outerkey = "bank" + settings["bank"]["Stock Pricing Function"]
  
  _, key, mods = unpack_event(event)
  # handle specific key interactions
  if key == pygame.K_BACKSPACE:
    settings[outerkey][clicked_textbox_key] = settings[outerkey][clicked_textbox_key][:-1]
  elif key == pygame.K_DELETE:
    settings[outerkey][clicked_textbox_key] = ''
  # handle copy/cut/paste
  elif is_letter(key):
    if mods & pygame.KMOD_CTRL:
      settings[outerkey][clicked_textbox_key] = ctrl_handler(key, settings[outerkey][clicked_textbox_key], string.digits + ".")
  # general char add
  elif is_digit(key) or key == pygame.K_PERIOD:
    if not (key == pygame.K_PERIOD and "." in settings[outerkey][clicked_textbox_key]):
      settings[outerkey][clicked_textbox_key] += pygame.key.name(key).strip("[]")
  return settings, clicked_textbox_key

def crunch_url(event: pygame.event.Event, url_textbox: str):
  txt, key, mods = unpack_event(event)
  # region handle specific key interactions
  if key == pygame.K_BACKSPACE:
    return url_textbox[:-1]
  elif key == pygame.K_DELETE:
    return ''
  # endregion
  
  # general char add
  elif is_letter(key) or is_digit(key) or key in {pygame.K_PERIOD, pygame.K_COLON}:
    # handle copy/cut/paste
    if mods & pygame.KMOD_CTRL:
      allowed_chars = string.ascii_letters + string.digits + ".:"
      return ctrl_handler(key, url_textbox, allowed_chars)
    else:
      # txt handles shift
      return url_textbox + txt
  return url_textbox
