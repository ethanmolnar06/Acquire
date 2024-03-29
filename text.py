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

def crunch_customSettings(currentTextState):
  settingsTxtbxs, clicked_textbox_int = currentTextState
  keyBoolMap = pygame.key.get_pressed()
  modifierKeyBoolMap = pygame.key.get_mods()
  for keyIndex in range(len(keyBoolMap)):
    if keyBoolMap[keyIndex]:
      keyNameAsStr = pygame.key.name(keyIndex)
      # handle specific key interactions
      if keyNameAsStr == 'backspace':
        settingsTxtbxs[clicked_textbox_int] = settingsTxtbxs[clicked_textbox_int][:-1]
      elif keyNameAsStr == 'delete':
        settingsTxtbxs[clicked_textbox_int] = ''
      elif keyNameAsStr == 'tab' or keyNameAsStr == 'return':
        clicked_textbox_int = (clicked_textbox_int + 1) % len(settingsTxtbxs)
      # add characters to type box
      elif len(keyNameAsStr) == 1 and ord(keyNameAsStr) < 128:
        # handle caps
        if modifierKeyBoolMap & pygame.KMOD_SHIFT:
          if keyNameAsStr in string.digits:
            keyNameAsStr = number_to_symbol[keyNameAsStr]
          else:
            keyNameAsStr = keyNameAsStr.upper()
        settingsTxtbxs[clicked_textbox_int] += keyNameAsStr
  return settingsTxtbxs, clicked_textbox_int