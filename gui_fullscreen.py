import pygame
from pygame import Surface, Rect
import plotly
# plotly.io.kaleido.scope.mathjax = None
import numpy as np
from io import BytesIO
from typing import Callable

from objects import *
from common import HIDE_PERSONAL_INFO, Colors, Fonts, ratio
from pregame import screen

# region gui components

def clear_screen():
  screen.fill((255, 255, 255))

def resize_screen(event) -> Surface:
  return pygame.display.set_mode((event.w, event.h), pygame.RESIZABLE)

# TODO maybe remake these?
# def horizontal_refontsizer(rect_width: int, default_font_size: int, 
#                            labels: list[str], font_name: str = Fonts.main, spacer_allocated: int = 250):
#   # resize all font across grid to fit largest entry
#   longestheader = max([len(h) for h in labels])
#   if longestheader * default_font_size * len(labels) + spacer_allocated > rect_width:
#     font_size = int(1.7 * (rect_width - spacer_allocated) / (longestheader * len(labels)))
#   header_font = pygame.font.SysFont(font_name, font_size)
#   return header_font, font_size
 
# def vertical_refontsizer(rect_height: int, default_font_size: int, pos_y: int, 
#                          labels: list[str], font_name: str = Fonts.main, spacer_allocated: int = 250):
#   col_stand_height = pos_y + (2 + len(labels)) * default_font_size * 11/10
#   if col_stand_height >= rect_height:
#     font_size = int(default_font_size * (1 - (col_stand_height - rect_height)/rect_height) )
#   info_font = pygame.font.SysFont(font_name, font_size)
#   return info_font, font_size

def dynamic_font(surface: Surface, rect: Rect, label: str, label_color: tuple[int, int, int], font_name: str, 
                 default_font_size: int | None = None) -> int:
  if default_font_size is None:
    default_font_size = min(rect.w, rect.h) // 2
  font = pygame.font.SysFont(font_name, default_font_size)
  label_surface = font.render(label, 1, label_color)
  
  font_size = default_font_size
  while label_surface.get_width() > .95 * rect.w:
    font_size = ratio(label_surface.get_width(), rect.w, font_size)
    font = pygame.font.SysFont(font_name, font_size)
    label_surface = font.render(label, 1, label_color)
  
  label_rect = label_surface.get_rect()
  label_rect.center = rect.center
  surface.blit(label_surface, label_rect)
  return font_size

def create_square_dims(list: list) -> tuple[int, int]:
  # Calculate grid arangement (aim for square)
  cols = int(np.round(np.sqrt(len(list)), 0))
  rows = len(list)//cols + (1 if len(list)%cols != 0 else 0)
  return cols, rows

