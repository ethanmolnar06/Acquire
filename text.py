import string
import pygame

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

def interface(mode, currentTextState):
  if mode == 'playerName':
    currentTextState = crunch_playernames(currentTextState)
  elif mode == 'customSettings':
    currentTextState = crunch_customSettings(currentTextState)
  return currentTextState

def crunch_playernames(currentTextState):
  playerNameTxtbxs, clicked_textbox_int = currentTextState
  keyBoolMap = pygame.key.get_pressed()
  modifierKeyBoolMap = pygame.key.get_mods()
  for keyIndex in range(len(keyBoolMap)):
    if keyBoolMap[keyIndex]:
      keyNameAsStr = pygame.key.name(keyIndex)
      # handle specific key interactions
      if keyNameAsStr == 'backspace':
        playerNameTxtbxs[clicked_textbox_int] = playerNameTxtbxs[clicked_textbox_int][:-1]
      elif keyNameAsStr == 'delete':
        playerNameTxtbxs[clicked_textbox_int] = ''
      elif keyNameAsStr == 'tab' or keyNameAsStr == 'return':
        clicked_textbox_int = (clicked_textbox_int + 1) % len(playerNameTxtbxs)
      # add characters to type box
      elif len(keyNameAsStr) == 1 and ord(keyNameAsStr) < 128:
        # handle caps
        if modifierKeyBoolMap & pygame.KMOD_SHIFT:
          if keyNameAsStr in string.digits:
            keyNameAsStr = number_to_symbol[keyNameAsStr]
          else:
            keyNameAsStr = keyNameAsStr.upper()
        playerNameTxtbxs[clicked_textbox_int] += keyNameAsStr
  return playerNameTxtbxs, clicked_textbox_int

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
  
  keyBoolMap = pygame.key.get_pressed()
  for keyIndex in range(len(keyBoolMap)):
    if keyBoolMap[keyIndex]:
      keyNameAsStr = pygame.key.name(keyIndex)
      # handle specific key interactions
      if keyNameAsStr == 'backspace':
        settings[outerkey][clicked_textbox_key] = settings[outerkey][clicked_textbox_key][:-1]
      elif keyNameAsStr == 'delete':
        settings[outerkey][clicked_textbox_key] = ''
      elif keyNameAsStr == 'tab' or keyNameAsStr == 'return':
        clicked_textbox_key = drawnSettingsKeys[(i+1)%len(drawnSettingsKeys)]
      # add numpers to type box
      elif keyNameAsStr in string.digits or keyNameAsStr == ".":
        if not (keyNameAsStr == "." and "." in settings[outerkey][clicked_textbox_key]):
          settings[outerkey][clicked_textbox_key] += keyNameAsStr
  return settings, clicked_textbox_key
