import pygame
from pygame import Surface, Rect
import plotly
# plotly.io.kaleido.scope.mathjax = None
import numpy as np
from io import BytesIO
from typing import Callable

from objects import *
from common import HIDE_PERSONAL_INFO, Colors, Fonts, ratio

# region gui components

def clear_screen():
  screen.fill((255, 255, 255))

def resize_screen(event) -> Surface:
  return pygame.display.set_mode((event.w, event.h), pygame.RESIZABLE)

# TODO maybe remake these?
# resize rects to fit font
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

# resize font to fit in a rect
def dynamic_font(surface: Surface, rect: Rect, label: str, label_color: tuple[int, int, int], font_name: str, 
                 font_scale_max: int | float = .95, font_scale_min: int | float = .9, y_offset_div: int | None = None,
                 justification: str = "centered", noBlit = False, shared_font_size: int | None = None) -> int:
  if not label:
    return 0
  default_font_size = min(rect.w, rect.h) // 2 if shared_font_size is None else shared_font_size
  font = pygame.font.SysFont(font_name, default_font_size)
  label_surface = font.render(label, 1, label_color)
  
  font_size = default_font_size
  while label_surface.get_width() / rect.w > font_scale_max and shared_font_size is None:
    # print(label_surface.get_width(), font_scale_max * rect.w, font_scale_min * rect.w)
    font_size = ratio(label_surface.get_width(), rect.w, font_size, font_scale_max)
    font = pygame.font.SysFont(font_name, font_size)
    label_surface = font.render(label, 1, label_color)
  
  label_rect = label_surface.get_rect()
  
  if justification == "right":
    label_rect.right = rect.right
  elif justification == "left":
    label_rect.left = rect.left
  else:
    label_rect.centerx = rect.centerx
  
  label_rect.centery = rect.centery
  if y_offset_div is not None:
    label_rect.top = rect.top + rect.h//y_offset_div
  if not noBlit: surface.blit(label_surface, label_rect)
  return font_size

def create_square_dims(list: list) -> tuple[int, int]:
  # Calculate grid arangement (aim for square)
  cols = int(np.round(np.sqrt(len(list)), 0))
  rows = len(list)//cols + (1 if len(list)%cols != 0 else 0)
  return cols, rows