def gridifier(surface: Surface, width: int, height: int, top_left: tuple[int, int], labels: list[str], cols: int, rows: int,
              rect_color_func: Callable[[int], tuple[int, int, int]], label_color_func: Callable[[int], tuple[int, int, int]],
              outline_color_func: Callable[[int], tuple[int, int, int] | None] | None = None, font_name: str = Fonts.main, 
              extra_render_func: Callable[[Surface], None] | None = None) -> list[Rect]:
  
  # Calculate rect sizing and arangement spacing
  rect_width  = int(width       // (cols + .5))
  rect_height = int(height      // (rows + .5))
  w_gap       = int(rect_width  // (cols * 3))
  h_gap       = int(rect_height // (rows * 3))
  
  # Calculate the grid starting offset from (0, 0) of the surface
  offset_x = top_left[0] + w_gap
  offset_y = top_left[1] + h_gap
  offset_x, offset_y = int(offset_x), int(offset_y)
  
  # Create grid of rects
  rects = []
  for j in range(rows):
    for i in range(cols):
      if i + cols*j >= len(labels):
        break
      # Calculate the position of the rect
      pos = (offset_x + i * rect_width + i * w_gap, offset_y + j * rect_height + j * h_gap)
      
      # Create the rect, add to rects, and draw to screen
      rect = Rect(pos[0], pos[1], rect_width, rect_height)
      rects.append(rect)
      pygame.draw.rect(surface, rect_color_func(i + cols*j), rect)
      
      # Draw outline around rect if necessary
      if outline_color_func is not None:
        outline_color = outline_color_func(i + cols*j)
        if outline_color is not None:
          pygame.draw.rect(surface, outline_color_func(i + cols*j), rect, 8)
      
      # Do extra stuff per rect if necessary
      if extra_render_func is not None:
        extra_render_func(screen)
      
      # Create the label and draw to surface
      dynamic_font(screen, rect, labels[i + cols*j], label_color_func(i + cols*j), font_name)
  
  return rects

def dropdown(surface: Surface, width: int, height: int, top_left: tuple[int, int], header: str, choices: list[str] | None, 
             header_rect_color: tuple[int, int, int], header_label_color: tuple[int, int, int],
             choice_rect_color_func: Callable[[int], tuple[int, int, int]], choice_label_color_func: Callable[[int], tuple[int, int, int]],
             header_outline_color: tuple[int, int, int] | None = None, 
             choice_outline_color_func: Callable[[int], tuple[int, int, int] | None] | None = None, header_outline_thick: int = 8, 
             choice_outline_thick: int = 8, font_name: str = Fonts.main, 
             header_extra_render_func: Callable[[Surface], None] | None = None,
             choice_extra_render_func: Callable[[Surface], None] | None = None) -> list[Rect]:
  
  # Calculate dropdown arangement
  if choices is None:
    rows = 10
  else:
    rows = max(len(choices), 10)
  
  # Calculate rect sizing and arangement spacing
  rect_width  = int(width  // (1.1))
  rect_height = int(height // (rows + 1))
  w_gap       = 0
  h_gap       = 0
  
  # Calculate the grid starting offset from (0, 0) of the surface
  offset_x = top_left[0] + w_gap
  offset_y = top_left[1] + h_gap
  offset_x, offset_y = int(offset_x), int(offset_y)
  
  # Create the header rect and draw to screen
  header_rect = Rect(offset_x, offset_y, rect_width, rect_height)
  pygame.draw.rect(surface, header_rect_color, header_rect, 0)
  
  # Draw outline around header rect if necessary
  if header_outline_color is not None:
    pygame.draw.rect(surface, header_outline_color, header_rect, header_outline_thick)
  
  # Do extra stuff to header rect if necessary
  if header_extra_render_func is not None:
    header_extra_render_func(screen)
  
  # Create the label and blit to surface
  dynamic_font(surface, header_rect, header, header_label_color, font_name)
  
  # Draw 
  choice_rects = None
  if choices is not None:
    choice_rects = []
    for i, choice in enumerate(choices):
      # Calculate the position of the choice
      choice_rect = header_rect.copy()
      choice_rect.y += (i+1) * choice_rect.height
      choice_rects.append(choice_rect)
      
      pygame.draw.rect(surface, choice_rect_color_func(i), choice_rect, 0)
      
      # Draw outline around rect if necessary
      if choice_outline_color_func is not None:
        choice_outline_color = choice_outline_color_func(i)
        if choice_outline_color is not None:
          pygame.draw.rect(surface, choice_outline_color, choice_rect, choice_outline_thick)
      
      # Do extra stuff per rect if necessary
      if choice_extra_render_func is not None:
        choice_extra_render_func(screen)
      
      # Create the label and blit to surface
      dynamic_font(surface, choice_rect, choice, choice_label_color_func(i), font_name)
  
  return header_rect, choice_rects

# endregion

# region gui prebuilts

def top_center_title(surface: Surface, title: str, y_offset_div: int = 60) -> Rect:
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

def top_right_corner_x_button(surface: Surface) -> Rect:
  window_width, window_height = surface.get_size()
  
  # Button "X" font + sizing
  font_size = min(window_width, window_height) // 25
  font = pygame.font.Font(Fonts.oblivious, font_size)
  
  # Place and size the button
  back_button_rect = Rect(window_width - font_size, 0, font_size, font_size)
  pygame.draw.rect(surface, Colors.RED, back_button_rect)
  
  # Draw the "X" label
  label = font.render('x', 1, Colors.WHITE)
  label_rect = label.get_rect()
  label_rect.center = (back_button_rect.x + back_button_rect.width // 2 + 1, back_button_rect.y + back_button_rect.height // 2 - 2)
  surface.blit(label, label_rect)
  
  return back_button_rect

# TODO make it draw arbitrary number of buttons
def center_center_dual_buttons(surface: Surface, button_labels: list[str], font_name: str = Fonts.main) -> list[Rect]:
  surface_width, surface_height = surface.get_size()
  font_size = min(surface_width, surface_height) // 20
  font = pygame.font.SysFont(font_name, font_size)
  
  # Calculate the size of each button
  button_chunk_width = int(surface_width // 3)
  button_chunk_height = int(surface_height // 3)
  
  button_rects = []
  for i, label in enumerate(button_labels):
    # Calculate the position of the button's top left corner
    pos_x = (surface_width // 12)*(6*i+1)
    pos_y = surface_height // 3
    pos_x, pos_y = int(pos_x), int(pos_y)
    
    # Create the button and draw it
    button_rect = pygame.Rect(pos_x, pos_y, button_chunk_width, button_chunk_height)
    button_rects.append(button_rect)
    pygame.draw.rect(screen, [Colors.RED, Colors.GREEN][i], button_rect)
    surface
    
    # Draw the label to the button
    label_surface = font.render(label, 1, Colors.WHITE)
    label_rect = label_surface.get_rect()
    label_rect.center = button_rect.center
    screen.blit(label_surface, label_rect)
  return button_rects

# TODO make it draw arbitrary number of buttons
def bottom_center_dual_buttons(surface: Surface, button_labels: list[str], font_name: str = Fonts.main) -> list[Rect]:
  window_width, window_height = surface.get_size()
  font_size = min(window_width, window_height) // 20
  font = pygame.font.SysFont(font_name, font_size)
  
  # Calculate the size of each button
  button_chunk_width = int(window_width // 3)
  button_chunk_height = int(window_height // 7)
  
  yesandno_rects = []
  # Draw the button information
  for i, text in enumerate(button_labels):
    # Calculate the position of the buttons' top left corner
    pos_x = (window_width // 12)*(6*i+1)
    pos_y = 5 * window_height // 6
    pos_x, pos_y = int(pos_x), int(pos_y)
    
    # Create a rectangle for the popup_select and add to popup_select_rects
    button_rect = Rect(pos_x, pos_y, button_chunk_width, button_chunk_height)
    yesandno_rects.append(button_rect)
    
    # Draw the popup_select
    pygame.draw.rect(surface, [Colors.RED, Colors.GREEN][i], button_rect)
    
    # Draw the stock name
    label = font.render(text, 1, Colors.WHITE)
    label_rect = label.get_rect()
    label_rect.center = (pos_x + button_chunk_width // 2, pos_y + button_chunk_height // 2)
    surface.blit(label, label_rect)
  return yesandno_rects

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

def draw_fullscreenSelect(drawinfo) -> list[Rect]:
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
  
  yesandno_rects = center_center_dual_buttons(screen, bianary_choices, Fonts.main)
  
  return yesandno_rects

def draw_selectSaveFile(drawinfo: tuple[bool, int, bool, int], saveinfo) -> tuple[Rect, list[Rect], Rect, Rect]:
  hover_directory, hover_save_int, clicked_directory, clicked_save_int = drawinfo
  saves_path, savefiles = saveinfo
  
  title_rect = top_center_title(screen, "Select Save File")
  
  window_width, window_height = screen.get_size()
  width = window_width * (3/7)
  height = window_height - window_height // 24
  top_left = (window_width//120, window_height // 24)
  
  header = saves_path if not HIDE_PERSONAL_INFO else "Saves Directory"
  header_rect_color = Colors.RED if clicked_directory else Colors.GRAY
  header_outline_color =  Colors.GREEN if hover_directory else Colors.BLACK
  
  choices = savefiles if not HIDE_PERSONAL_INFO else [f"Save {i+1}" for i in range(len(savefiles))]
  
  def choice_rect_color_func(i: int) -> tuple[int, int, int]:
    return Colors.LIGHTGREEN if i == clicked_save_int and clicked_directory else Colors.GRAY
  
  def choice_outline_color_func(i: int) -> tuple[int, int, int]:
    return Colors.GREEN if i == hover_save_int and not hover_directory else None
  
  header_rect, choice_rects = dropdown(screen, width, height, top_left, header, choices if clicked_directory else None,
                                       header_rect_color, Colors.BLACK, 
                                       choice_rect_color_func, lambda x: Colors.BLACK, 
                                       header_outline_color, choice_outline_color_func)
  
  load_rect = None
  if clicked_save_int is not None:
    # Calc load font
    font_size = min(window_width, window_height) // 20
    font = pygame.font.SysFont(Fonts.main, font_size)
    
    # Draw directory box and text
    load_width = int(font_size * 4)
    load_height = int(font_size * 2)
    load_rect = Rect(window_width - (window_width//20 + load_width), window_height - (window_height//20 + load_height), load_width, load_height)
    pygame.draw.rect(screen, Colors.LIGHTGREEN , load_rect, 0)
    msg = font.render("LOAD", 1, Colors.BLACK)
    screen.blit(msg, msg.get_rect(center = load_rect.center))
  
  # Create an "x" button to back out of menu
  back_button_rect = top_right_corner_x_button(screen)
  
  return header_rect, choice_rects, load_rect, back_button_rect

# TODO flesh out over-Internet connections
def draw_joinCode(ipTxtBx: str) -> tuple[Rect, list[Rect]]:
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
  
  text_field_rect = Rect(pos_x, pos_y, text_field_width, text_field_height)
  pygame.draw.rect(screen, Colors.GRAY, text_field_rect, 0)
  pygame.draw.rect(screen, Colors.GREEN, text_field_rect, 8)
  
  # Render and blit the player name text on the text field
  text_surface = font.render(ipTxtBx, True, Colors.BLACK)
  screen.blit(text_surface, (pos_x + 5, pos_y + 5))
  
  yesandno_rects = bottom_center_dual_buttons(screen, ['Back', 'Connect'], Fonts.main)
  
  return text_field_rect, yesandno_rects

def draw_setPlayerNameHost(playernameTxtbx: str) -> tuple[Rect, list[Rect]]:
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
  
  text_field_rect = Rect(pos_x, pos_y, text_field_width, text_field_height)
  pygame.draw.rect(screen, Colors.GRAY, text_field_rect, 0)
  pygame.draw.rect(screen, Colors.GREEN, text_field_rect, 8)
  
  # Render and blit the player name text on the text field
  text_surface = font.render(playernameTxtbx, True, Colors.BLACK)
  screen.blit(text_surface, (pos_x + 5, pos_y + 5))
  
  yesandno_rects = bottom_center_dual_buttons(screen, ['Back', 'Connect'], Fonts.main)
  
  return text_field_rect, yesandno_rects

def draw_setPlayerNameJoin(playernameTxtbx: str) -> tuple[Rect]:
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
  
  text_field_rect = Rect(pos_x, pos_y, text_field_width, text_field_height)
  pygame.draw.rect(screen, Colors.GRAY, text_field_rect, 0)
  pygame.draw.rect(screen, Colors.GREEN, text_field_rect, 8)
  
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
  confirm_rect = Rect(pos_x, pos_y, button_chunk_width, button_chunk_height)
  
  # Draw the popup_select
  pygame.draw.rect(screen, Colors.GREEN, confirm_rect)
  
  # Draw the stock name
  label = font.render("CONFRIM", 1, Colors.WHITE)
  label_rect = label.get_rect()
  label_rect.center = (pos_x + button_chunk_width // 2, pos_y + button_chunk_height // 2)
  screen.blit(label, label_rect)
  
  return confirm_rect

def draw_setPlayerNamesLocal(player_names, clicked_textbox_int) -> tuple[list[Rect], list[Rect]]:
  window_width, window_height = screen.get_size()
  
  title_rect = top_center_title(screen, "Name The Players")
  
  grid_width = int(window_width)
  grid_height = int(window_height * (4/5))
  top_left = (0, window_width // 40)
  
  def outline_color_func(i: int) -> tuple[int, int, int]:
    return Colors.GREEN if i == clicked_textbox_int else None
  
  cols, rows = create_square_dims(player_names)
  
  player_rects = gridifier(screen, grid_width, grid_height, top_left, player_names, cols, rows, 
                           lambda x: Colors.GRAY, lambda x: Colors.BLACK, outline_color_func)
  
  button_labels = ['Custom Settings', 'Default Settings']
  yesandno_rects = bottom_center_dual_buttons(screen, button_labels)
  
  # Create an "x" button to back out of menu
  back_button_rect = top_right_corner_x_button(screen)
  
  return player_rects, yesandno_rects, back_button_rect

def draw_customSettings(drawnSettings: dict, clicked_textbox_key: str, longestKey: str) -> tuple[list[Rect], list[Rect], Rect]:
  
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
    text_field_rect = Rect(pos_x, pos_y, val_text_width, text_field_height + window_width//250)
    pygame.draw.rect(screen, Colors.GRAY, text_field_rect, 0)
    text_field_rects.append(text_field_rect)
    
    if clicked_textbox_key == k:
      pygame.draw.rect(screen, Colors.GREEN, text_field_rect, 4)
    
    # Render and blit the text on the text field
    text_surface = font.render(str(v), True, Colors.BLACK)
    screen.blit(text_surface, (pos_x + window_width//150, pos_y))
  
  yesandno_rects = bottom_center_dual_buttons(screen, ['Reset to Default', 'Start Game'], Fonts.main)
  
  # Create an "x" button to back out of menu
  back_button_rect = top_right_corner_x_button(screen)
  
  return text_field_rects, yesandno_rects, back_button_rect

def draw_waitingForJoin(clientMode: str, connected_players: list[Player], clicked_textbox_int: int) -> tuple[list[Rect], list[Rect]]:
  # Get the current window size and generate title font size
  window_width, window_height = screen.get_size()
  font_size = min(window_width, window_height) // 20
  font = pygame.font.SysFont(Fonts.main, font_size)
  
  title_rect = top_center_title(screen, "Lobby: Waiting for Players")
  
  grid_width = int(window_width)
  grid_height = int(window_height * (4/5))
  top_left = (0, window_width // 40)
  
  player_names = [p.name for p in connected_players]
  cols, rows = create_square_dims(player_names)
  
  def outline_color_func(i: int) -> tuple[int, int, int]:
    if clientMode == "hostServer":
      return Colors.GREEN if i == clicked_textbox_int else Colors.BLACK
    return Colors.BLACK
  
  ready = [p.ready for p in connected_players]
  def label_color_func(i: int) -> tuple[int, int, int]:
    return Colors.GREEN if ready[i] else Colors.BLACK
  
  player_rects = gridifier(screen, grid_width, grid_height, top_left, player_names, cols, rows,
                           lambda x: Colors.GRAY, label_color_func, outline_color_func)
  
  # Calculate text field sizing
  text_field_width = window_width//2.5
  text_field_height = window_height//6
  text_field_width, text_field_height = int(text_field_width), int(text_field_height)
  
  yesandno_labels = ['Disconnect', 'Mark Ready']
  if clientMode == "hostServer":
    yesandno_labels = ['Kick Player', 'Start Game']
  
  yesandno_rects = bottom_center_dual_buttons(screen, yesandno_labels)
  
  return player_rects, yesandno_rects

def draw_selectPlayerFromSave(drawinfo, unclaimed_players: list[Player]) -> tuple[list[Rect], Rect, Rect]:
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
  player_header_rect = Rect(window_width // 20, title_rect.bottom + dd_height// 3, dd_width, dd_height)
  pygame.draw.rect(screen, Colors.RED, player_header_rect, 0)
  pygame.draw.rect(screen, Colors.BLACK, player_header_rect, 9)
  msg = font.render("Players", 1, Colors.BLACK)
  screen.blit(msg, msg.get_rect(center = player_header_rect.center))
  
  player_rects: list[Rect] = []
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
    load_rect = Rect(window_width - (window_width//20 + load_width), window_height - (window_height//20 + load_height), load_width, load_height)
    pygame.draw.rect(screen, Colors.LIGHTGREEN , load_rect, 0)
    msg = font.render("SELECT", 1, Colors.BLACK)
    screen.blit(msg, msg.get_rect(center = load_rect.center))
  
  # Create an "x" button to back out of menu
  back_button_rect = top_right_corner_x_button(screen)
  
  return (player_rects, load_rect, back_button_rect)

# endregion

# region postgame gui

# TODO implement dropdown() here
def draw_endGameStats(players, statlist, hover_stat_int, clicked_stat_int, viewmode, graphfig) -> tuple[list[Rect], Rect]:
  
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
    
    text_field_rect = Rect(pos_x, pos_y, text_field_width, text_field_height)
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
  viewmode_rect = Rect(window_width - (window_width//20 + load_width), window_height - (window_height//20 + load_height), load_width, load_height)
  pygame.draw.rect(screen, Colors.LIGHTGREEN if viewmode == "STATS" else Colors.RED, viewmode_rect, 0)
  msg = font.render(viewmode, 1, Colors.BLACK)
  screen.blit(msg, msg.get_rect(center = viewmode_rect.center))
  
  return (statswap_rects, viewmode_rect)

# endregion
