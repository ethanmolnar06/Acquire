import string
import pygame

pygame.scrap.init()

number_to_symbol = {
  "1": "!",
  "2": "@",
  "3": "#",
  "4": "$",
  "5": "%",
  "6": "^",
  "7": "&",
  "8": "*",
  "9": "(",
  "0": ")",
}

def fetch_keyboard():
  keyBoolMap = pygame.key.get_pressed()
  modifierKeyBoolMap = pygame.key.get_mods()
  keyNamesAsStr = [pygame.key.name(i) for i in range(len(keyBoolMap)) if keyBoolMap[i]]
  return keyNamesAsStr, modifierKeyBoolMap

def ctrl_handler(key, txt:str):
  # does not add to txt for paste, is handled downstream
  if key == "c":
    pygame.scrap.put(pygame.SCRAP_TEXT, txt.encode())
    key = ""
  elif key == "x":
    pygame.scrap.put(pygame.SCRAP_TEXT, txt.encode())
    key = ""; txt = ""
  elif key == "v":
    key = pygame.scrap.get(pygame.SCRAP_TEXT).strip(b"\x00").decode()
  return key, txt

def nav_handler(fields, selected_field_int, num_col: int = None):
  keyNamesAsStr, _ = fetch_keyboard()
  if 'tab' in keyNamesAsStr or 'return' in keyNamesAsStr or 'left arrow' in keyNamesAsStr:
    selected_field_int = (selected_field_int + 1) % len(fields)
  elif 'right arrow' in keyNamesAsStr:
    selected_field_int = (selected_field_int - 1) % len(fields)
  elif num_col is not None:
    if 'up arrow' in keyNamesAsStr:
      selected_field_int = (selected_field_int - num_col) % len(fields)
    elif 'down arrow' in keyNamesAsStr:
      selected_field_int = (selected_field_int + num_col) % len(fields)
  return selected_field_int

def crunch_playername(playernameTxtbx):
  keyNamesAsStr, modifierKeyBoolMap = fetch_keyboard()
  for key in keyNamesAsStr:
    # handle specific key interactions
    if 'backspace' == key:
      playernameTxtbx = playernameTxtbx[:-1]
    elif 'delete' == key:
      playernameTxtbx = ''
    
    # add characters to type box
    elif len(key) == 1 and ord(key) < 128:
      if modifierKeyBoolMap & pygame.KMOD_CTRL:
        key, playernameTxtbx = ctrl_handler(key, playernameTxtbx)
      elif modifierKeyBoolMap & pygame.KMOD_SHIFT:
        if key in string.digits:
          key = number_to_symbol[key]
        else:
          key = key.upper()
      playernameTxtbx += key
  return playernameTxtbx

def crunch_ip(ipTxtbx):
  keyNamesAsStr, modifierKeyBoolMap = fetch_keyboard()
  for key in keyNamesAsStr:
    # handle specific key interactions
    if key == 'backspace':
      ipTxtbx = ipTxtbx[:-1]
    elif key == 'delete':
      ipTxtbx = ''
    
    if modifierKeyBoolMap & pygame.KMOD_CTRL:
      key, ipTxtbx = ctrl_handler(key, ipTxtbx)
      ipTxtbx += key
    # add characters to type box
    elif key in string.digits or key == ".":
      if len(ipTxtbx) <= 15:
        # max ip length 255.255.255.255
        ipTxtbx += key
      if len(ipTxtbx) > 15:
        ipTxtbx = ipTxtbx[:15]
  return ipTxtbx

def crunch_customSettings_nav(settings: dict[str], clicked_textbox_key: str, drawnSettingsKeys: list[str]):
  i = drawnSettingsKeys.index(clicked_textbox_key)
  i = nav_handler(drawnSettingsKeys, i, 2)
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
  
  keyNamesAsStr, modifierKeyBoolMap = fetch_keyboard()
  
  for key in keyNamesAsStr:
    # handle specific key interactions
    if key == 'backspace':
      settings[outerkey][clicked_textbox_key] = settings[outerkey][clicked_textbox_key][:-1]
    elif key == 'delete':
      settings[outerkey][clicked_textbox_key] = ''
    # add numpers to type box
    elif modifierKeyBoolMap & pygame.KMOD_CTRL:
      key, settings[outerkey][clicked_textbox_key] = ctrl_handler(key, settings[outerkey][clicked_textbox_key])
      settings[outerkey][clicked_textbox_key] += key
    elif key in string.digits or key == ".":
      if not (key == "." and "." in settings[outerkey][clicked_textbox_key]):
        settings[outerkey][clicked_textbox_key] += key
  return settings, clicked_textbox_key