def gridifier(surface: Surface, width: int, height: int, top_left: tuple[int, int], labels: list[str], cols: int, rows: int,
              rect_color_func: Callable[[int], tuple[int, int, int] | None] | None, 
              label_color_func: Callable[[int], tuple[int, int, int] | None] | None,
              outline_color_func: Callable[[int], tuple[int, int, int] | None] | None = None, outline_width: int = 8, 
              underfill: bool = False, underfill_color: tuple[int, int, int] | None = None, font_name: str = Fonts.main, 
              rect_width_factor: int | float = 1, rect_height_factor: int | float = 1, font_scale_max: int | float = .95, 
              font_scale_min: int = .8, shared_font_size: int | None = None, 
              extra_render_func: Callable[[Surface, int, Rect, int], None] | None = None) -> list[Rect]:
  
  # Calculate rect sizing and arangement spacing
  rect_width  = int(width       // (cols + .5))
  rect_height = int(height      // (rows + .5))
  w_gap       = int((width - rect_width * cols) // (cols+1))
  h_gap       = int((height - rect_height * rows) // (rows+1))
  
  # Calculate the grid starting offset from (0, 0) of the surface
  offset_x = top_left[0] + w_gap + (cols-1) * rect_width * (1-rect_width_factor)
  offset_y = top_left[1] + h_gap + (rows-1) * rect_height * (1-rect_height_factor)
  offset_x, offset_y = int(offset_x), int(offset_y)
  
  if underfill and underfill_color is not None:
    max_x = offset_x + cols * rect_width * rect_width_factor + cols * w_gap
    max_y = offset_y + rows * rect_height * rect_height_factor + rows * h_gap
    underfill_rect = Rect(int(offset_x - w_gap//2), int(offset_y - h_gap//2), int(max_x - offset_x), int(max_y - offset_y)).scale_by(1.025, 1.025)
    pygame.draw.rect(surface, underfill_color, underfill_rect)
  
  # Create grid of rects
  rects = []
  for j in range(rows):
    for i in range(cols):
      if i + cols*j >= len(labels):
        break
      # Calculate the position of the rect
      pos = (offset_x + i * rect_width * rect_width_factor + i * w_gap, 
             offset_y + j * rect_height * rect_height_factor + j * h_gap)
      
      # Create the rect, add to rects, and draw to screen
      rect = Rect(int(pos[0]), int(pos[1]), int(rect_width * rect_width_factor), int(rect_height * rect_height_factor))
      rects.append(rect)
      if rect_color_func is not None and rect_color_func(i + cols*j) is not None:
        pygame.draw.rect(surface, rect_color_func(i + cols*j), rect)
      
      # Draw outline around rect if necessary
      if outline_color_func is not None and outline_color_func(i + cols*j) is not None:
        pygame.draw.rect(surface, outline_color_func(i + cols*j), rect, outline_width)
      
      # Create the label and draw to surface
      if label_color_func is not None and label_color_func(i + cols*j) is not None:
        font_size = dynamic_font(screen, rect, labels[i + cols*j], label_color_func(i + cols*j), font_name, 
                                 font_scale_max=font_scale_max, font_scale_min=font_scale_min, shared_font_size=shared_font_size)
      
      # Do extra stuff per rect if necessary
      if extra_render_func is not None:
        extra_render_func(screen, i + cols*j, rect, font_size)
  
  return rects

def dropdown(surface: Surface, width: int, height: int, top_left: tuple[int, int], header: str, choices: list[str] | None, 
             header_rect_color: tuple[int, int, int] | None, header_label_color: tuple[int, int, int] | None,
             choice_rect_color_func: Callable[[int], tuple[int, int, int] | None] | None, 
             choice_label_color_func: Callable[[int], tuple[int, int, int] | None] | None,
             header_outline_color: tuple[int, int, int] | None = None, 
             choice_outline_color_func: Callable[[int], tuple[int, int, int] | None] | None = None, header_outline_thick: int = 8, 
             choice_outline_thick: int = 8, font_name: str = Fonts.main, choice_share_font_size: bool = False, 
             label_justification: str = "centered", choice_justification: str = "centered",
             header_extra_render_func: Callable[[Surface, Rect, int], None] | None = None,
             choice_extra_render_func: Callable[[Surface, int, Rect, int], None] | None = None) -> list[Rect]:
  
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
  if header_rect_color is not None:
    pygame.draw.rect(surface, header_rect_color, header_rect, 0)
  
  # Draw outline around header rect if necessary
  if header_outline_color is not None:
    pygame.draw.rect(surface, header_outline_color, header_rect, header_outline_thick)
  
  # Create the label and blit to surface
  if header_label_color is not None:
    header_font_size = dynamic_font(surface, header_rect, header, header_label_color, font_name, justification=label_justification)
  
  # Do extra stuff to header rect if necessary
  if header_extra_render_func is not None:
    header_extra_render_func(screen, header_rect, header_font_size)
  
  if choice_share_font_size:
    shared_font_size = min([dynamic_font(surface, header_rect, choice, Colors.BLACK, font_name, default_font_size=45, noBlit=True) for choice in choices])
    print(shared_font_size)
  
  # Draw the Choices
  choice_rects = None
  if choices is not None:
    choice_rects = []
    for i, choice in enumerate(choices):
      # Calculate the position of the choice
      choice_rect = header_rect.copy()
      choice_rect.y += (i+1) * choice_rect.height
      choice_rects.append(choice_rect)
      
      if choice_rect_color_func is not None and choice_rect_color_func(i) is not None:
        pygame.draw.rect(surface, choice_rect_color_func(i), choice_rect, 0)
      
      # Draw outline around rect if necessary
      if choice_outline_color_func is not None and choice_outline_color_func(i) is not None:
        choice_outline_color = choice_outline_color_func(i)
        if choice_outline_color is not None:
          pygame.draw.rect(surface, choice_outline_color, choice_rect, choice_outline_thick)
      
      # Create the label and blit to surface
      if choice_label_color_func is not None and choice_label_color_func(i) is not None:
        if choice_share_font_size:
          choice_font_size = dynamic_font(surface, choice_rect, choice, choice_label_color_func(i), font_name, 
                                          justification=choice_justification, shared_font_size=shared_font_size)
        else:
          choice_font_size = dynamic_font(surface, choice_rect, choice, choice_label_color_func(i), font_name, justification=choice_justification)
      
      # Do extra stuff per rect if necessary
      if choice_extra_render_func is not None:
        choice_extra_render_func(screen, i, choice_rect, choice_font_size)
  
  return header_rect, choice_rects

def draw_slider(surface: Surface, slider_vec):
  slider_pos, dragging, slider_value, p_stocks = slider_vec
  
  surface_width, surface_height = surface.get_size()
  
  # Get the current mouse position and state
  mouse_pos = pygame.mouse.get_pos()
  mouse_pressed = pygame.mouse.get_pressed()
  
  # Calculate the x and y coordinates of the center of the slider
  x = surface_width // 2
  y = surface_height // 2
  
  # Calculate the length and height of the slider
  length = 4 * surface_width // 5
  height = surface_height // 80
  num_points = p_stocks // 2 + 1
  
  # Calculate the coordinates of the end points of the slider
  x1 = x - length // 2
  y1 = y - height // 2
  x2 = x + length // 2
  y2 = y + height // 2
  
  # Check if the mouse is currently over the slider
  if x1 <= mouse_pos[0] <= x2 and y1 <= mouse_pos[1] <= y2:
    # If the left mouse button is pressed, start dragging the slider
    if mouse_pressed[0] == 1:
      dragging = True
  
  # If the left mouse button is released, stop dragging the slider
  if mouse_pressed[0] == 0:
    dragging = False
  
  # If the slider is being dragged, update the slider position
  if dragging:
    slider_pos = mouse_pos[0] - x1
  
  # Make sure the slider position is within the valid range
  slider_pos = max(0, min(slider_pos, length))
  
  # Calculate the current value of the slider
  slider_value = int(slider_pos / length * num_points)
  
  # Snap the slider to the nearest integer fraction of the bar
  slider_pos = int(slider_value / num_points * length)
  
  # Draw the slider bar
  slider_rect = pygame.Rect(x1, y1, length, height)
  pygame.draw.rect(surface, (0, 0, 0), slider_rect)
  
  # Draw the slider handle
  bar_rect = pygame.Rect(x1 + slider_pos, y1, 10, height)
  pygame.draw.rect(surface, (0, 0, 0), bar_rect)
  
  # Display the current value of the slider
  font_size = min(surface_width, surface_height) // 20
  font = pygame.font.SysFont(Fonts.main, font_size)
  text = font.render(str(slider_value), True, (0, 0, 0))
  surface.blit(text, (x - text.get_width() // 2, y - text.get_height() // 2))
  
  return [slider_rect, bar_rect]

# endregion

# region gui prebuilts

def top_center_title(surface: Surface, title: str, y_offset_div: int = 60) -> Rect:
  surface_width, surface_height = surface.get_size()
  
  rect_width = surface_width * (2/3)
  rect_height = surface_height // 10
  rect = pygame.Rect(surface_width //2 - rect_width//2, 0,
                     rect_width, rect_height)
  # pygame.draw.rect(surface, Colors.GRAY, rect)
  
  font_size = dynamic_font(screen, rect, title, Colors.BLACK, Fonts.main, y_offset_div=y_offset_div)
  
  return rect

def row_buttons(surface: Surface, choices: list[str], rect_color_func: Callable[[int], tuple[int, int, int]] | None = None, 
                outline_color_func: Callable[[int], tuple[int, int, int]] | None = None, 
                row_align = "bottom", row_width_div: int = 1, row_height_div: int = 4,
                font_scale_max: int =.8, font_scale_min: int =.7, shared_font_size: int | None = None):
  surface_width, surface_height = surface.get_size()
  width = surface_width // row_width_div
  height = surface_height // row_height_div
  
  if row_align == "bottom":
    top_left = (0, surface_height - height)
  elif row_align == "top":
    top_left = (0, 0)
  else: # center
    top_left = (0, (surface_height - height) // 2)
  
  if rect_color_func is None:
    def rect_color_func(i: int) -> tuple[int, int, int]:
      return Colors.RED if i == 0 else Colors.GREEN
  
  button_rects = gridifier(surface, width, height, top_left, choices, len(choices), 1, 
                             rect_color_func, lambda x: Colors.WHITE, outline_color_func,
                             rect_width_factor=.9, font_scale_max=font_scale_max, font_scale_min=font_scale_min,
                             shared_font_size=shared_font_size)
  
  return button_rects

def central_textbox(surface: Surface, text: str):
  surface_width, surface_height = surface.get_size()
  width = surface_width
  height = int(surface_height * (2/5))
  top_left = (0, surface_height // 3 - height // 5)
  
  textbox_rect = gridifier(surface, width, height, top_left, [text,], 1, 1, lambda x: Colors.GRAY,
                           lambda x: Colors.BLACK, lambda x: Colors.GREEN)[0]
  
  return textbox_rect

def single_button(surface: Surface, label: str, color: tuple[int, int, int] = Colors.LIGHTGREEN,
                        label_color: tuple[int, int, int] = Colors.BLACK, 
                        rect_width_div: int = 7, rect_height_div: int = 7,
                        rect_offest_x: float = 4/5, rect_offest_y: float = 4/5,) -> Rect:
  surface_width, surface_height = surface.get_size()
  
  # defaults to bottom right of the surface
  rect_width = int(surface_width // rect_width_div)
  rect_height = int(surface_height // rect_height_div)
  
  pos_x = surface_width * rect_offest_x
  pos_y = surface_height * rect_offest_y
  pos_x, pos_y = int(pos_x), int(pos_y)
  
  button_rect = Rect(pos_x, pos_y, rect_width, rect_height)
  pygame.draw.rect(surface, color, button_rect)
  
  font_size = dynamic_font(surface, button_rect, label, label_color, Fonts.main)
  
  return button_rect

# TODO finish this
def dpi(surface: Surface, p: Player, rect_width_div=4):
  surface_width, surface_height = surface.get_size()
  
  width = surface_width // rect_width_div
  height = surface_height * (7/12)
  top_left = (surface_width - width, 0)
  
  choices = [f'${p.bal}',] + [f'{stock}: {p.stocks[stock]}' for stock in p.stocks.keys()]
  
  text_rects = dropdown(surface, width, height, top_left, p.name, choices, None, Colors.BLACK, lambda x: [Colors.RED, Colors.YELLOW][x%2], lambda x: Colors.BLACK,
                        choice_share_font_size=True, choice_justification="right", label_justification="right")


# TODO remake this
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
  label_rect.center = (back_button_rect.centerx + 1, back_button_rect.centery - 3)
  surface.blit(label, label_rect)
  
  return back_button_rect

# TODO remake this
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

from pregame import screen

# region pregame gui

def draw_fullscreenSelect(drawinfo) -> list[Rect]:
  # Decide title and button labels
  title = 'Default Yes/No Question?'
  bianary_choices = ['No', 'Yes']
  
  if drawinfo == 'hostJoin': 
    title = 'Will you Host or Join a Game?'
    bianary_choices = ['Host', 'Join']
  elif drawinfo == 'hostLocal': 
    title = 'Will you Host Locally or on a Server?'
    bianary_choices = ['Local', 'Server']
  elif drawinfo == 'loadSave': 
    title = 'Would You Like to Load a Save?'
    bianary_choices = ['New Game', 'Load Save']
  elif drawinfo == 'setPlayerNamesLocal': 
    title = 'Use Standard Settings?'
  elif drawinfo == 'askToBuy': 
    title = 'Would You Like to Buy Stock?'
  elif drawinfo == 'endGameConfirm': 
    title = 'Would You Like to End the Game?'
  elif drawinfo == 'makeSave': 
    title = 'Would You Like to Save the Current Game?'
  elif drawinfo == 'endGameStats': 
    title = 'Would You Like to Show End Game Stats?'
  
  title_rect = top_center_title(screen, title)
  
  yesandno_rects = row_buttons(screen, bianary_choices, row_align="center", row_height_div=2,
                               font_scale_max=0.65, font_scale_min=0.6)
  
  return yesandno_rects

def draw_singleTextBox(ipTxtBx: str, title: str, confirm_label: str) -> list[Rect]:
  
  title_rect = top_center_title(screen, title)
  
  textbox_rect = central_textbox(screen, ipTxtBx)
  
  yesandno_rects = row_buttons(screen, ['Back', confirm_label])
  
  return yesandno_rects

def draw_setPlayerNameJoin(playernameTxtbx: str) -> tuple[Rect]:
  
  title_rect = top_center_title(screen, "Enter Your Username")
  
  textbox_rect = central_textbox(screen, playernameTxtbx)
  
  confirm_rect = single_button(screen, "CONFRIM", Colors.GREEN, Colors.WHITE, rect_width_div=3, 
                               rect_offest_x=1/3, rect_offest_y=9/12)
  
  return confirm_rect

# gridifier-based
# TODO combine these two funcs?
def draw_setPlayerNamesLocal(player_names: list[str], clicked_textbox_int: int) -> tuple[list[Rect], list[Rect]]:
  window_width, window_height = screen.get_size()
  
  title_rect = top_center_title(screen, "Name The Players")
  
  # region Draw player name grid
  grid_width = int(window_width)
  grid_height = int(window_height * (72/100))
  top_left = (0, window_width // 30)
  
  def outline_color_func(i: int) -> tuple[int, int, int]:
    return Colors.GREEN if i == clicked_textbox_int else None
  
  cols, rows = create_square_dims(player_names)
  
  player_rects = gridifier(screen, grid_width, grid_height, top_left, player_names, cols, rows, 
                           lambda x: Colors.GRAY, lambda x: Colors.BLACK, outline_color_func)
  # endregion
  
  yesandno_rects = row_buttons(screen, ['Back to Settings', 'Start Game'])
  
  # Create an "x" button to back out of menu
  back_button_rect = top_right_corner_x_button(screen)
  
  return player_rects, yesandno_rects, back_button_rect

def draw_waitingForJoin(clientMode: str, connected_players: list[Player], clicked_textbox_int: int, gameStartable: bool) -> tuple[list[Rect], list[Rect]]:
  
  title_rect = top_center_title(screen, "Lobby: Waiting for Players")
  
  # region Draw player name grid
  window_width, window_height = screen.get_size()
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
  # endregion
  
  button_labels = ['Disconnect', 'Mark Ready']
  rect_colors = [Colors.RED, Colors.GREEN]
  if clientMode == "hostServer":
    button_labels = ['Kick Player', 'Mark Ready']
    if gameStartable: 
      button_labels.append('Start Game')
      rect_colors.append(Colors.DARKGREEN)
  
  def rect_color_func(i):
    return rect_colors[i]
  
  button_rects = row_buttons(screen, button_labels, rect_color_func)
  
  return player_rects, button_rects

# dropdown-based
def draw_selectSaveFile(drawinfo: tuple[bool, int, bool, int], saveinfo) -> tuple[Rect, list[Rect], Rect, Rect]:
  hover_directory, hover_save_int, clicked_directory, clicked_save_int = drawinfo
  saves_path, savefiles = saveinfo
  
  title_rect = top_center_title(screen, "Select Save File")
  
  # region Create save dropdown
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
  # endregion
  
  # Draw load save button if save clicked
  load_rect = None
  if clicked_save_int is not None:
    load_rect = single_button(screen, "LOAD")
  
  # Create an "x" button to back out of menu
  back_button_rect = top_right_corner_x_button(screen)
  
  return header_rect, choice_rects, load_rect, back_button_rect

def draw_selectPlayerFromSave(drawinfo: tuple[int, int], unclaimed_players: list[Player]) -> tuple[list[Rect], Rect, Rect]:
  hover_player_int, clicked_player_int = drawinfo
  
  title_rect = top_center_title(screen, "Select Player From Save File")
  
  # region Create player dropdown
  window_width, window_height = screen.get_size()
  width = window_width * (3/7)
  height = window_height - window_height // 24
  top_left = (window_width//120, window_height // 24)
  
  def choice_rect_color_func(i: int) -> tuple[int, int, int]:
    return Colors.LIGHTGREEN if i == clicked_player_int else Colors.GRAY
  
  def choice_outline_color_func(i: int) -> tuple[int, int, int]:
    return Colors.GREEN if i == hover_player_int else None
  
  header_rect, player_rects = dropdown(screen, width, height, top_left, "  Players  ", unclaimed_players,
                                       Colors.RED, Colors.BLACK, 
                                       choice_rect_color_func, lambda x: Colors.BLACK, 
                                       Colors.BLACK, choice_outline_color_func)
  # endregion
  
  # Draw player info and select player button if player clicked
  load_rect = None
  if clicked_player_int is not None:
    draw_player_info(unclaimed_players[clicked_player_int], window_width//40)
    load_rect = single_button(screen, "SELECT")
  
  # Create an "x" button to back out of menu
  back_button_rect = top_right_corner_x_button(screen)
  
  return player_rects, load_rect, back_button_rect

# non-template
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
  
  yesandno_rects = row_buttons(screen, ['Reset to Default', 'Create Players'], row_height_div=6)
  
  # Create an "x" button to back out of menu
  back_button_rect = top_right_corner_x_button(screen)
  
  return text_field_rects, yesandno_rects, back_button_rect

# endregion

# region postgame gui

def draw_endGameStats(players: list[Player], statlist, hover_stat_int: int, clicked_stat_int: int, viewByField: bool, graphfig) -> tuple[list[Rect], Rect]:
  
  title_rect = top_center_title(screen, "End Game Stats")
  
  # region Create stats/player dropdown
  window_width, window_height = screen.get_size()
  width = window_width * (3/7)
  height = window_height - window_height // 24
  top_left = (window_width//120, window_height // 24)
  
  header = "Stats by Field" if viewByField else "Stats by Player"
  choices = statlist if viewByField else [p.name for p in players] 
  
  def choice_rect_color_func(i: int) -> tuple[int, int, int]:
    return Colors.LIGHTGREEN if i == clicked_stat_int else Colors.GRAY
  
  def choice_outline_color_func(i: int) -> tuple[int, int, int]:
    return Colors.GREEN if i == hover_stat_int else None
  
  header_rect, statswap_rects = dropdown(screen, width, height, top_left, header, choices,
                                       Colors.RED, Colors.BLACK, 
                                       choice_rect_color_func, lambda x: Colors.BLACK, 
                                       Colors.BLACK, choice_outline_color_func)
  # endregion
  
  #Draw graph to the screen
  if clicked_stat_int is not None and graphfig is not None:
    scale = min(1.35 * window_width/1600, 1.3 * window_height/900)
    figBytes = BytesIO(plotly.io.to_image(graphfig, format='png', scale=scale))
    graph_surface = pygame.image.load(figBytes)
    screen.blit(graph_surface, graph_surface.get_rect(right=window_width, centery=window_height//2))
  
  # Draw button to change viewmode
  label = "View by Field" if viewByField else "View by Player"
  color = Colors.LIGHTGREEN if viewByField else Colors.RED
  viewByField_rect = single_button(screen, label, color, rect_width_div=6, rect_height_div=10, rect_offest_y=8/9)
  
  return (statswap_rects, viewByField_rect)

# endregion
