import pygame
import plotly
from io import BytesIO
from __main__ import HIDE_PERSONAL_INFO, screen
from common import colors, fonts
# plotly.io.kaleido.scope.mathjax = None

def clear_screen():
  screen.fill((255, 255, 255))

def resize_screen(event):
  return pygame.display.set_mode((event.w, event.h), pygame.RESIZABLE)

def draw_fullscreenSelect(drawinfo):
  # Get the current window size and generate title font size
  window_width, window_height = screen.get_size()
  font_size = min(window_width, window_height) // 20
  font = pygame.font.SysFont(fonts.main, font_size)

  # Calculate the size of each popup_select
  button_chunk_width = int(window_width // 3)
  button_chunk_height = int(window_height // 3)

  # Draw the title question
  # Calculate the position of the title question
  pos_x = window_width // 2
  pos_y = window_height // 15
  pos_x, pos_y = int(pos_x), int(pos_y)

  # Decide title text
  if drawinfo == 'hostJoin': label_text = 'Will you Host or Join a Game?'
  elif drawinfo == 'loadSave': label_text = 'Would You Like to Load a Gamestate?'
  elif drawinfo == 'newGameInit': label_text = 'Use Standard Settings?'
  elif drawinfo == 'askToBuy': label_text = 'Would You Like to Buy Stock?'
  elif drawinfo == 'endGameConfirm': label_text = 'Would You Like to End the Game?'
  elif drawinfo == 'makeSave': label_text = 'Would You Like to Save the Current Game?'
  elif drawinfo == 'endGameStats': label_text = 'Would You Like to Show End Game Stats?'
  else: label_text = 'Default Yes/No Question?'

  # Draw the header
  label = font.render(label_text, 1, colors.BLACK)
  label_rect = label.get_rect()
  label_rect.center = (pos_x, pos_y)
  screen.blit(label, label_rect)

  # Decide title text 
  # TODO implement hostJoin comment by actually making the feature
  if drawinfo == 'hostJoin': bianary_choices = ['Yes', 'Yes'] # bianary_choices = ['Host', 'Join']
  elif drawinfo == 'newGameInit': bianary_choices = ['Yes', 'Yes']
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
    pygame.draw.rect(screen, [colors.RED, colors.GREEN][i], button_rect)

    # Draw the stock name
    label = font.render(text, 1, colors.WHITE)
    label_rect = label.get_rect()
    label_rect.center = (pos_x + button_chunk_width // 2, pos_y + button_chunk_height // 2)
    screen.blit(label, label_rect)
  return button_rects

def draw_selectSaveFile(drawinfo, saveinfo):
  hover_directory, hover_save_int, clicked_directory, clicked_save_int = drawinfo
  saves_path, savefiles = saveinfo

  # Get the current window size and generate title font size
  window_width, window_height = screen.get_size()
  font_size = min(window_width, window_height) // 20
  font = pygame.font.SysFont(fonts.main, font_size)
  
  # Calculate the position of the title
  pos_x = window_width // 2
  pos_y = window_height // 60
  pos_x, pos_y = int(pos_x), int(pos_y)
  label_text = "Select Save File"

  # Draw the title
  label = font.render(label_text, 1, colors.BLACK)
  label_rect = label.get_rect()
  label_rect.center = (pos_x, pos_y)
  screen.blit(label, label_rect)

  # Calc directory text
  font_size = min(2*window_width // 3, 2*window_height // 3) // 30
  font = pygame.font.SysFont(fonts.main, font_size)

  # Draw directory box and text
  longeststrlen = max([len(save) for save in savefiles] + [len(saves_path)])
  dd_width = int(font_size * longeststrlen * 10/16)
  dd_height = int(font_size * 4)
  directory_rect = pygame.Rect(window_width // 20, label_rect.bottom + dd_height// 3, dd_width, dd_height)
  pygame.draw.rect(screen, colors.GRAY if not clicked_directory else colors.RED, directory_rect, 0)
  pygame.draw.rect(screen, colors.GREEN if hover_directory else colors.BLACK, directory_rect, 12)
  msg = font.render(saves_path if not HIDE_PERSONAL_INFO else "Saves Directory", 1, colors.BLACK)
  screen.blit(msg, msg.get_rect(center = directory_rect.center))

  savefile_rects = None
  if clicked_directory:
    savefile_rects = []
    for i, savefile in enumerate(savefiles):
      savefile_rect = directory_rect.copy()
      savefile_rect.y += (i+1) * savefile_rect.height
      pygame.draw.rect(screen, colors.GRAY if i != clicked_save_int else colors.LIGHTGREEN, savefile_rect, 0)
      savefile_rects.append(savefile_rect)
      if (not hover_directory and i == hover_save_int):
        pygame.draw.rect(screen, colors.GREEN if (not hover_directory and i == hover_save_int) else colors.BLACK, savefile_rect, 8)
      msg = font.render(savefile if not HIDE_PERSONAL_INFO else f"Save {i}", 1, colors.BLACK)
      screen.blit(msg, msg.get_rect(center = savefile_rect.center))

  load_rect = None
  if clicked_save_int != None:
    # Calc load font
    font_size = min(window_width, window_height) // 20
    font = pygame.font.SysFont(fonts.main, font_size)

    # Draw directory box and text
    load_width = int(font_size * 4)
    load_height = int(font_size * 2)
    load_rect = pygame.Rect(window_width - (window_width//20 + load_width), window_height - (window_height//20 + load_height), load_width, load_height)
    pygame.draw.rect(screen, colors.LIGHTGREEN , load_rect, 0)
    msg = font.render("LOAD", 1, colors.BLACK)
    screen.blit(msg, msg.get_rect(center = load_rect.center))

  return (directory_rect, savefile_rects, load_rect)

def draw_newGameInit(player_names, clicked_textbox_int):
  # Get the current window size and generate title font size
  window_width, window_height = screen.get_size()
  font_size = min(window_width, window_height) // 20
  font = pygame.font.SysFont(fonts.main, font_size)

  # Calculate the position of the title
  pos_x = window_width // 2
  pos_y = window_height // 60
  pos_x, pos_y = int(pos_x), int(pos_y)
  label_text = "Name The Players"

  # Draw the title
  label = font.render(label_text, 1, colors.BLACK)
  label_rect = label.get_rect()
  label_rect.center = (pos_x, pos_y)
  screen.blit(label, label_rect)

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
    pygame.draw.rect(screen, colors.GRAY, text_field_rect, 0)
    text_field_rects.append(text_field_rect)

    if clicked_textbox_int == i:
      pygame.draw.rect(screen, colors.GREEN, text_field_rect, 4)

    # Render and blit the player name text on the text field
    text_surface = font.render(player_names[i], True, colors.BLACK)
    screen.blit(text_surface, (pos_x + 5, pos_y + 5))

  # Calculate the size of each button
  button_chunk_width = int(window_width // 3)
  button_chunk_height = int(window_height // 7)

  yesandno_rects = []
  # Draw the button information
  for i, text in enumerate(['No', 'Yes']):
    # Calculate the position of the buttons' top left corner
    pos_x = (window_width // 12)*(6*i+1)
    pos_y = 5 * window_height // 6
    pos_x, pos_y = int(pos_x), int(pos_y)

    # Create a rectangle for the popup_select and add to popup_select_rects
    button_rect = pygame.Rect(pos_x, pos_y, button_chunk_width, button_chunk_height)
    yesandno_rects.append(button_rect)

    # Draw the popup_select
    pygame.draw.rect(screen, [colors.RED, colors.GREEN][i], button_rect)

    # Draw the stock name
    label = font.render(text, 1, colors.WHITE)
    label_rect = label.get_rect()
    label_rect.center = (pos_x + button_chunk_width // 2, pos_y + button_chunk_height // 2)
    screen.blit(label, label_rect)

  return text_field_rects, yesandno_rects

def draw_endGameStats(players, statlist, hover_stat_int, clicked_stat_int, viewmode, graphfig):
  # Get the current window size and generate title font size
  window_width, window_height = screen.get_size()
  font_size = min(window_width, window_height) // 20
  font = pygame.font.SysFont(fonts.main, font_size)

  # Calculate the position of the title
  pos_x = window_width // 2
  pos_y = window_height // 60
  pos_x, pos_y = int(pos_x), int(pos_y)
  label_text = "End Game Stats"

  # Draw the title
  label = font.render(label_text, 1, colors.BLACK)
  label_rect = label.get_rect()
  label_rect.center = (pos_x, pos_y)
  screen.blit(label, label_rect)

  # Calculate text field sizing
  graphClickables = [p.name for p in players] if viewmode == "USER" else statlist
  longeststrlen = max([len(text) for text in graphClickables])
  font_size = min(2*window_width // 3, 2*window_height // 3) // 30
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
    pygame.draw.rect(screen, colors.GRAY if clicked_stat_int != i else colors.LIGHTGREEN, text_field_rect, 0)
    statswap_rects.append(text_field_rect)
    if i == hover_stat_int:
      pygame.draw.rect(screen, colors.GREEN if i == hover_stat_int else colors.BLACK, text_field_rect, 8)

    # Render and blit the player name text on the text field
    text_surface = font.render(graphClickables[i], True, colors.BLACK)
    screen.blit(text_surface, text_surface.get_rect(center = text_field_rect.center))

  # Calc load font
  font_size = min(window_width, window_height) // 20
  font = pygame.font.SysFont(fonts.main, font_size)

  #Create plotly stat Figures
  if clicked_stat_int != None and graphfig != None:
    figBytes = BytesIO(plotly.io.to_image(graphfig, format='png', scale=min(window_width, window_height) / 600))
    graph_png = pygame.image.load(figBytes)
    screen.blit(graph_png, graph_png.get_rect(center = (2*window_width//3, window_height//2)))

  # Draw viewmode box and text
  load_width = int(font_size * 4)
  load_height = int(font_size * 2)
  viewmode_rect = pygame.Rect(window_width - (window_width//20 + load_width), window_height - (window_height//20 + load_height), load_width, load_height)
  pygame.draw.rect(screen, colors.LIGHTGREEN if viewmode == "STATS" else colors.RED, viewmode_rect, 0)
  msg = font.render(viewmode, 1, colors.BLACK)
  screen.blit(msg, msg.get_rect(center = viewmode_rect.center))
  
  return (statswap_rects, viewmode_rect)
