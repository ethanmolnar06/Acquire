import pygame
import plotly
from io import BytesIO

from objects import *
from common import HIDE_PERSONAL_INFO, Colors, Fonts
from pregame import screen

# plotly.io.kaleido.scope.mathjax = None

# region gui components

def clear_screen():
  screen.fill((255, 255, 255))

def resize_screen(event) -> pygame.Surface:
  return pygame.display.set_mode((event.w, event.h), pygame.RESIZABLE)

def top_center_title(surface: pygame.Surface, title: str, y_offset_div: int = 60) -> pygame.Rect:
  surface_width, surface_height = surface.get_size()
  
  # Title font + sizing
  font_size = min(surface_width, surface_height) // 20
  font = pygame.font.SysFont(Fonts.main, font_size)
  
  # Calculate the position of the title
  pos_x = surface_width // 2
  pos_y = surface_height // y_offset_div
  pos_x, pos_y = int(pos_x), int(pos_y)
  
  # Draw the title
  label = font.render(title, 1, Colors.BLACK)
  title_rect = label.get_rect()
  title_rect.center = (pos_x, pos_y)
  surface.blit(label, title_rect)
  
  return title_rect

def top_right_corner_x_button(surface: pygame.Surface) -> pygame.Rect:
  window_width, window_height = surface.get_size()
  
  # Button "X" font + sizing
  font_size = min(window_width, window_height) // 25
  font = pygame.font.Font(Fonts.oblivious, font_size)
  
  # Place and size the button
  back_button_rect = pygame.Rect(window_width - font_size, 0, font_size, font_size)
  pygame.draw.rect(surface, Colors.RED, back_button_rect)
  
  # Draw the "X" label
  label = font.render('x', 1, Colors.WHITE)
  label_rect = label.get_rect()
  label_rect.center = (back_button_rect.x + back_button_rect.width // 2 + 1, back_button_rect.y + back_button_rect.height // 2 - 2)
  surface.blit(label, label_rect)
  
  return back_button_rect

def draw_player_info(p: Player, x_offest_sub: int = 0) -> None:
  # Get the current window size and generate title font size
  window_width, window_height = screen.get_size()
  font_size = min(window_width, window_height) // 20
  font = pygame.font.SysFont(Fonts.main, font_size)
  
  # Get the current window size and generate font
  font_size = min(window_width, window_height) // 20
  font = pygame.font.SysFont(Fonts.main, font_size)
  
  # Calculate the position of the player information
  # Use the right edge of the screen as the x-coordinate
  offset_x = window_width - window_width // 100 - x_offest_sub
  offset_y = window_height // 9 - window_height // 10
  offset_x, offset_y = int(offset_x), int(offset_y)
  
  # Draw the player name
  label = font.render(p.name, 1, Colors.BLACK)
  label_rect = label.get_rect()
  label_rect.right = offset_x
  label_rect.top = offset_y
  screen.blit(label, label_rect)
  
  # Draw the player money
  label = font.render(f'${p.bal}', 1, Colors.BLACK)
  label_rect = label.get_rect()
  label_rect.right = offset_x
  label_rect.top = offset_y + font_size
  screen.blit(label, label_rect)
  
  # Draw the player stock holdings
  font_size_stock = int((min(window_width, window_height) / 19) * (7 / (len(p.stocks))))
  font_stock = pygame.font.SysFont(Fonts.main, font_size_stock)
  for i, stock in enumerate(p.stocks):
    label = font_stock.render(f'{stock}: {p.stocks[stock]}', 1, Colors.BLACK)
    label_rect = label.get_rect()
    label_rect.right = offset_x
    label_rect.top = offset_y + 2*font_size + i*font_size_stock
    screen.blit(label, label_rect)

# endregion

# region pregame gui

def draw_fullscreenSelect(drawinfo) -> list[pygame.Rect]:
  # Get the current window size and generate title font size
  window_width, window_height = screen.get_size()
  font_size = min(window_width, window_height) // 20
  font = pygame.font.SysFont(Fonts.main, font_size)
  
  # Calculate the size of each popup_select
  button_chunk_width = int(window_width // 3)
  button_chunk_height = int(window_height // 3)
  
  # Decide title text
  if drawinfo == 'hostJoin': title = 'Will you Host or Join a Game?'
  elif drawinfo == 'hostLocal': title = 'Will you Host Locally or on a Server?'
  elif drawinfo == 'loadSave': title = 'Would You Like to Load a Save?'
  elif drawinfo == 'setPlayerNamesLocal': title = 'Use Standard Settings?'
  elif drawinfo == 'askToBuy': title = 'Would You Like to Buy Stock?'
  elif drawinfo == 'endGameConfirm': title = 'Would You Like to End the Game?'
  elif drawinfo == 'makeSave': title = 'Would You Like to Save the Current Game?'
  elif drawinfo == 'endGameStats': title = 'Would You Like to Show End Game Stats?'
  else: title = 'Default Yes/No Question?'
  
  title_rect = top_center_title(screen, title, 15)
  
  # Decide choices text 
  if drawinfo == 'hostJoin': bianary_choices = ['Host', 'Join']
  elif drawinfo == 'hostLocal': bianary_choices = ['Local', 'Server']
  elif drawinfo == 'loadSave': bianary_choices = ['New Game', 'Load Save']
  else: bianary_choices = ['No', 'Yes']
  
  button_rects = []
  # Draw the button information
  for i, text in enumerate(bianary_choices):
    # Calculate the position of the buttons' top left corner
    pos_x = (window_width // 12)*(6*i+1)
    pos_y = window_height // 3
    pos_x, pos_y = int(pos_x), int(pos_y)
    
    # Create a rectangle for the popup_select and add to popup_select_rects
    button_rect = pygame.Rect(pos_x, pos_y, button_chunk_width, button_chunk_height)
    button_rects.append(button_rect)
    
    # Draw the popup_select
    pygame.draw.rect(screen, [Colors.RED, Colors.GREEN][i], button_rect)
    
    # Draw the stock name
    label = font.render(text, 1, Colors.WHITE)
    label_rect = label.get_rect()
    label_rect.center = (pos_x + button_chunk_width // 2, pos_y + button_chunk_height // 2)
    screen.blit(label, label_rect)
  return button_rects

def draw_selectSaveFile(drawinfo: tuple[bool, int, bool, int], saveinfo) -> tuple[pygame.Rect, list[pygame.Rect], pygame.Rect, pygame.Rect]:
  hover_directory, hover_save_int, clicked_directory, clicked_save_int = drawinfo
  saves_path, savefiles = saveinfo
  
  title_rect = top_center_title(screen, "Select Save File")
  
  # Get the current window size and Calc directory text
  window_width, window_height = screen.get_size()
  font_size = min(2*window_width // 3, 2*window_height // 3) // 30
  font = pygame.font.SysFont(Fonts.main, font_size)
  
  # Draw directory box and text
  longeststrlen = max([len(save) for save in savefiles] + [len(saves_path)])
  dd_width = int(font_size * longeststrlen * 10/16)
  dd_height = int(font_size * 4)
  directory_rect = pygame.Rect(window_width // 20, title_rect.bottom + dd_height// 3, dd_width, dd_height)
  pygame.draw.rect(screen, Colors.GRAY if not clicked_directory else Colors.RED, directory_rect, 0)
  pygame.draw.rect(screen, Colors.GREEN if hover_directory else Colors.BLACK, directory_rect, 12)
  msg = font.render(saves_path if not HIDE_PERSONAL_INFO else "Saves Directory", 1, Colors.BLACK)
  screen.blit(msg, msg.get_rect(center = directory_rect.center))
  
  savefile_rects = None
  if clicked_directory:
    savefile_rects = []
    for i, savefile in enumerate(savefiles):
      savefile_rect = directory_rect.copy()
      savefile_rect.y += (i+1) * savefile_rect.height
      pygame.draw.rect(screen, Colors.GRAY if i != clicked_save_int else Colors.LIGHTGREEN, savefile_rect, 0)
      savefile_rects.append(savefile_rect)
      if (not hover_directory and i == hover_save_int):
        pygame.draw.rect(screen, Colors.GREEN if (not hover_directory and i == hover_save_int) else Colors.BLACK, savefile_rect, 8)
      msg = font.render(savefile if not HIDE_PERSONAL_INFO else f"Save {i}", 1, Colors.BLACK)
      screen.blit(msg, msg.get_rect(center = savefile_rect.center))
  
  load_rect = None
  if clicked_save_int is not None:
    # Calc load font
    font_size = min(window_width, window_height) // 20
    font = pygame.font.SysFont(Fonts.main, font_size)
    
    # Draw directory box and text
    load_width = int(font_size * 4)
    load_height = int(font_size * 2)
    load_rect = pygame.Rect(window_width - (window_width//20 + load_width), window_height - (window_height//20 + load_height), load_width, load_height)
    pygame.draw.rect(screen, Colors.LIGHTGREEN , load_rect, 0)
    msg = font.render("LOAD", 1, Colors.BLACK)
    screen.blit(msg, msg.get_rect(center = load_rect.center))
  
  # Create an "x" button to back out of menu
  back_button_rect = top_right_corner_x_button(screen)
  
  return (directory_rect, savefile_rects, load_rect, back_button_rect)

# TODO flesh out over-Internet connections
def draw_joinCode(ipTxtBx: str) -> tuple[pygame.Rect, list[pygame.Rect]]:
  # Get the current window size and generate title font size
  window_width, window_height = screen.get_size()
  font_size = min(window_width, window_height) // 20
  font = pygame.font.SysFont(Fonts.main, font_size)
  
  title_rect = top_center_title(screen, "Enter Host IP")
  
  # Calculate text field sizing
  text_field_width = window_width//2.5
  text_field_height = window_height//6
  text_field_width, text_field_height = int(text_field_width), int(text_field_height)
  
  pos_x = window_width//2 - text_field_width//2
  pos_y = window_width//15 + text_field_height + window_width//30 
  pos_x, pos_y = int(pos_x), int(pos_y)
  
  text_field_rect = pygame.Rect(pos_x, pos_y, text_field_width, text_field_height)
  pygame.draw.rect(screen, Colors.GRAY, text_field_rect, 0)
  pygame.draw.rect(screen, Colors.GREEN, text_field_rect, 8)
  
  # Render and blit the player name text on the text field
  text_surface = font.render(ipTxtBx, True, Colors.BLACK)
  screen.blit(text_surface, (pos_x + 5, pos_y + 5))
  
  # Calculate the size of each button
  button_chunk_width = int(window_width // 3)
  button_chunk_height = int(window_height // 7)
  
  yesandno_rects = []
  # Draw the button information
  for i, text in enumerate(['Back', 'Connect']):
    # Calculate the position of the buttons' top left corner
    pos_x = (window_width // 12)*(6*i+1)
    pos_y = 5 * window_height // 6
    pos_x, pos_y = int(pos_x), int(pos_y)
    
    # Create a rectangle for the popup_select and add to popup_select_rects
    button_rect = pygame.Rect(pos_x, pos_y, button_chunk_width, button_chunk_height)
    yesandno_rects.append(button_rect)
    
    # Draw the popup_select
    pygame.draw.rect(screen, [Colors.RED, Colors.GREEN][i], button_rect)
    
    # Draw the stock name
    label = font.render(text, 1, Colors.WHITE)
    label_rect = label.get_rect()
    label_rect.center = (pos_x + button_chunk_width // 2, pos_y + button_chunk_height // 2)
    screen.blit(label, label_rect)
  
  return text_field_rect, yesandno_rects

def draw_setPlayerNameHost(playernameTxtbx) -> tuple[pygame.Rect, list[pygame.Rect]]:
  # Get the current window size and generate title font size
  window_width, window_height = screen.get_size()
  font_size = min(window_width, window_height) // 20
  font = pygame.font.SysFont(Fonts.main, font_size)
  
  title_rect = top_center_title(screen, "Enter Your Username")
  
  # Calculate text field sizing
  text_field_width = window_width//2.5
  text_field_height = window_height//6
  text_field_width, text_field_height = int(text_field_width), int(text_field_height)
  
  pos_x = window_width//2 - text_field_width//2
  pos_y = window_width//15 + text_field_height + window_width//30 
  pos_x, pos_y = int(pos_x), int(pos_y)
  
  text_field_rect = pygame.Rect(pos_x, pos_y, text_field_width, text_field_height)
  pygame.draw.rect(screen, Colors.GRAY, text_field_rect, 0)
  pygame.draw.rect(screen, Colors.GREEN, text_field_rect, 8)
  
  # Render and blit the player name text on the text field
  text_surface = font.render(playernameTxtbx, True, Colors.BLACK)
  screen.blit(text_surface, (pos_x + 5, pos_y + 5))
  
  # Calculate the size of each button
  button_chunk_width = int(window_width // 3)
  button_chunk_height = int(window_height // 7)
  
  yesandno_rects = []
  # Draw the button information
  for i, text in enumerate(['Back', 'Confirm']):
    # Calculate the position of the buttons' top left corner
    pos_x = (window_width // 12)*(6*i+1)
    pos_y = 5 * window_height // 6
    pos_x, pos_y = int(pos_x), int(pos_y)
    
    # Create a rectangle for the popup_select and add to popup_select_rects
    button_rect = pygame.Rect(pos_x, pos_y, button_chunk_width, button_chunk_height)
    yesandno_rects.append(button_rect)
    
    # Draw the popup_select
    pygame.draw.rect(screen, [Colors.RED, Colors.GREEN][i], button_rect)
    
    # Draw the stock name
    label = font.render(text, 1, Colors.WHITE)
    label_rect = label.get_rect()
    label_rect.center = (pos_x + button_chunk_width // 2, pos_y + button_chunk_height // 2)
    screen.blit(label, label_rect)
  
  return text_field_rect, yesandno_rects

def draw_setPlayerNameJoin(playernameTxtbx, clicked_textbox) -> tuple[pygame.Rect, pygame.Rect]:
  # Get the current window size and generate title font size
  window_width, window_height = screen.get_size()
  font_size = min(window_width, window_height) // 20
  font = pygame.font.SysFont(Fonts.main, font_size)
  
  title_rect = top_center_title(screen, "Enter Your Username")
  
  # Calculate text field sizing
  text_field_width = window_width//2.5
  text_field_height = window_height//6
  text_field_width, text_field_height = int(text_field_width), int(text_field_height)
  
  pos_x = window_width//2 - text_field_width//2
  pos_y = window_width//15 + text_field_height + window_width//30 
  pos_x, pos_y = int(pos_x), int(pos_y)
  
  text_field_rect = pygame.Rect(pos_x, pos_y, text_field_width, text_field_height)
  pygame.draw.rect(screen, Colors.GRAY, text_field_rect, 0)
  
  if clicked_textbox:
    pygame.draw.rect(screen, Colors.GREEN, text_field_rect, 4)
  
  # Render and blit the player name text on the text field
  text_surface = font.render(playernameTxtbx, True, Colors.BLACK)
  screen.blit(text_surface, (pos_x + 5, pos_y + 5))
  
  # Calculate the size of each button
  button_chunk_width = int(window_width // 3)
  button_chunk_height = int(window_height // 7)
  
  # Draw the confirmation button
  pos_x = (window_width // 2) - (button_chunk_width // 2)
  pos_y = 5 * window_height // 6
  pos_x, pos_y = int(pos_x), int(pos_y)
  
  # Create a rectangle for the popup_select and add to popup_select_rects
  confirm_rect = pygame.Rect(pos_x, pos_y, button_chunk_width, button_chunk_height)
  
  # Draw the popup_select
  pygame.draw.rect(screen, Colors.GREEN, confirm_rect)
  
  # Draw the stock name
  label = font.render("CONFRIM", 1, Colors.WHITE)
  label_rect = label.get_rect()
  label_rect.center = (pos_x + button_chunk_width // 2, pos_y + button_chunk_height // 2)
  screen.blit(label, label_rect)
  
  return text_field_rect, confirm_rect

def draw_setPlayerNamesLocal(player_names, clicked_textbox_int) -> tuple[list[pygame.Rect], list[pygame.Rect]]:
  # Get the current window size and generate title font size
  window_width, window_height = screen.get_size()
  font_size = min(window_width, window_height) // 20
  font = pygame.font.SysFont(Fonts.main, font_size)
  
  title_rect = top_center_title(screen, "Name The Players")
  
  # Calculate text field sizing
  text_field_width = window_width//2.5
  text_field_height = window_height//6
  text_field_width, text_field_height = int(text_field_width), int(text_field_height)
  
  text_field_rects = []
  numbcols = 2
  for i in range(len(player_names)):
    pos_x = window_width//2 + (((i%numbcols)-1) * text_field_width) + ((((i%numbcols)*numbcols)-1) * window_width//30)
    pos_y = window_width//15 + text_field_height*(i//numbcols) + (window_width//30 * (i//numbcols))
    pos_x, pos_y = int(pos_x), int(pos_y)
    
    text_field_rect = pygame.Rect(pos_x, pos_y, text_field_width, text_field_height)
    pygame.draw.rect(screen, Colors.GRAY, text_field_rect, 0)
    text_field_rects.append(text_field_rect)
    
    if clicked_textbox_int == i:
      pygame.draw.rect(screen, Colors.GREEN, text_field_rect, 4)
    
    # Render and blit the player name text on the text field
    text_surface = font.render(player_names[i], True, Colors.BLACK)
    screen.blit(text_surface, (pos_x + 5, pos_y + 5))
  
  # Calculate the size of each button
  button_chunk_width = int(window_width // 3)
  button_chunk_height = int(window_height // 7)
  
  yesandno_rects = []
  # Draw the button information
  for i, text in enumerate(['Custom Settings', 'Default Settings']):
    # Calculate the position of the buttons' top left corner
    pos_x = (window_width // 12)*(6*i+1)
    pos_y = 5 * window_height // 6
    pos_x, pos_y = int(pos_x), int(pos_y)
    
    # Create a rectangle for the popup_select and add to popup_select_rects
    button_rect = pygame.Rect(pos_x, pos_y, button_chunk_width, button_chunk_height)
    yesandno_rects.append(button_rect)
    
    # Draw the popup_select
    pygame.draw.rect(screen, [Colors.RED, Colors.GREEN][i], button_rect)
    
    # Draw the stock name
    label = font.render(text, 1, Colors.WHITE)
    label_rect = label.get_rect()
    label_rect.center = (pos_x + button_chunk_width // 2, pos_y + button_chunk_height // 2)
    screen.blit(label, label_rect)
  
  return text_field_rects, yesandno_rects

def draw_customSettings(drawnSettings: dict, clicked_textbox_key: str, longestKey: str) -> tuple[list[pygame.Rect], list[pygame.Rect], pygame.Rect]:
  
  title_rect = top_center_title(screen, "Set Custom Settings")
  
  numbcols = 2
  numbrows = 10
  # Calculate text field sizing
  window_width, window_height = screen.get_size()
  font_size = min(window_width, window_height) // 30
  font = pygame.font.SysFont(Fonts.main, font_size)
  key_text_width = int( (window_width - window_width//20) / (numbcols + 2) + longestKey)
  val_text_width = int(window_width//6)
  text_field_height = int(font_size + window_height//200)
  
  text_field_rects = []
  for i, kv in enumerate(drawnSettings.items()):
    k, v = kv
    
    # Draw Key Title
    pos_x = window_width//40 + (window_width//4 + key_text_width) * (i//numbrows)
    pos_y = window_height//12 + (window_width//45 + text_field_height) * (i%numbrows)
    pos_x, pos_y = int(pos_x), int(pos_y)
    key_surface = font.render(k, True, Colors.BLACK)
    screen.blit(key_surface, (pos_x, pos_y))
    
    # Draw Text Box and Value
    pos_x = pos_x + key_text_width + window_width//30
    pos_y = pos_y
    text_field_rect = pygame.Rect(pos_x, pos_y, val_text_width, text_field_height + window_width//250)
    pygame.draw.rect(screen, Colors.GRAY, text_field_rect, 0)
    text_field_rects.append(text_field_rect)
    
    if clicked_textbox_key == k:
      pygame.draw.rect(screen, Colors.GREEN, text_field_rect, 4)
    
    # Render and blit the text on the text field
    text_surface = font.render(str(v), True, Colors.BLACK)
    screen.blit(text_surface, (pos_x + window_width//150, pos_y))
  
  # Calculate the size of each button
  button_chunk_width = int(window_width // 3)
  button_chunk_height = int(window_height // 9)
  
  yesandno_rects = []
  # Draw the button information
  for i, text in enumerate(['Reset to Default', 'Start Game']):
    # Calculate the position of the buttons' top left corner
    pos_x = (window_width // 12)*(6*i+1)
    pos_y =  window_height * 6 // 7
    pos_x, pos_y = int(pos_x), int(pos_y)
    
    # Create a rectangle for the popup_select and add to popup_select_rects
    button_rect = pygame.Rect(pos_x, pos_y, button_chunk_width, button_chunk_height)
    yesandno_rects.append(button_rect)
    
    # Draw the popup_select
    pygame.draw.rect(screen, [Colors.RED, Colors.GREEN][i], button_rect)
    
    # Draw the option text
    label = font.render(text, 1, Colors.WHITE)
    label_rect = label.get_rect()
    label_rect.center = (pos_x + button_chunk_width // 2, pos_y + button_chunk_height // 2)
    screen.blit(label, label_rect)
  
  # Create an "x" button to back out of menu
  back_button_rect = top_right_corner_x_button(screen)
  
  return text_field_rects, yesandno_rects, back_button_rect

def draw_waitingForJoin(clientMode: str, connected_players: list[Player], clicked_textbox_int: int) -> tuple[list[pygame.Rect], list[pygame.Rect]]:
  # Get the current window size and generate title font size
  window_width, window_height = screen.get_size()
  font_size = min(window_width, window_height) // 20
  font = pygame.font.SysFont(Fonts.main, font_size)
  
  title_rect = top_center_title(screen, "Lobby: Waiting for Players")
  
  # Calculate text field sizing
  text_field_width = window_width//2.5
  text_field_height = window_height//6
  text_field_width, text_field_height = int(text_field_width), int(text_field_height)
  
  player_rects = []
  numbcols = 2
  for i, p in enumerate(connected_players):
    pos_x = window_width//2 + (((i%numbcols)-1) * text_field_width) + ((((i%numbcols)*numbcols)-1) * window_width//30)
    pos_y = window_width//15 + text_field_height*(i//numbcols) + (window_width//30 * (i//numbcols))
    pos_x, pos_y = int(pos_x), int(pos_y)
    
    player_rect = pygame.Rect(pos_x, pos_y, text_field_width, text_field_height)
    pygame.draw.rect(screen, Colors.GRAY, player_rect, 0)
    player_rects.append(player_rect)
    
    if clientMode == "hostServer" and clicked_textbox_int == i:
      pygame.draw.rect(screen, Colors.GREEN, player_rect, 4)
    
    # Render and blit the player name text on the text field
    text_surface = font.render(p.name, True, Colors.GREEN if p.ready else Colors.BLACK)
    screen.blit(text_surface, (pos_x + 5, pos_y + 5))
  
  # Calculate the size of each button
  button_chunk_width = int(window_width // 3)
  button_chunk_height = int(window_height // 7)
  
  yesandno_rects = []
  # Draw the button information
  yesandno_labels = ['Disconnect', 'Mark Ready']
  if clientMode == "hostServer":
    yesandno_labels = ['Kick Player', 'Start Game']
  
  for i, text in enumerate(yesandno_labels):
    # Calculate the position of the buttons' top left corner
    pos_x = (window_width // 12)*(6*i+1)
    pos_y = 5 * window_height // 6
    pos_x, pos_y = int(pos_x), int(pos_y)
    
    # Create a rectangle for the popup_select and add to popup_select_rects
    button_rect = pygame.Rect(pos_x, pos_y, button_chunk_width, button_chunk_height)
    yesandno_rects.append(button_rect)
    
    # Draw the popup_select
    pygame.draw.rect(screen, [Colors.RED, Colors.GREEN][i], button_rect)
    
    # Draw the stock name
    label = font.render(text, 1, Colors.WHITE)
    label_rect = label.get_rect()
    label_rect.center = (pos_x + button_chunk_width // 2, pos_y + button_chunk_height // 2)
    screen.blit(label, label_rect)
  
  return player_rects, yesandno_rects

def draw_selectPlayerFromSave(drawinfo, unclaimed_players: list[Player]) -> tuple[list[pygame.Rect], pygame.Rect, pygame.Rect]:
  hover_player_int, clicked_player_int = drawinfo
  
  title_rect = top_center_title(screen, "Select Player From Save File")
  
  # Calc text size
  window_width, window_height = screen.get_size()
  font_size = min(2*window_width // 3, 2*window_height // 3) // 30
  font = pygame.font.SysFont(Fonts.main, font_size)
  
  # Draw header box and text
  longeststrlen = max([len(p.name) for p in unclaimed_players] + [len("  Players  ")])
  dd_width = int(font_size * longeststrlen * 10/16)
  dd_height = int(font_size * 4)
  player_header_rect = pygame.Rect(window_width // 20, title_rect.bottom + dd_height// 3, dd_width, dd_height)
  pygame.draw.rect(screen, Colors.RED, player_header_rect, 0)
  pygame.draw.rect(screen, Colors.BLACK, player_header_rect, 9)
  msg = font.render("Players", 1, Colors.BLACK)
  screen.blit(msg, msg.get_rect(center = player_header_rect.center))
  
  player_rects: list[pygame.Rect] = []
  for i, p in enumerate(unclaimed_players):
    player_rect = player_header_rect.copy()
    player_rect.y += (i+1) * player_rect.height
    pygame.draw.rect(screen, Colors.GRAY if i != clicked_player_int else Colors.LIGHTGREEN, player_rect, 0)
    player_rects.append(player_rect)
    if i == hover_player_int:
      pygame.draw.rect(screen, Colors.GREEN if i == hover_player_int else Colors.BLACK, player_rect, 8)
    msg = font.render(p.name, 1, Colors.BLACK)
    screen.blit(msg, msg.get_rect(center = player_rect.center))
  
  load_rect = None
  if clicked_player_int is not None:
    draw_player_info(unclaimed_players[clicked_player_int], window_width//40)
    
    # Calc load font
    font_size = min(window_width, window_height) // 20
    font = pygame.font.SysFont(Fonts.main, font_size)
    
    # Draw directory box and text
    load_width = int(font_size * 4)
    load_height = int(font_size * 2)
    load_rect = pygame.Rect(window_width - (window_width//20 + load_width), window_height - (window_height//20 + load_height), load_width, load_height)
    pygame.draw.rect(screen, Colors.LIGHTGREEN , load_rect, 0)
    msg = font.render("SELECT", 1, Colors.BLACK)
    screen.blit(msg, msg.get_rect(center = load_rect.center))
  
  # Create an "x" button to back out of menu
  back_button_rect = top_right_corner_x_button(screen)
  
  return (player_rects, load_rect, back_button_rect)

# endregion

# region postgame gui

def draw_endGameStats(players, statlist, hover_stat_int, clicked_stat_int, viewmode, graphfig) -> tuple[list[pygame.Rect], pygame.Rect]:
  
  title_rect = top_center_title(screen, "End Game Stats")
  
  # Get the current window size and calculate text field sizing
  window_width, window_height = screen.get_size()
  font_size = min(2*window_width // 3, 2*window_height // 3) // 30
  
  graphClickables = [p.name for p in players] if viewmode == "USER" else statlist
  longeststrlen = max([len(text) for text in graphClickables])
  text_field_width = int(font_size * longeststrlen * 20/16)
  text_field_height = int(font_size * 30 / len(graphClickables))
  # text_field_width = window_width//5
  # text_field_height = window_height//20
  # text_field_width, text_field_height = int(text_field_width), int(text_field_height)
  
  statswap_rects = []
  numbcols = 1
  widthspacer = 50
  heightspacer = 90
  
  for i in range(len(graphClickables)):
    pos_x = window_width//3 + (((i%numbcols)-1) * text_field_width) + ((((i%numbcols)*numbcols)-1) * window_width//widthspacer)
    pos_y = window_height//18 + text_field_height*(i//numbcols) + (window_height//heightspacer * (i//numbcols))
    pos_x, pos_y = int(pos_x), int(pos_y)
    
    text_field_rect = pygame.Rect(pos_x, pos_y, text_field_width, text_field_height)
    pygame.draw.rect(screen, Colors.GRAY if clicked_stat_int != i else Colors.LIGHTGREEN, text_field_rect, 0)
    statswap_rects.append(text_field_rect)
    if i == hover_stat_int:
      pygame.draw.rect(screen, Colors.GREEN if i == hover_stat_int else Colors.BLACK, text_field_rect, 8)
    
    # Render and blit the player name text on the text field
    text_surface = font.render(graphClickables[i], True, Colors.BLACK)
    screen.blit(text_surface, text_surface.get_rect(center = text_field_rect.center))
  
  # Calc load font
  font_size = min(window_width, window_height) // 20
  font = pygame.font.SysFont(Fonts.main, font_size)
  
  #Create plotly stat Figures
  if clicked_stat_int is not None and graphfig is not None:
    figBytes = BytesIO(plotly.io.to_image(graphfig, format='png', scale=min(window_width, window_height) / 600))
    graph_png = pygame.image.load(figBytes)
    screen.blit(graph_png, graph_png.get_rect(center = (2*window_width//3, window_height//2)))
  
  # Draw viewmode box and text
  load_width = int(font_size * 4)
  load_height = int(font_size * 2)
  viewmode_rect = pygame.Rect(window_width - (window_width//20 + load_width), window_height - (window_height//20 + load_height), load_width, load_height)
  pygame.draw.rect(screen, Colors.LIGHTGREEN if viewmode == "STATS" else Colors.RED, viewmode_rect, 0)
  msg = font.render(viewmode, 1, Colors.BLACK)
  screen.blit(msg, msg.get_rect(center = viewmode_rect.center))
  
  return (statswap_rects, viewmode_rect)

# endregion
