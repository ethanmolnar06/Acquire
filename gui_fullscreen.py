import pygame
from pygame import Surface, Rect
from pygame.font import Font
from plotly.graph_objects import Figure
from kaleido.scopes.plotly import PlotlyScope
scope = PlotlyScope()
import numpy as np
from io import BytesIO
from typing import Callable

from objects import *
from common import HIDE_PERSONAL_INFO, Colors, Fonts, iter_flatten

# region gui components

def clear_screen(surface: Surface):
  surface.fill((255, 255, 255))

def resize_screen(event) -> Surface:
  return pygame.display.set_mode((event.w, event.h), pygame.RESIZABLE)

# TODO maybe remake these two?
# resize rects to fit font
def horizontal_refontsizer(rect_width: int, default_font_size: int, labels: list[str], font_name: str = Fonts.main, spacer_allocated: int = 250) -> tuple[Font, int]:
  # resize all font across grid to fit largest entry
  longestheader = max([len(h) for h in labels])
  font_size = default_font_size
  if longestheader * default_font_size * len(labels) + spacer_allocated > rect_width:
    font_size = int(1.7 * (rect_width - spacer_allocated) / (longestheader * len(labels)))
  header_font = pygame.font.Font(font_name, font_size)
  return header_font, font_size

def vertical_refontsizer(rect_height: int, default_font_size: int, pos_y: int, labels: list[str], font_name: str = Fonts.main) -> tuple[Font, int]:
  col_stand_height = pos_y + (2 + len(labels)) * default_font_size * 11/10
  font_size = default_font_size
  if col_stand_height >= rect_height:
    font_size = int(default_font_size * (1 - (col_stand_height - rect_height)/rect_height) )
  info_font = pygame.font.Font(font_name, font_size)
  return info_font, font_size

