import pygame
from pygame import Surface, Rect
from pygame.font import Font
import numpy as np

from objects import TileBag, Board, Player, Bank
from common import Colors, Fonts
from gui_fullscreen import create_square_dims, horizontal_refontsizer, vertical_refontsizer, gridifier, dropdown, \
                           single_button, draw_player_info, top_center_title

# region gui components

def tile_size_calc(surface: Surface):
  # Get the current window size
  surface_width, surface_height = surface.get_size()
  
  # Calculate the size of each tile
  tile_width = (surface_width * (5/6) - surface_width//20) // tilebag.cols
  tile_height = (surface_height - surface_height//25) // tilebag.rows
  
  return tile_width, tile_height

# endregion

from gameloop import screen, tilebag, board, bank

def draw_main_screen(board: Board, p: Player, showTiles: bool, prohibitedTiles: list[bool], defunctMode: bool):
  window_width, window_height = screen.get_size()
  
  # region Draw Game Board
  width = window_width * (3/4)
  height = window_height * (19/20)
  top_left = (window_width // 70, window_height//30)
  
  labels = board._tilebag.alltiles
  active_tiles = board.tilesinplay
  cols = board._tilebag.cols
  rows = board._tilebag.rows
  
  rect_color_tup = [(Colors.chain(board.chaindict[label]) if label in board.chaindict else Colors.BLACK) if label in active_tiles else Colors.YELLOW for label in labels]
  def rect_color_func(i):
    return rect_color_tup[i]
  
  def label_color_func(i):
    return Colors.WHITE if rect_color_tup[i] == Colors.BLACK else Colors.BLACK
  
  tile_rects = gridifier(screen, width, height, top_left, labels, cols, rows, rect_color_func, label_color_func, 
                         lambda x: Colors.OUTLINE, outline_width=4, underfill=True, underfill_color=Colors.OUTLINE, 
                         font_name=Fonts.tile)
  # endregion
  
  # region Draw Tiles or Tile Hider
  tile_rects = tilehider_rect = None
  if showTiles:
    width = window_width // 6.2
    height = window_height // 2.9
    top_left = (window_width * (81/100), window_height * (66/100))
    
    labels = p.tiles
    cols, rows = create_square_dims(labels)
    
    def rect_color_func(i):
      return Colors.UNSELECTABLEGRAY if prohibitedTiles[i] else Colors.BLACK
    
    def label_color_func(i):
      return Colors.BLACK if prohibitedTiles[i] else Colors.WHITE
    
    def extra_render_func(surface, i: int, rect: Rect, font_size: int):
      if prohibitedTiles[i]:
        font = pygame.font.SysFont(Fonts.oblivious, int(font_size*4.5))
        label_surface = font.render("x", 1, Colors.RED)
        label_rect = label_surface.get_rect()
        label_rect.center = rect.center
        label_rect.centery = rect.centery - rect.height//20
        surface.blit(label_surface, label_rect)
    
    tile_rects = gridifier(screen, width, height, top_left, labels, cols, rows, rect_color_func, label_color_func, 
                          font_name=Fonts.tile, extra_render_func=extra_render_func)
  else:
    label = f"Tiles Hidden: Defuncting" if defunctMode else f"Click to Reveal {p.name}'s Tiles"
    tilehider_rect = single_button(screen, label, Colors.BLACK, Colors.WHITE, rect_width_div=5.1, rect_offest_x=79/100, rect_offest_y=74/100)
  # endregion
  
  popup_select_labels = ['View Other Player Inventories', 'View Hotel Stocks Remaining']
  popup_select_rects = draw_player_info(screen, p, extra_text=popup_select_labels)[-len(popup_select_labels):]
  
  # # region Draw Popup Select Buttons
  # popup_select_rects = []
  # # finish y-axis sizing
  # popup_select_rects.append(single_button(screen, popup_select_labels[0], Colors.GRAY, Colors.BLACK, 6, 18, 80/100, 22/40))
  # popup_select_rects.append(single_button(screen, popup_select_labels[1], Colors.GRAY, Colors.BLACK, 6, 18, 80/100, 49/80))
  # # endregion
  
  return tilehider_rect, tile_rects, popup_select_rects



def draw_popup(subdraw_tag, drawinfo):
  # Calculate the size of the popup
  window_width, window_height = screen.get_size()
  popup_width = 2*window_width // 3
  popup_height = 2*window_height // 3
  font_size = min(popup_width, popup_height) // 20
  font = pygame.font.SysFont(Fonts.main, font_size)
  
  # Calculate the offset to center the popup
  offset_x = (window_width - popup_width) // 2 - 50
  offset_y = (window_height - popup_height) // 2
  offset_x, offset_y = int(offset_x), int(offset_y)
  
  # Create a surface for the popup
  popup = pygame.Surface((popup_width, popup_height))
  
  # Draw the popup background
  popup.fill(Colors.GRAY)
  
  # Draw info into the popup
  closeable = True
  popupInfo = [popup, popup_width, popup_height, font, font_size]
  if subdraw_tag == 'playerStats':
    subdraw_output = draw_playerStats(popupInfo, drawinfo)
  elif subdraw_tag == 'newChain':
    subdraw_output = draw_newChain(popupInfo, drawinfo)
    closeable = False
  elif subdraw_tag == 'mergeChainPriority':
    if type(drawinfo[0]) == tuple:
      closeable = all(['' not in mergeCart for mergeCart in drawinfo[0]])
    else: 
      closeable = '' not in drawinfo[0]
    subdraw_output = draw_mergeChainPriority(popupInfo, drawinfo)
  elif subdraw_tag == 'defunctPayout':
    subdraw_output = draw_defunctPayout(popupInfo, drawinfo)
  elif subdraw_tag == 'defuncter':
    subdraw_output = draw_defuncter(popupInfo, drawinfo)
  elif subdraw_tag in ('loadSave', 'setPlayerNamesLocal', 'endGameConfirm', 'askToBuy'):
    subdraw_output = draw_yesorno(popupInfo, subdraw_tag)
    closeable = False
  elif subdraw_tag == 'stockBuy':
    subdraw_output = draw_stockbuy(popupInfo, drawinfo)
  
  # Draw the close button on the popup for closeable popups, update offset
  if closeable:
    close_button_rect = pygame.Rect(popup_width - font_size, 0, font_size, font_size)
    pygame.draw.rect(popup, Colors.RED, close_button_rect)
    
    # Create an "x" for the closeable popup button
    font_size = min(popup_width, popup_height) // 25
    font = pygame.font.Font(Fonts.oblivious, font_size)
    label = font.render('x', 1, Colors.WHITE)
    label_rect = label.get_rect()
    label_rect.center = (close_button_rect.x + close_button_rect.width // 2 + 1, close_button_rect.y + close_button_rect.height // 2 - 2)
    popup.blit(label, label_rect)
    
    close_button_rect.x += offset_x
    close_button_rect.y += offset_y
  else: close_button_rect = None
  
  #Commit popup to the screen
  screen.blit(popup, (offset_x, offset_y))
  
  # Update the output recs with the position of the popup
  if type(subdraw_output) == pygame.Rect:
    subdraw_output.x += offset_x; subdraw_output.y += offset_y
  elif type(subdraw_output) == list:
    for rect in subdraw_output:
      if type(rect) == pygame.Rect: rect.x += offset_x; rect.y += offset_y
  elif type(subdraw_output) == tuple:
    for rectList in subdraw_output: 
      for rect in rectList:
        if type(rect) == pygame.Rect: rect.x += offset_x; rect.y += offset_y
  
  return close_button_rect, subdraw_output
  # Calc stock font shrinkage to fit column
  info_font_size = font_size
  col_stand_height = pos_y + (2 + len(v_info)) * font_size * 11/10
  if col_stand_height >= surface_height:
    info_font_size = int(font_size * (1 - (col_stand_height - surface_height)/surface_height) )
  info_font = pygame.font.SysFont(Fonts.main, info_font_size)
  return info_font, info_font_size

def draw_playerStats(popupInfo: tuple[Surface, int, int, Font, int], otherplayers):
  popup, popup_width, popup_height, font, font_size = popupInfo
  pos_y = int(popup_height // 20)
  
  h_headers = [p.name for p in otherplayers]
  header_font, header_font_size = horizontal_refontsizer(popup_width, font_size, h_headers)
  
  v_info = otherplayers[0].stocks.keys()
  info_font, info_font_size = vertical_refontsizer(popup_height, font_size, pos_y, v_info)
  
  # Draw the player information
  for i, player in enumerate(otherplayers):
    # Calculate the position of the player information
    pos_x = (popup_width // (len(otherplayers)+1) )*(i+1)
    
    # Draw the player name
    label = header_font.render(player.name, 1, Colors.BLACK)
    label_rect = label.get_rect()
    label_rect.right = pos_x
    label_rect.top = pos_y
    popup.blit(label, label_rect)
    
    # Draw the player money
    balance = player.balance if 'balance' in player.__dict__.keys() else f'${player.bal}'
    label = header_font.render(balance, 1, Colors.BLACK)
    label_rect = label.get_rect()
    label_rect.right = pos_x
    label_rect.top = pos_y + font_size*1.3
    popup.blit(label, label_rect)
    
    # Draw the player stock holdings
    for i, stock in enumerate(player.stocks):
      label = info_font.render(f'{stock}: {player.stocks[stock]}', 1, Colors.BLACK)
      label_rect = label.get_rect()
      label_rect.right = pos_x
      label_rect.top = pos_y + 2 * font_size*1.3 + i * info_font_size*1.05
      popup.blit(label, label_rect)
  return None

def draw_newChain(popupInfo: tuple[Surface, int, int, Font, int], outlinedChain):
  popup, popup_width, popup_height, font, font_size = popupInfo
  
  title_rect = top_center_title(popup, 'Which Chain Would You Like To Found?', 30, 0)
  
  unopenedchains = [chain for chain in tilebag.chainnames if chain not in board.fetchactivechains()]
  chaingroup1 = [chain for chain in unopenedchains if chain in tilebag.chainTierGrouped['cheap']]
  chaingroup2 = [chain for chain in unopenedchains if chain in tilebag.chainTierGrouped['med']]
  chaingroup3 = [chain for chain in unopenedchains if chain in tilebag.chainTierGrouped['high']]
  unopenedchainsgrouped = [group for group in [chaingroup1, chaingroup2, chaingroup3] if len(group) > 0]
  
  newchain_rects = []
  # Draw the chain information
  for i, chaingroup in enumerate(unopenedchainsgrouped):
    # Calculate the size of each tile_chunk
    pos_y = popup_height // (len(unopenedchainsgrouped)+1) * (i+1)
    pos_y = int(pos_y)
    header_font, header_font_size = horizontal_refontsizer(popup_width, font_size, chaingroup)
    
    longest_chain_name = max([len(chain) for chain in chaingroup])
    chain_color_rect_width = int( (popup_width - popup_width//20) / (len(chaingroup) + 2) + longest_chain_name)
    chain_color_rect_height = int((popup_height // (len(unopenedchainsgrouped)+1)) * np.sqrt(header_font_size)/11)
    # chain_color_rect_height = int(popup_height // 10)
    
    # Calculate the position of the chain group
    for j, chain in enumerate(chaingroup):
      
      # Calculate the position of the chain
      pos_x = int( ((popup_width // (len(chaingroup)+1) )*(j+1)) - chain_color_rect_width//2)
      
      # Create a rectangle for the popup_select and add to popup_select_rects
      newchain_rect = pygame.Rect(pos_x, pos_y, chain_color_rect_width, chain_color_rect_height)
      newchain_rects.append(newchain_rect)
      
      # Draw the popup_select
      pygame.draw.rect(popup, Colors.chain(chain), newchain_rect)
      
      # Draw the stock name
      label = header_font.render(chain, 1, Colors.BLACK)
      label_rect = label.get_rect()
      label_rect.center = (pos_x + chain_color_rect_width // 2, pos_y + chain_color_rect_height // 2)
      popup.blit(label, label_rect)
  return newchain_rects

def draw_mergeChainPriority(popupInfo: tuple[Surface, int, int, Font, int], mergeCart_vec):
  popup, popup_width, popup_height, font, font_size = popupInfo
  mergeCart, chainoptions = mergeCart_vec
  
  if type(mergeCart) == tuple:
    quadMerge_2_2 = True
    mergeCart = mergeCart[0]+mergeCart[1]
    chainoptions = chainoptions[0]+chainoptions[1]
  else:
    quadMerge_2_2 = False
  
  title_rect = top_center_title(popup, 'Set Merger Priorities', 30, 0)
  
  # Calculate the size of each popup_select
  tile_chunk_width = int(popup_width // 5)
  tile_chunk_height = int(popup_height // 10)
  checkX_width = int(popup_width // (16*2))
  checkX_height = int(popup_height // (9*2))
  checkX_width, checkX_height = int(checkX_width), int(checkX_height)
  
  # Draw the mergePrio
  mergecart_rects = []
  mergePrio_width_acum = 0
  for i in range(len(chainoptions)):
    # Calculate the position of mergePrios
    x_spacer = popup_width // 50
    # pos_x = popup_width // 2 - x_spacer - checkX_width * 3
    pos_x = (popup_width - (checkX_width*3 + checkX_width*(len(chainoptions)-1) + x_spacer*(len(chainoptions)-1)))/2 + mergePrio_width_acum + .5*checkX_width*i
    pos_y = 2*(popup_height // 15)
    pos_x, pos_y = int(pos_x), int(pos_y)
    
    # Create a rectangle for a mergePrio square
    mergePrio_width = checkX_width * 3 if i==0 else checkX_width
    mergePrio_yspacer = 0 if i==0 else int(checkX_width*3/2 - checkX_width/2)
    
    mergecart_rect = pygame.Rect(pos_x, pos_y - label.get_height()//2 + mergePrio_yspacer, mergePrio_width, mergePrio_width)
    
    if mergeCart[i] == '': stockcart_color = Colors.WHITE
    else: stockcart_color = Colors.chain(mergeCart[i])
    
    # Draw a stockcart square to screen
    pygame.draw.rect(popup, stockcart_color, mergecart_rect)
    
    mergecart_rects.append(mergecart_rect)
    mergePrio_width_acum += mergePrio_width
  
  mergeChain_rects = []
  # Draw the chain information
  for i, chain in enumerate(chainoptions):
    # pos_x = (popup_width // 15) * (4*i+2)
    pos_x = (popup_width - (tile_chunk_width*len(chainoptions) + (popup_width//15)*(len(chainoptions)-1)))/2 + tile_chunk_width*i + (popup_width//15)*i
    pos_y = (popup_height - tile_chunk_height) // 2
    if quadMerge_2_2:
      pos_x = (popup_width - (tile_chunk_width*2 + popup_width//15))/2 + tile_chunk_width*(i%2) + (popup_width//15)*(i%2)
      pos_y = ((popup_height - tile_chunk_height) // 4) * (i//2 + 2)
    pos_x, pos_y = int(pos_x), int(pos_y)
    
    # Create a rectangle for the popup_select and add to popup_select_rects
    mergeChain_rect = pygame.Rect(pos_x, pos_y, tile_chunk_width, tile_chunk_height)
    mergeChain_rects.append(mergeChain_rect)
    
    # Draw the popup_select
    pygame.draw.rect(popup, Colors.chain(chain), mergeChain_rect)
    
    # Draw the stock name
    label = font.render(chain, 1, Colors.BLACK)
    label_rect = label.get_rect()
    label_rect.center = (pos_x + tile_chunk_width // 2, pos_y + tile_chunk_height // 2)
    popup.blit(label, label_rect)
  
  return (mergeChain_rects, mergecart_rects)

def draw_defunctPayout(popupInfo: tuple[Surface, int, int, Font, int], statementsTup_vec):
  popup, popup_width, popup_height, font, font_size = popupInfo
  statementsTup, iofnStatement = statementsTup_vec
  
  title_rect = top_center_title(popup, f'Defunct Chain Payout ({iofnStatement[0]}/{iofnStatement[1]})', 30, 0)
  
  # Draw the defuncting information
  for i, statement in enumerate(statementsTup):
    # Calculate the position of the player information
    pos_x = popup_width // 2
    pos_y = (popup_height // 8) * (i+1)
    pos_x, pos_y = int(pos_x), int(pos_y)
    
    # Draw the player name
    label = font.render(statement, 1, Colors.BLACK)
    label_rect = label.get_rect()
    label_rect.centerx = pos_x
    label_rect.centery = pos_y
    popup.blit(label, label_rect)
  return None

def draw_defuncter(popupInfo: tuple[Surface, int, int, Font, int], drawinfo):
  popup, popup_width, popup_height, font, font_size = popupInfo
  knob1_x, knob2_x, tradeBanned, defunctingStocks, pDefuncting, defunctChain, bigchain = drawinfo
  keepnumb = int(knob1_x)
  tradenumb = int((defunctingStocks - knob2_x) / 2)
  sellnumb = int(defunctingStocks - (keepnumb + tradenumb))
  
  title_rect = top_center_title(popup, f"{pDefuncting.name}'s {defunctChain} Stock Defunct Allocation", 30, 0)
  
  # Draw create slider, knobs, and colored slider segments
  slider_width = 7*int(popup_width // 8)
  slider_height = int(popup_height // 8)
  slider_x = (popup_width - slider_width)//2
  slider_y = (popup_height - slider_height)//2 - popup_height//6
  knob_width = slider_width // 18
  knob_height = knob_width * 4
  knob1_x = slider_x + knob1_x * (slider_width / defunctingStocks) #convert from stock-scale to pixel sale
  knob2_x = slider_x + knob2_x * (slider_width / defunctingStocks) #convert from stock-scale to pixel sale
  slider_rect = pygame.Rect(slider_x, slider_y, slider_width, slider_height)
  knob1_rect = pygame.Rect(knob1_x - knob_width//2, slider_y - 3*(knob_height//24), knob_width, knob_height)
  knob2_rect = pygame.Rect(knob2_x - knob_width//2, slider_y - (21*knob_height//24 - slider_height), knob_width, knob_height)
  keep_bar_rect = pygame.Rect(slider_x, slider_y, knob1_x - slider_x, slider_height)
  sell_bar_rect = pygame.Rect(knob1_x, slider_y, knob2_x - knob1_x, slider_height)
  trade_bar_rect = pygame.Rect(knob2_x, slider_y, slider_x + slider_width - knob2_x, slider_height)
  
  #Draw bars and knobs to popup
  pygame.draw.rect(popup, Colors.chain(defunctChain), keep_bar_rect)
  pygame.draw.rect(popup, Colors.BLACK, sell_bar_rect)
  pygame.draw.rect(popup, Colors.chain(bigchain), trade_bar_rect)
  pygame.draw.rect(popup, Colors.RED, knob1_rect)
  pygame.draw.rect(popup, Colors.RED if bank.stocks[bigchain] > 0 else Colors.UNSELECTABLEGRAY, knob2_rect)
  
  # Create and Draw tradeBanned Colors.GRAY left-half
  if tradeBanned:
    if bank.stocks[bigchain] > 0:
      tradeBanned_rect = knob2_rect.copy()
      tradeBanned_rect.width = tradeBanned_rect.width//2
      pygame.draw.rect(popup, Colors.UNSELECTABLEGRAY, tradeBanned_rect)
    # Create and Draw overlap square if needed
    if knob1_x == knob2_x:
      pretty_rect = knob1_rect.copy()
      pretty_rect.y = slider_y + slider_height//2
      pretty_rect.height = pretty_rect.height//2
      pygame.draw.rect(popup, Colors.RED, pretty_rect)
  
  # Create and draw numbers for keep, sell, trade
  pos_x = popup_width // 2
  pos_y = 4*popup_height // 5
  pos_x, pos_y = int(pos_x), int(pos_y)
  label = font.render(f"Keep: {keepnumb} Sell: {sellnumb} Trade: {tradenumb}", 1, Colors.BLACK)
  label_rect = label.get_rect()
  label_rect.center = (pos_x, pos_y)
  popup.blit(label, label_rect)
  
  return [knob1_rect, knob2_rect, slider_rect]

def draw_yesorno(popupInfo: tuple[Surface, int, int, Font, int], drawinfo):
  popup, popup_width, popup_height, font, font_size = popupInfo
  
  # Decide title text
  if drawinfo == 'loadSave': label_text = 'Would You Like to Load a Gamestate?'
  elif drawinfo == 'setPlayerNamesLocal': label_text = 'Use Standard Settings?'
  elif drawinfo == 'askToBuy': label_text = 'Would You Like to Buy Stock?'
  elif drawinfo == 'endGameConfirm': label_text = 'Would You Like to End the Game?'
  elif drawinfo == 'endGameStats': label_text = 'Would You Like to Show End Game Stats?'
  else: label_text = 'Default Yes/No Question?'
  
  title_rect = top_center_title(popup, label_text, 30, 0)
  
  # Calculate the size of each popup_select
  button_chunk_width = int(popup_width // 3)
  button_chunk_height = int(popup_height // 3)
  
  button_rects = []
  # Draw the button information
  for i, text in enumerate(['No', 'Yes']):
    # Calculate the position of the buttons' top left corner
    pos_x = (popup_width // 12)*(6*i+1)
    pos_y = popup_height // 3
    pos_x, pos_y = int(pos_x), int(pos_y)
    
    # Create a rectangle for the popup_select and add to popup_select_rects
    button_rect = pygame.Rect(pos_x, pos_y, button_chunk_width, button_chunk_height)
    button_rects.append(button_rect)
    
    # Draw the popup_select
    pygame.draw.rect(popup, [Colors.RED, Colors.GREEN][i], button_rect)
    
    # Draw the stock name
    label = font.render(text, 1, Colors.WHITE)
    label_rect = label.get_rect()
    label_rect.center = (pos_x + button_chunk_width // 2, pos_y + button_chunk_height // 2)
    popup.blit(label, label_rect)
  return button_rects

def draw_stockbuy(popupInfo: tuple[Surface, int, int, Font, int], stock_p_vec: tuple[list[str], Player]):
  stockcart, p = stock_p_vec
  popup, popup_width, popup_height, font, font_size = popupInfo
  chaingroup1 = [chain for chain in board.fetchactivechains() if chain in tilebag.chainTierGrouped["cheap"]]
  chaingroup2 = [chain for chain in board.fetchactivechains() if chain in tilebag.chainTierGrouped["med"]]
  chaingroup3 = [chain for chain in board.fetchactivechains() if chain in tilebag.chainTierGrouped["high"]]
  chainsgrouped = [group for group in [chaingroup1, chaingroup2, chaingroup3] if len(group) > 0]
  
  if len(stockcart) < 3:
    for i in range(3 - len(stockcart)):
      stockcart.append('')
  
  title_rect = top_center_title(popup, 'Which Stock Would You Like To Buy?', 60, 0)
  
  # Draw the stockcart
  # Calculate the position of stockcart
  x_spacer = popup_width // 50
  pos_x = popup_width // 2 + x_spacer
  pos_y = 2*(popup_height // 15)
  pos_x, pos_y = int(pos_x), int(pos_y)
  
  # Draw the stockcart header
  label = font.render('Stock Cart:', 1, Colors.BLACK)
  label_rect = label.get_rect()
  label_rect.center = (pos_x - 2 * x_spacer - label.get_width() // 2, pos_y)
  popup.blit(label, label_rect)
  
  # Calculate the size of each popup_select
  plusmin_width = int(popup_width // (16*2))
  plusmin_height = int(popup_height // (9*2))
  
  # TODO redo this using draw_newChain spacing logic
  # TODO change range(3) to use bank maxBuy setting
  # Draw the stockcart icons
  for i in range(3):
    # Create a rectangle for a stockcart square
    # Calculate the size of each popup_select
    stockcart_rect = pygame.Rect(pos_x + (plusmin_width + plusmin_width // 5) * i, 
    pos_y - label.get_height()//2, plusmin_width, plusmin_height)
    stockcart_color = Colors.WHITE if stockcart[i] == '' else Colors.chain(stockcart[i])
    # Draw a stockcart square to screen
    pygame.draw.rect(popup, stockcart_color, stockcart_rect)
  
  stock_plusmin_rects = []
  # Draw the chain information
  for i, chaingroup in enumerate(chainsgrouped):
    # Calculate the size of each tile_chunk
    pos_y = popup_height // (len(chainsgrouped)+1) * (i+1)
    pos_y = int(pos_y)
    header_font, header_font_size = horizontal_refontsizer(popup_width, font_size, chaingroup)
    
    longest_chain_name = max([len(chain) for chain in chaingroup])
    chain_color_rect_width = int( (popup_width - popup_width//20) / (len(chaingroup) + 2) + longest_chain_name)
    chain_color_rect_height = int((popup_height // (len(chainsgrouped)+1)) * np.sqrt(header_font_size)/11)
    # chain_color_rect_height = int(popup_height // 10)
    
    # Calculate the position of each chain
    for j, chain in enumerate(chaingroup):
      
      # Calculate the position of the chain
      pos_x = int( ((popup_width // (len(chaingroup)+1) )*(j+1)) - chain_color_rect_width//2)
      
      # Create a rectangle for the popup_select and add to popup_select_rects
      buychain_rect = pygame.Rect(pos_x, pos_y, chain_color_rect_width, chain_color_rect_height)
      pygame.draw.rect(popup, Colors.chain(chain), buychain_rect)
      
      # Draw the stock name
      label = header_font.render(chain, 1, Colors.BLACK)
      label_rect = label.get_rect()
      label_rect.center = buychain_rect.center
      popup.blit(label, label_rect)
      
      # Draw the stock's price
      stockprice = bank.stockcost(chain, board.fetchchainsize(chain))
      pricecolor = Colors.BLACK if stockprice <= p.bal else Colors.RED
      label2 = font.render(f'${stockprice}', 1, pricecolor)
      label2_rect = label2.get_rect()
      label2_rect.center = (buychain_rect.centerx, buychain_rect.bottom + popup_height // 30)
      popup.blit(label2, label2_rect)
      
      minusplus_iterlist = [1, 4] if (bank.stocks[chain] and stockprice <= p.bal) else [-1]
      for k in minusplus_iterlist: #minus and plus buttons
        # Create a rectangle for the interactive piece and add to output rects list
        stock_plusmin_rect = pygame.Rect(buychain_rect.left + buychain_rect.w * (k/5) - plusmin_width // 2,
                                         buychain_rect.bottom + buychain_rect.h // 20,
                                         plusmin_width, plusmin_height)
        stock_plusmin_rects.append(stock_plusmin_rect)
        if len(minusplus_iterlist) == 1: stock_plusmin_rects.append(None)
        
        # Draw the rect
        pygame.draw.rect(popup, Colors.BLACK, stock_plusmin_rect)
        
        # Draw the plus/minus label
        label = font.render('-' if k == 1 else '+', 1, Colors.WHITE)
        label_rect = label.get_rect()
        label_rect.center = stock_plusmin_rect.center
        if k == 1:
          label_rect.centery -= label_rect.h // 15
        popup.blit(label, label_rect)
  
  return stock_plusmin_rects
