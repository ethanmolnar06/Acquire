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

def interface(mode, currentTextState):
  if mode == 'playerNames':
    currentTextState = crunch_playerNames(currentTextState)
  elif mode == 'playername':
    currentTextState = crunch_playername(currentTextState)
  elif mode == 'ip':
    currentTextState = crunch_ip(currentTextState)
  elif mode == 'customSettings':
    currentTextState = crunch_customSettings(currentTextState)
  return currentTextState

def crunch_playername(currentTextState):
  playernameTxtbx = currentTextState
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

def crunch_playerNames(currentTextState):
  playerNameTxtbxs, clicked_textbox_int = currentTextState
  keyNamesAsStr, modifierKeyBoolMap = fetch_keyboard()
  if 'tab' in keyNamesAsStr or 'return' in keyNamesAsStr:
    clicked_textbox_int = (clicked_textbox_int + 1) % len(playerNameTxtbxs)
  playerNameTxtbxs[clicked_textbox_int] = crunch_playername(playerNameTxtbxs[clicked_textbox_int])
  return playerNameTxtbxs, clicked_textbox_int

def crunch_ip(currentTextState):
  ipTxtbx = currentTextState
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

def crunch_customSettings(currentTextState: tuple):
  settings, clicked_textbox_key, drawnSettingsKeys = currentTextState
  
  if clicked_textbox_key == "Stock Pricing Function":
    choices = ["Classic", "Linear", "Logarithmic", "Exponential"]
    i = choices.index(settings["bank"][clicked_textbox_key])
    settings["bank"][clicked_textbox_key] = choices[(i + 1) % len(choices)]
    return settings, clicked_textbox_key
  
  i = drawnSettingsKeys.index(clicked_textbox_key)
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
    elif key == 'tab' or key == 'return':
      clicked_textbox_key = drawnSettingsKeys[(i+1)%len(drawnSettingsKeys)]
    # add numpers to type box
    elif modifierKeyBoolMap & pygame.KMOD_CTRL:
      key, settings[outerkey][clicked_textbox_key] = ctrl_handler(key, settings[outerkey][clicked_textbox_key])
      settings[outerkey][clicked_textbox_key] += key
    elif key in string.digits or key == ".":
      if not (key == "." and "." in settings[outerkey][clicked_textbox_key]):
        settings[outerkey][clicked_textbox_key] += key
  return settings, clicked_textbox_key