# resize font to fit in a rect
def dynamic_font(rect: Rect, label: str, font_name: str, font_scale_max: int | float = .95, default_font_size: int = 0) -> tuple[Font, int]:
  if not label:
    return None, 0
  if not default_font_size:
    default_font_size = max(min(rect.w, rect.h) // 2, 50)
  font = pygame.font.Font(font_name, default_font_size)
  label_surface = font.render(label, 1, Colors.BLACK)
  font_size = default_font_size
  
  # print(label, font_size, round(label_surface.get_width() / rect.w, 2), round(label_surface.get_height() / rect.h, 2))
  # print(font_scale_max, label_surface.get_width() / rect.w > font_scale_max, label_surface.get_height() / rect.h > font_scale_max)
  
  while label_surface.get_width() / rect.w > font_scale_max or label_surface.get_height() / rect.h > font_scale_max:
    # print(label, font_size, round(label_surface.get_width() / rect.w, 2), round(label_surface.get_height() / rect.h, 2))
    font_size = int(font_size * font_scale_max)
    font = pygame.font.Font(font_name, font_size)
    label_surface = font.render(label, 1, Colors.BLACK)
  
  # print(label, font_size, round(label_surface.get_width() / rect.w, 2), round(label_surface.get_height() / rect.h, 2))
  
  return font, font_size

def blit_font_to_rect(surface: Surface, font: Font, rect: Rect, label: str, label_color: tuple[int, int, int],
                      justification: str = "centered", vert_justification: str = "centered", font_offset_div: int = 0) -> Rect:
  label_surface = font.render(label, 1, label_color)
  label_rect = label_surface.get_rect()
  
  if justification == "right":
    label_rect.right = rect.right
  elif justification == "left":
    label_rect.left = rect.left
  else:
    label_rect.centerx = rect.centerx
  
  if vert_justification == "top":
    label_rect.top = rect.top
  elif vert_justification == "bottom":
    label_rect.bottom = rect.bottom
  else:
    label_rect.centery = rect.centery
  
  if font_offset_div:
    label_rect.centery += rect.h//font_offset_div
  surface.blit(label_surface, label_rect)
  
  return label_rect

def create_square_dims(list: list) -> tuple[int, int]:
  # Calculate grid arangement (aim for square)
  cols = int(np.round(np.sqrt(len(list)), 0))
  rows = len(list)//cols + (1 if len(list)%cols != 0 else 0)
  return cols, rows

def gridifier(surface: Surface, subrect: Rect, labels: list[str] | list[list[str]], cols: int | None, rows: int | None,
              rect_color_func: Callable[[int], tuple[int, int, int] | None] | None, 
              label_color_func: Callable[[int], tuple[int, int, int] | None] | None,
              outline_color_func: Callable[[int], tuple[int, int, int] | None] | None = None, outline_width: int = 8, 
              underfill: bool = False, underfill_color: tuple[int, int, int] | None = None, 
              rect_width_factor: int | float = 1, rect_height_factor: int | float = 1, rect_width_spacing_factor: int | float = 1,
              rect_height_spacing_factor: int | float = 1, extra_render_func: Callable[[Surface, int, Rect, int], None] | None = None,
              font_name: str = Fonts.main, font_scale_max: int | float = .95, share_font_size: bool = False, default_font_size: int = 0,
               allignment: str = "left", forceSquare: bool = False) -> list[Rect]:
  
  # compensate for non-symmetric grids
  if isinstance(labels[0], list):
    rows = len(labels)
    cols = max([len(l) for l in labels])
  label_text = iter_flatten(labels)
  
  # Calculate rect sizing and arangement spacing
  rect_width  = int(subrect.w  // (cols + .5 * rect_width_spacing_factor) )
  rect_height = int(subrect.h // (rows + .5 * rect_height_spacing_factor))
  if forceSquare:
    rect_width = rect_height = min(rect_width, rect_height)
  w_gap       = int((subrect.w - rect_width * cols) // (cols+1))
  h_gap       = int((subrect.h - rect_height * rows) // (rows+1))
  
  # Calculate the grid starting offset from (0, 0) of the surface
  offset_x = subrect.left + w_gap + (cols-1) * rect_width * (1-rect_width_factor)
  offset_y = subrect.top + h_gap + (rows-1) * rect_height * (1-rect_height_factor)
  offset_x, offset_y = int(offset_x), int(offset_y)
  
  if share_font_size:
    fonts_and_sizes = [dynamic_font(Rect(0, 0, rect_width, rect_height), text, font_name, font_scale_max=font_scale_max, 
                                  default_font_size=default_font_size) for text in label_text]
    font, font_size = min(fonts_and_sizes, key=lambda x: x[1])
  
  if underfill and underfill_color is not None:
    max_x = offset_x + cols * rect_width * rect_width_factor + cols * w_gap
    max_y = offset_y + rows * rect_height * rect_height_factor + rows * h_gap
    underfill_rect = Rect(int(offset_x - w_gap//2), int(offset_y - h_gap//2), int(max_x - offset_x), int(max_y - offset_y)).scale_by(1.025, 1.025)
    pygame.draw.rect(surface, underfill_color, underfill_rect)
  
  # Create grid of rects
  n = 0
  rects = []
  for j in range(rows):
    if isinstance(labels[0], list):
      cols = len(labels[j])
    
    # Calculate the grid starting offset from (0, 0) of the surface
    if allignment == "center":
      offset_x = subrect.left + (subrect.w - rect_width * rect_width_factor * cols - w_gap * (cols-1))//2
    else:
      offset_x = subrect.left + w_gap + (cols-1) * rect_width * (1-rect_width_factor)
    offset_y = subrect.top + h_gap + (rows-1) * rect_height * (1-rect_height_factor)
    offset_x, offset_y = int(offset_x), int(offset_y)
    
    for i in range(cols):
      if not isinstance(labels[0], list) and n >= len(labels):
        break
      # Calculate the position of the rect
      pos = (offset_x + i * rect_width * rect_width_factor + i * w_gap, 
             offset_y + j * rect_height * rect_height_factor + j * h_gap)
      
      # Create the rect, add to rects, and draw to screen
      rect = Rect(int(pos[0]), int(pos[1]), int(rect_width * rect_width_factor), int(rect_height * rect_height_factor))
      rects.append(rect)
      if rect_color_func is not None and rect_color_func(n) is not None:
        pygame.draw.rect(surface, rect_color_func(n), rect)
      
      # Draw outline around rect if necessary
      if outline_color_func is not None and outline_color_func(n) is not None:
        pygame.draw.rect(surface, outline_color_func(n), rect, outline_width)
      
      # Create the label and draw to surface
      if label_text[n] and label_color_func is not None and label_color_func(n) is not None:
        if not share_font_size:
          font, font_size = dynamic_font(rect, label_text[n], font_name, font_scale_max=font_scale_max, default_font_size=default_font_size)
        if font is not None:
          blit_font_to_rect(surface, font, rect, label_text[n], label_color_func(n))
      
      # Do extra stuff per rect if necessary
      if extra_render_func is not None:
        extra_render_func(surface, n, rect, font_size)
      
      n += 1
  
  return rects

def dropdown(surface: Surface, subrect: Rect, header: str, choices: list[str] | None, 
             header_rect_color: tuple[int, int, int] | None, header_label_color: tuple[int, int, int] | None,
             choice_rect_color_func: Callable[[int], tuple[int, int, int] | None] | None, 
             choice_label_color_func: Callable[[int], tuple[int, int, int] | None] | None,
             header_outline_color: tuple[int, int, int] | None = None, 
             choice_outline_color_func: Callable[[int], tuple[int, int, int] | None] | None = None, 
             header_outline_thick: int = 8, choice_outline_thick: int = 8, 
             font_name: str = Fonts.main, share_font_size: bool = False, default_font_size: int = 0,
             label_justification: str = "centered", choice_justification: str = "centered", 
             extras_index: int | None = None, extras_justification: str = "centered",
             header_extra_render_func: Callable[[Surface, Rect, int], None] | None = None,
             choice_extra_render_func: Callable[[Surface, int, Rect, int], None] | None = None) -> tuple[Rect, list[Rect]]:
  
  # Calculate dropdown arangement
  if choices is None:
    rows = 6
  else:
    rows = max(len(choices), 6)
  
  # Calculate rect sizing and arangement spacing
  w_gap       = 0
  h_gap       = 0
  header_rect = Rect(subrect.left + w_gap, subrect.top + h_gap, 
                     int(subrect.w  // (1.1)), int(subrect.h // (rows + 1)))
  
  # Create the header rect and draw to screen
  if header_rect_color is not None:
    pygame.draw.rect(surface, header_rect_color, header_rect, 0)
  
  # Draw outline around header rect if necessary
  if header_outline_color is not None:
    pygame.draw.rect(surface, header_outline_color, header_rect, header_outline_thick)
  
  # Create the label and blit to surface
  if header and header_label_color is not None:
    font, font_size = dynamic_font(header_rect, header, font_name, default_font_size=default_font_size)
    if font is not None:
      blit_font_to_rect(surface, font, header_rect, header, header_label_color, justification=label_justification)
  
  # Do extra stuff to header rect if necessary
  if header_extra_render_func is not None:
    header_extra_render_func(surface, header_rect, font_size)
  
  # Draw the Choices
  if share_font_size:
    textlengthpairs = [(text, len(text)) for text in choices[:extras_index]]
    textlengthpairs.sort(key=lambda x: x[1], reverse=True)
    font, font_size = dynamic_font(header_rect, textlengthpairs[0][0], font_name, default_font_size=default_font_size)
  
  choice_rects = None
  if choices is not None:
    choice_rects = []
    for i, choice in enumerate(choices):
      if choice:
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
          if not share_font_size or i >= len(choices[:extras_index]):
            font, font_size = dynamic_font(header_rect, choice, font_name, default_font_size=default_font_size)
          if font is not None:
            justification = choice_justification if i < len(choices[:extras_index]) else extras_justification
            font_offset_div = 0
            if i < len(choices) - 1 and choices[i + 1] == "":
              # I know this is a terrible, horrible way to do this
              # too bad!
              choice_rect.y += choice_rect.height
              choice_rects.append(choice_rect.copy())
              pygame.draw.rect(surface, choice_rect_color_func(i + 1), choice_rect, 0)
              choice_rect.y -= choice_rect.height
              font_offset_div = 2
            blit_font_to_rect(surface, font, choice_rect, choice, choice_label_color_func(i), justification=justification, font_offset_div=font_offset_div)
        
        # Do extra stuff per rect if necessary
        if choice_extra_render_func is not None:
          choice_extra_render_func(surface, i, choice_rect, font_size)
  
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
  font = pygame.font.Font(Fonts.main, font_size)
  text = font.render(str(slider_value), True, (0, 0, 0))
  surface.blit(text, (x - text.get_width() // 2, y - text.get_height() // 2))
  
  return [slider_rect, bar_rect]

# endregion

# region gui prebuilts

def default_dropdown_rect(surface: Surface) -> Rect:
  window_width, window_height = surface.get_size()
  
  width = window_width * (3/7)
  height = window_height - window_height // 24
  top_left = (window_width//120, window_height // 24)
  
  return Rect(top_left[0], top_left[1], width, height)

def top_rect_title(surface: Surface, title: str, y_offset_div: int = 0, font_offset_div: int = 50, surface_subrect: Rect = None, justification: str = "centered") -> Rect:
  if surface_subrect:
    rect = surface_subrect.copy()
  else:
    surface_width, surface_height = surface.get_size()
    rect = pygame.Rect(0, 0, surface_width, surface_height)
  
  text_rect = rect.scale_by(2/3, 1/15)
  text_rect.top = rect.top
  text_rect.top += rect.h//y_offset_div if y_offset_div else y_offset_div
  # pygame.draw.rect(surface, Colors.GREEN, text_rect) # DEBUG
  
  font, font_size = dynamic_font(text_rect, title, Fonts.main)
  label_rect = blit_font_to_rect(surface, font, text_rect, title, Colors.BLACK, justification=justification,
                                 vert_justification="top", font_offset_div=font_offset_div)
  
  return label_rect

def row_buttons(surface: Surface, choices: list[str], rect_color_func: Callable[[int], tuple[int, int, int]] | None = None, 
                outline_color_func: Callable[[int], tuple[int, int, int]] | None = None, 
                row_align = "bottom", row_width_div: int = 1, row_height_div: int = 4,
                font_scale_max: int =.8, share_font_size: bool = True):
  surface_width, surface_height = surface.get_size()
  subrect = Rect(0,                              0,
                 surface_width // row_width_div, surface_height // row_height_div)
  
  if row_align == "bottom":
    subrect.bottom =  surface_height
  elif row_align == "center":
    subrect.centery =  surface_height // 2
  
  if rect_color_func is None:
    def rect_color_func(i: int) -> tuple[int, int, int]:
      return Colors.RED if i == 0 else Colors.GREEN
  
  button_rects = gridifier(surface, subrect, choices, len(choices), 1, 
                             rect_color_func, lambda x: Colors.WHITE, outline_color_func,
                             rect_width_factor=.9, font_scale_max=font_scale_max,
                             share_font_size=share_font_size)
  
  return button_rects

def central_textbox(surface: Surface, text: str):
  surface_width, surface_height = surface.get_size()
  subrect_height = surface_height * (2/5)
  subrect = Rect(0, surface_height // 3 - subrect_height // 5,
              surface_width, subrect_height)
  
  textbox_rect = gridifier(surface, subrect, [text,], 1, 1, lambda x: Colors.GRAY,
                           lambda x: Colors.BLACK, lambda x: Colors.GREEN)[0]
  
  return textbox_rect

def single_button(surface: Surface, label: str, color: tuple[int, int, int] | None = Colors.LIGHTGREEN,
                        label_color: tuple[int, int, int] = Colors.BLACK, surface_subrect: Rect | None = None,
                        rect_width_div: int = 7, rect_height_div: int = 7,
                        rect_offest_x: int | float = 5, rect_offest_y: float = 5,) -> Rect:
  if surface_subrect:
    rect = surface_subrect.copy()
  else:
    surface_width, surface_height = surface.get_size()
    rect = pygame.Rect(0, 0, surface_width, surface_height)
  
  # defaults to bottom right of the surface
  button_rect = rect.scale_by(1/rect_width_div, 1/rect_height_div)
  button_rect.bottomright = rect.bottomright
  button_rect.right -= button_rect.w // rect_offest_x
  button_rect.bottom -= button_rect.h // rect_offest_y
  
  if color is not None:
    pygame.draw.rect(surface, color, button_rect)
    
    font, font_size = dynamic_font(button_rect, label, Fonts.main)
    blit_font_to_rect(surface, font, button_rect, label, label_color)
  
  return button_rect

def draw_player_info(surface: Surface, p: Player | Bank, subrect: Rect | None = None, extra_text: list[str] | None = None,
                     label_justification: str = "right", choice_justification: str = "right",
                     highlight_player_name: bool = False) -> tuple[Rect, list[Rect]]:
  surface_width, surface_height = surface.get_size()
  
  if subrect is None:
    subrect = Rect(surface_width * 25/32, 0,
                   surface_width * 7/32, surface_height * 16/24)
  
  balance = p.balance if 'balance' in p.__dict__.keys() else f'${p.bal}'
  choices = [balance,] + [f'{stock}: {p.stocks[stock]}' for stock in p.stocks.keys()]
  n_choices = len(choices)
  
  header_label_color = Colors.RED if highlight_player_name else Colors.BLACK
  
  def choice_rect_color_func(i):
    if i < n_choices:
      return None # [Colors.RED, Colors.YELLOW][i%2]
    else:
      return Colors.GRAY
  
  extras_index = None
  if extra_text is not None:
    choices += extra_text
    extras_index = -len(extra_text)
  
  header_rect, choice_rects = dropdown(surface, subrect, p.name, choices, None, 
                                       header_label_color, choice_rect_color_func, lambda x: Colors.BLACK, share_font_size=True, 
                                       label_justification=label_justification, choice_justification=choice_justification, extras_index=extras_index)
  
  return header_rect, choice_rects

# TODO remake this?
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

# endregion

def clear_screen(surface: Surface):
  surface.fill((255, 255, 255))

# region pregame gui
# pre-built-based
def draw_fullscreenSelect(surface: Surface, drawinfo: str) -> list[Rect]:
  # Decide title and button labels
  title = 'Default Yes/No Question?'
  bianary_choices = ['No', 'Yes']
  
  if drawinfo == 'hostJoin': 
    title = 'Will you Host or Join a Game?'
    bianary_choices = ['Host', 'Join']
  elif drawinfo == 'proxyNAT': 
    title = 'Will you Join via a Proxy or on local NAT?'
    bianary_choices = ['Proxy', 'NAT']
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
  
  title_rect = top_rect_title(surface, title)
  
  yesandno_rects = row_buttons(surface, bianary_choices, row_align="center", row_height_div=2,
                               font_scale_max=0.85, share_font_size=True)
  
  return yesandno_rects

def draw_singleTextBox(surface: Surface, ipTxtBx: str, title: str, confirm_label: str) -> list[Rect]:
  
  title_rect = top_rect_title(surface, title)
  
  textbox_rect = central_textbox(surface, ipTxtBx)
  
  yesandno_rects = row_buttons(surface, ['Back', confirm_label])
  
  return yesandno_rects

def draw_setPlayerNameJoin(surface: Surface, playernameTxtbx: str) -> tuple[Rect]:
  
  title_rect = top_rect_title(surface, "Enter Your Username")
  
  textbox_rect = central_textbox(surface, playernameTxtbx)
  
  confirm_rect = single_button(surface, "CONFRIM", Colors.GREEN, Colors.WHITE, rect_width_div=3, 
                               rect_offest_x=3, rect_offest_y=4)
  
  return confirm_rect

# gridifier-based
def draw_setPlayerNamesLocal(surface: Surface, player_names: list[str], clicked_textbox_int: int) -> tuple[list[Rect], list[Rect]]:
  title_rect = top_rect_title(surface, "Name The Players")
  
  # region Draw player name grid
  window_width, window_height = surface.get_size()
  subrect = Rect(0, window_width // 30,
                 window_width, int(window_height * (72/100)))
  
  def outline_color_func(i: int) -> tuple[int, int, int]:
    return Colors.GREEN if i == clicked_textbox_int else None
  
  cols, rows = create_square_dims(player_names)
  
  player_rects = gridifier(surface, subrect, player_names, cols, rows, 
                           lambda x: Colors.GRAY, lambda x: Colors.BLACK, outline_color_func)
  # endregion
  
  yesandno_rects = row_buttons(surface, ['Back to Settings', 'Start Game'])
  
  # Create an "x" button to back out of menu
  back_button_rect = top_right_corner_x_button(surface)
  
  return player_rects, yesandno_rects, back_button_rect

def draw_waitingForJoin(surface: Surface, clientMode: str, connected_players: list[Player], clicked_textbox_int: int, gameStartable: bool) -> tuple[list[Rect], list[Rect]]:
  
  title_rect = top_rect_title(surface, "Lobby: Waiting for Players")
  
  # region Draw player name grid
  window_width, window_height = surface.get_size()
  subrect = Rect(0, window_width // 40,
                 window_width, int(window_height * (19/25)))
  
  player_names = [p.name for p in connected_players]
  cols, rows = create_square_dims(player_names)
  
  def outline_color_func(i: int) -> tuple[int, int, int]:
    if clientMode == "hostServer":
      return Colors.GREEN if i == clicked_textbox_int else Colors.BLACK
    return Colors.BLACK
  
  ready = [p.ready for p in connected_players]
  def label_color_func(i: int) -> tuple[int, int, int]:
    return Colors.GREEN if ready[i] else Colors.BLACK
  
  player_rects = gridifier(surface, subrect, player_names, cols, rows,
                           lambda x: Colors.GRAY, label_color_func, outline_color_func, rect_height_spacing_factor=.9)
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
  
  button_rects = row_buttons(surface, button_labels, rect_color_func)
  
  return player_rects, button_rects

# dropdown-based
def draw_selectSaveFile(surface: Surface, drawinfo: tuple[bool, int, bool, int], saveinfo) -> tuple[Rect, list[Rect], Rect, Rect]:
  hover_directory, hover_save_int, clicked_directory, clicked_save_int = drawinfo
  saves_path, savefiles = saveinfo
  
  title_rect = top_rect_title(surface, "Select Save File")
  
  # region Create save dropdown
  drect: Rect = default_dropdown_rect(surface)
  
  header = saves_path if not HIDE_PERSONAL_INFO else "Saves Directory"
  header_rect_color = Colors.RED if clicked_directory else Colors.GRAY
  header_outline_color =  Colors.GREEN if hover_directory else Colors.BLACK
  
  choices = savefiles if not HIDE_PERSONAL_INFO else [f"Save {i+1}" for i in range(len(savefiles))]
  
  def choice_rect_color_func(i: int) -> tuple[int, int, int]:
    return Colors.LIGHTGREEN if i == clicked_save_int and clicked_directory else Colors.GRAY
  
  def choice_outline_color_func(i: int) -> tuple[int, int, int]:
    return Colors.GREEN if i == hover_save_int and not hover_directory else None
  
  header_rect, choice_rects = dropdown(surface, drect, header, choices if clicked_directory else None,
                                       header_rect_color, Colors.BLACK, 
                                       choice_rect_color_func, lambda x: Colors.BLACK, 
                                       header_outline_color, choice_outline_color_func)
  # endregion
  
  # Draw load save button if save clicked
  load_rect = None
  if clicked_save_int is not None:
    load_rect = single_button(surface, "LOAD")
  
  # Create an "x" button to back out of menu
  back_button_rect = top_right_corner_x_button(surface)
  
  return header_rect, choice_rects, load_rect, back_button_rect

def draw_selectPlayerFromSave(surface: Surface, drawinfo: tuple[int, int], unclaimed_players: list[Player]) -> tuple[list[Rect], Rect, Rect]:
  hover_player_int, clicked_player_int = drawinfo
  
  title_rect = top_rect_title(surface, "Select Player From Save File")
  
  # region Create player dropdown
  drect: Rect = default_dropdown_rect(surface)
  
  def choice_rect_color_func(i: int) -> tuple[int, int, int]:
    return Colors.LIGHTGREEN if i == clicked_player_int else Colors.GRAY
  
  def choice_outline_color_func(i: int) -> tuple[int, int, int]:
    return Colors.GREEN if i == hover_player_int else None
  
  header_rect, player_rects = dropdown(surface, drect, "  Players  ", unclaimed_players,
                                       Colors.RED, Colors.BLACK, 
                                       choice_rect_color_func, lambda x: Colors.BLACK, 
                                       Colors.BLACK, choice_outline_color_func)
  # endregion
  
  # Draw player info and select player button if player clicked
  load_rect = None
  if clicked_player_int is not None:
    draw_player_info(surface, unclaimed_players[clicked_player_int])
    load_rect = single_button(surface, "SELECT")
  
  # Create an "x" button to back out of menu
  back_button_rect = top_right_corner_x_button(surface)
  
  return player_rects, load_rect, back_button_rect

# non-template
def draw_customSettings(surface: Surface, drawnSettings: dict, clicked_textbox_key: str, longestKey: str) -> tuple[list[Rect], list[Rect], Rect]:
  
  title_rect = top_rect_title(surface, "Set Custom Settings")
  
  numbcols = 2
  numbrows = 10
  # Calculate text field sizing
  window_width, window_height = surface.get_size()
  font_size = min(window_width, window_height) // 30
  font = pygame.font.Font(Fonts.main, font_size)
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
    surface.blit(key_surface, (pos_x, pos_y))
    
    # Draw Text Box and Value
    pos_x = pos_x + key_text_width + window_width//30
    pos_y = pos_y
    text_field_rect = Rect(pos_x, pos_y, val_text_width, text_field_height + window_width//250)
    pygame.draw.rect(surface, Colors.GRAY, text_field_rect, 0)
    text_field_rects.append(text_field_rect)
    
    if clicked_textbox_key == k:
      pygame.draw.rect(surface, Colors.GREEN, text_field_rect, 4)
    
    # Render and blit the text on the text field
    text_surface = font.render(str(v), True, Colors.BLACK)
    surface.blit(text_surface, (pos_x + window_width//150, pos_y))
  
  yesandno_rects = row_buttons(surface, ['Reset to Default', 'Create Players'], row_height_div=6)
  
  # Create an "x" button to back out of menu
  back_button_rect = top_right_corner_x_button(surface)
  
  return text_field_rects, yesandno_rects, back_button_rect

# endregion

# region postgame gui

def draw_endGameStats(surface: Surface, players: list[Player], statlist, hover_stat_int: int, clicked_stat_int: int, viewByField: bool, graphfig: Figure) -> tuple[list[Rect], Rect]:
  
  title_rect = top_rect_title(surface, "End Game Stats")
  
  # region Create stats/player dropdown
  drect: Rect = default_dropdown_rect(surface)
  
  header = "Stats by Field" if viewByField else "Stats by Player"
  choices = statlist if viewByField else [p.name for p in players] 
  
  def choice_rect_color_func(i: int) -> tuple[int, int, int]:
    return Colors.LIGHTGREEN if i == clicked_stat_int else Colors.GRAY
  
  def choice_outline_color_func(i: int) -> tuple[int, int, int]:
    return Colors.GREEN if i == hover_stat_int else None
  
  header_rect, statswap_rects = dropdown(surface, drect, header, choices,
                                       Colors.RED, Colors.BLACK, 
                                       choice_rect_color_func, lambda x: Colors.BLACK, 
                                       Colors.BLACK, choice_outline_color_func)
  # endregion
  
  #Draw graph to the screen
  if clicked_stat_int is not None and graphfig is not None:
    window_width, window_height = surface.get_size()
    scale = min(1.35 * window_width/1600, 1.3 * window_height/900)
    figBytes = BytesIO(scope.transform(graphfig, format='png', scale=scale))
    graph_surface = pygame.image.load(figBytes)
    surface.blit(graph_surface, graph_surface.get_rect(right=window_width, centery=window_height//2))
  
  # Draw button to change viewmode
  label = "View by Field" if viewByField else "View by Player"
  color = Colors.LIGHTGREEN if viewByField else Colors.RED
  viewByField_rect = single_button(surface, label, color, rect_width_div=6, rect_height_div=10, rect_offest_y=8/9)
  
  return (statswap_rects, viewByField_rect)

# endregion
