import pygame
import numpy as np
from __main__ import screen, tilebag, bank, board
from common import colors, fonts

def tile_size_calc():
  # Get the current window size
  window_width, window_height = screen.get_size()

  # Calculate the size of each tile
  tile_width = (window_width * (5/6) - window_width//20) // tilebag.cols
  tile_height = (window_height - window_height//25) // tilebag.rows

  return window_width, window_height, tile_width, tile_height

def draw_grid(active_tiles):
  window_width, window_height, tile_width, tile_height = tile_size_calc()

  # Calculate the offset to center the grid
  offset_x = (window_width - (tile_width * tilebag.cols)) // 25
  offset_y = (window_height - (tile_height * tilebag.rows)) // 2
  offset_x, offset_y = int(offset_x), int(offset_y)

  # Create a list of tile colors and font colors
  
  tile_colors = [(getattr(colors, board.chaindict[label]) if label in board.chaindict else colors.BLACK) if label in active_tiles else colors.YELLOW for label in tilebag.alltiles]
  font_colors = [colors.WHITE if color == colors.BLACK else colors.BLACK for color in tile_colors]

  # Create a font for the tile labels
  font_size = int(min(tile_width, tile_height) // 2)
  font = pygame.font.SysFont(fonts.tile, font_size)

  # Draw the grid
  for i in range(tilebag.cols):
    for j in range(tilebag.rows):
      # Calculate the position of the tile
      pos = (offset_x + i * tile_width + 3, offset_y + j * tile_height + 3)

      # Draw the tile
      pygame.draw.rect(screen, tile_colors[i*tilebag.rows+j], (pos[0], pos[1], tile_width, tile_height))

      # Draw the tile label
      label = font.render(tilebag.alltiles[i*tilebag.rows+j], 1, font_colors[i*tilebag.rows+j])
      label_rect = label.get_rect()
      label_rect.center = (pos[0] + tile_width // 2, pos[1] + tile_height // 2)
      screen.blit(label, label_rect)

      # Draw the outline around the tile and board
      pygame.draw.rect(screen, colors.OUTLINE, (pos[0], pos[1], tile_width, tile_height), 4)
      pygame.draw.rect(screen, colors.OUTLINE, (offset_x, offset_y, tile_width * tilebag.cols + 6, tile_height * tilebag.rows + 6), 4)

def draw_player_info(p):
  window_width, window_height, tile_width, tile_height = tile_size_calc()

  # Get the current window size and generate font
  font_size = min(window_width, window_height) // 20
  font = pygame.font.SysFont(fonts.main, font_size)

  # Calculate the position of the player information
  # Use the right edge of the screen as the x-coordinate
  offset_x = window_width - window_width // 100
  offset_y = window_height // 9 - window_height // 10
  offset_x, offset_y = int(offset_x), int(offset_y)

  # Draw the player name
  label = font.render(p.name, 1, colors.BLACK)
  label_rect = label.get_rect()
  label_rect.right = offset_x
  label_rect.top = offset_y
  screen.blit(label, label_rect)

  # Draw the player money
  label = font.render(f'${p.bal}', 1, colors.BLACK)
  label_rect = label.get_rect()
  label_rect.right = offset_x
  label_rect.top = offset_y + font_size
  screen.blit(label, label_rect)

  # Draw the player stock holdings
  font_size_stock = int((min(window_width, window_height) / 19) * (7 / (len(p.stocks))))
  font_stock = pygame.font.SysFont(fonts.main, font_size_stock)
  for i, stock in enumerate(p.stocks):
    label = font_stock.render(f'{stock}: {p.stocks[stock]}', 1, colors.BLACK)
    label_rect = label.get_rect()
    label_rect.right = offset_x
    label_rect.top = offset_y + 2*font_size + i*font_size_stock
    screen.blit(label, label_rect)

def draw_tiles(p, prohibitedTiles):
  button_labels = p.tiles
  window_width, window_height, tile_width, tile_height = tile_size_calc()

  # Calculate the size of each button
  grid_width = int(np.round(np.sqrt(len(button_labels)), 0))
  rows = len(button_labels)//grid_width + (1 if len(button_labels)%grid_width != 0 else 0) 
  button_width = int(window_width * (1/6) // (grid_width) )
  button_height = int((window_height * (6/16) - window_height/25) // (rows))
  button_width = button_height = min(button_width, button_height)
  w_gap = h_gap = button_width//10

  # Calculate the offset to position the button grid
  # offset_x = window_width * (5/6 + 1/128)
  # offset_y = window_height * (10/16 + 1/128)
  zone_x = tile_width * tilebag.cols + window_width//50
  zone_y = window_height * 10/16
  offset_x = zone_x + (window_width - (zone_x + ((grid_width)*button_width + w_gap*(grid_width-1))))//2
  offset_y = zone_y + (window_height - (zone_y + ((rows)*button_height + h_gap*(rows-1))))//2
  offset_x, offset_y = int(offset_x), int(offset_y)

  # Create a font for the button labels
  font_size = min(button_width, button_height) // 2
  font = pygame.font.SysFont(fonts.tile, font_size)

  # Draw the grid of buttons
  tile_rects = []
  for j in range(rows):
    for i in range(grid_width):
      if i + grid_width*j >= len(button_labels):
        break
      # Calculate the position of the button
      pos = (offset_x + i * button_width + w_gap*i, offset_y + j * button_height + h_gap*j)

      # Create a rectangle for the button and add to tile_rects
      button_rect = pygame.Rect(pos[0], pos[1], button_width, button_height)
      tile_rects.append(button_rect)

      # Draw the button
      tile_color = colors.BLACK if not prohibitedTiles[i + grid_width*j] else colors.UNSELECTABLEGRAY
      pygame.draw.rect(screen, tile_color, button_rect)

      # Draw red X blocker if unplayable
      if prohibitedTiles[i + grid_width*j]:
        Xfont_size = int(min(button_width, button_height)*1.9)
        Xfont = pygame.font.Font(fonts.oblivious, Xfont_size)
        Xlabel = Xfont.render('x', 1, colors.RED)
        Xlabel_rect = Xlabel.get_rect()
        Xlabel_rect.center = (button_rect.centerx + Xfont_size//30, button_rect.centery - Xfont_size//20)
        screen.blit(Xlabel, Xlabel_rect)

      # Draw the button label
      label_color = colors.WHITE if not prohibitedTiles[i + grid_width*j] else colors.BLACK
      label = font.render(button_labels[i + grid_width*j], 1, label_color)
      label_rect = label.get_rect()
      label_rect.center = button_rect.center
      screen.blit(label, label_rect)

  return tile_rects

def draw_popup_selects():
  window_width, window_height, tile_width, tile_height = tile_size_calc()
 
  # Calculate the size of each popup_select
  popup_select_width = int(window_width - (tile_width * tilebag.cols + window_width//30))
  popup_select_height = int(window_height//20)

  zone_x = window_width - window_width // 100 - popup_select_width
  zone_y = window_height * 8/16

  popup_select_labels = ['View Other Player Inventories', 'View Hotel Stocks Remaining']
  popup_select_rects = []
  for i, label in enumerate(popup_select_labels):
    # calc offset per label
    offset_x = zone_x
    offset_y = zone_y + i*popup_select_height + i*window_height//40
    offset_x, offset_y = int(offset_x), int(offset_y)

    # Create a font for the label
    font_size = min(popup_select_width//7, popup_select_height) // 2
    font = pygame.font.SysFont(fonts.main, font_size)

    # Create a rectangle for the popup select
    popup_select_rect = pygame.Rect(offset_x, offset_y, popup_select_width, popup_select_height)
    popup_select_rects.append(popup_select_rect)

    # Draw the popup select
    pygame.draw.rect(screen, colors.GRAY, popup_select_rect)

    # Draw the popup select label
    label = font.render(label, 1, colors.BLACK)
    label_rect = label.get_rect()
    label_rect.center = (offset_x + popup_select_width // 2, offset_y + popup_select_height // 2)
    screen.blit(label, label_rect)

  return popup_select_rects

def draw_popup(subdraw_tag, drawinfo):
  # Calculate the size of the popup
  window_width, window_height, tile_width, tile_height = tile_size_calc()
  popup_width = 2*window_width // 3
  popup_height = 2*window_height // 3
  font_size = min(popup_width, popup_height) // 20
  font = pygame.font.SysFont(fonts.main, font_size)

  # Calculate the offset to center the popup
  offset_x = (window_width - popup_width) // 2 - 50
  offset_y = (window_height - popup_height) // 2
  offset_x, offset_y = int(offset_x), int(offset_y)

  # Create a surface for the popup
  popup = pygame.Surface((popup_width, popup_height))

  # Draw the popup background
  popup.fill(colors.GRAY)

  # Draw info into the popup
  popupInfo = [popup, popup_width, popup_height, font, font_size]
  if subdraw_tag == 'playerStats':
    subdraw_output = draw_playerStats(popupInfo, drawinfo)
    closeable = True
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
    closeable = True
  elif subdraw_tag == 'defuncter':
    subdraw_output = draw_defuncter(popupInfo, drawinfo)
    closeable = True
  elif subdraw_tag in ('loadSave', 'newGameInit', 'endGameConfirm', 'askToBuy'):
    subdraw_output = draw_yesorno(popupInfo, subdraw_tag)
    closeable = False
  elif subdraw_tag == 'stockBuy':
    subdraw_output = draw_stockbuy(popupInfo, drawinfo)
    closeable = True
  
  # Draw the close button on the popup for closeable popups, update offset
  if closeable:
    close_button_rect = pygame.Rect(popup_width - font_size, 0, font_size, font_size)
    pygame.draw.rect(popup, colors.RED, close_button_rect)

    # Create an "x" for the closeable popup button
    font_size = min(popup_width, popup_height) // 25
    font = pygame.font.Font(fonts.oblivious, font_size)
    label = font.render('x', 1, colors.WHITE)
    label_rect = label.get_rect()
    # label_rect.center = (close_button_rect.x + 9*close_button_rect.width // 16, close_button_rect.y + 6*close_button_rect.height // 16 )
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

def horizontal_refontsizer(surface_width, surface_height, font_size, pos_y, h_headers, spacer_allocated = 250):
  # Calc column widths per player number and name length
  header_font_size = font_size
  longestheader = max([len(h) for h in h_headers])
  if longestheader * font_size * len(h_headers) + spacer_allocated > surface_width:
    header_font_size = int(1.7 * (surface_width - spacer_allocated) / (longestheader * len(h_headers)))
  header_font = pygame.font.SysFont(fonts.main, header_font_size)
  return header_font, header_font_size

def vertical_refontsizer(surface_width, surface_height, font_size, pos_y, v_info, spacer_allocated = 250):
  # Calc stock font shrinkage to fit column
  info_font_size = font_size
  col_stand_height = pos_y + (2 + len(v_info)) * font_size * 11/10
  if col_stand_height >= surface_height:
    info_font_size = int(font_size * (1 - (col_stand_height - surface_height)/surface_height) )
  info_font = pygame.font.SysFont(fonts.main, info_font_size)
  return info_font, info_font_size

def draw_playerStats(popupInfo, otherplayers):
  popup, popup_width, popup_height, font, font_size = popupInfo
  pos_y = int(popup_height // 20)

  h_headers = [p.name for p in otherplayers]
  header_font, header_font_size = horizontal_refontsizer(popup_width, popup_height, font_size, pos_y, h_headers)

  v_info = otherplayers[0].stocks.keys()
  info_font, info_font_size = vertical_refontsizer(popup_width, popup_height, font_size, pos_y, v_info)

  # Draw the player information
  for i, player in enumerate(otherplayers):
    # Calculate the position of the player information
    pos_x = (popup_width // (len(otherplayers)+1) )*(i+1)

    # Draw the player name
    label = header_font.render(player.name, 1, colors.BLACK)
    label_rect = label.get_rect()
    label_rect.right = pos_x
    label_rect.top = pos_y
    popup.blit(label, label_rect)

    # Draw the player money
    balance = player.balance if 'balance' in player.__dict__.keys() else f'${player.bal}'
    label = header_font.render(balance, 1, colors.BLACK)
    label_rect = label.get_rect()
    label_rect.right = pos_x
    label_rect.top = pos_y + font_size*1.3
    popup.blit(label, label_rect)

    # Draw the player stock holdings
    for i, stock in enumerate(player.stocks):
      label = info_font.render(f'{stock}: {player.stocks[stock]}', 1, colors.BLACK)
      label_rect = label.get_rect()
      label_rect.right = pos_x
      label_rect.top = pos_y + 2 * font_size*1.3 + i * info_font_size*1.05
      popup.blit(label, label_rect)
  return None

def draw_tilehider(player, showTiles):
  window_width, window_height, tile_width, tile_height = tile_size_calc()
 
  # Calculate the size of each tilehider
  tilehider_width = int(window_width - (tile_width * tilebag.cols + window_width//30))
  tilehider_height = int(window_height//20)

  # calc offset
  offset_x = window_width - window_width // 100 - tilehider_width
  offset_y = window_height * 12.5/16
  offset_x, offset_y = int(offset_x), int(offset_y)

  # Create a font for the label
  font_size = min(tilehider_width//7, tilehider_height) // 2
  font = pygame.font.SysFont(fonts.main, font_size)

  # Create a rectangle for the tilehider
  tilehider_rect = pygame.Rect(offset_x, offset_y, tilehider_width, tilehider_height)

  # Draw the tilehider
  pygame.draw.rect(screen, colors.BLACK, tilehider_rect)

  # Draw the popup_select label
  if not showTiles:
    label = font.render(f"Click to Reveal {player.name}'s Tiles", 1, colors.WHITE)
  else:
    label = font.render(f"Tiles Hidden: Defuncting", 1, colors.WHITE)
  label_rect = label.get_rect()
  label_rect.center = (offset_x + tilehider_width // 2, offset_y + tilehider_height // 2)
  screen.blit(label, label_rect)

  return tilehider_rect

def draw_newChain(popupInfo, outlinedChain):
  popup, popup_width, popup_height, font, font_size = popupInfo

  unopenedchains = [chain for chain in tilebag.chainnames if chain not in board.fetchactivechains()]
  chaingroup1 = [chain for chain in unopenedchains if chain in tilebag.chainTierGrouped['cheap']]
  chaingroup2 = [chain for chain in unopenedchains if chain in tilebag.chainTierGrouped['med']]
  chaingroup3 = [chain for chain in unopenedchains if chain in tilebag.chainTierGrouped['high']]
  unopenedchainsgrouped = [group for group in [chaingroup1, chaingroup2, chaingroup3] if len(group) > 0]

  # Draw the title question
  # Calculate the position of the title question
  pos_x = popup_width // 2
  pos_y = popup_height // 15
  pos_x, pos_y = int(pos_x), int(pos_y)

  # Draw the popup header
  label = font.render('Which Chain Would You Like To Found?', 1, colors.BLACK)
  label_rect = label.get_rect()
  label_rect.center = (pos_x, pos_y)
  popup.blit(label, label_rect)

  spacer_allocated = 250

  newchain_rects = []
  # Draw the chain information
  for i, chaingroup in enumerate(unopenedchainsgrouped):
    # Calculate the size of each tile_chunk
    pos_y = popup_height // (len(unopenedchainsgrouped)+1) * (i+1)
    pos_y = int(pos_y)
    header_font, header_font_size = horizontal_refontsizer(popup_width, popup_height, font_size, pos_y, chaingroup, spacer_allocated)
  
    longest_chain_name = max([len(chain) for chain in chaingroup])
    chain_color_rect_width = int( (popup_width - popup_width//20) / (len(chaingroup) + 2) + longest_chain_name)
    # chain_color_rect_width = int(2 * (popup_width - popup_width//20)/(longest_chain_name * len(chaingroup)**.5) )
    # chain_color_rect_width = int(875 * popup_width/(longest_chain_name * (len(chaingroup)**1.85) * (header_font_size**1.05)))
    # chain_color_rect_width = int((23*popup_width//30)//longest_chain_name)
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
      pygame.draw.rect(popup, getattr(colors, chain), newchain_rect)

      # Draw the stock name
      label = header_font.render(chain, 1, colors.BLACK)
      label_rect = label.get_rect()
      label_rect.center = (pos_x + chain_color_rect_width // 2, pos_y + chain_color_rect_height // 2)
      popup.blit(label, label_rect)
  return newchain_rects

def draw_mergeChainPriority(popupInfo, mergeCart_vec):
  popup, popup_width, popup_height, font, font_size = popupInfo
  mergeCart, chainoptions = mergeCart_vec
  if type(mergeCart) == tuple:
    quadMerge_2_2 = True
    mergeCart = mergeCart[0]+mergeCart[1]
    chainoptions = chainoptions[0]+chainoptions[1]
    # input()
  else:
    quadMerge_2_2 = False

  # Calculate the size of each popup_select
  tile_chunk_width = int(popup_width // 5)
  tile_chunk_height = int(popup_height // 10)

  # Draw the title question
  # Calculate the position of the title question
  pos_x = popup_width // 2
  pos_y = popup_height // 15
  checkX_width = int(popup_width // (16*2))
  checkX_height = int(popup_height // (9*2))
  pos_x, pos_y = int(pos_x), int(pos_y)
  checkX_width, checkX_height = int(checkX_width), int(checkX_height)

  # Draw the popup header
  label = font.render('Set Merger Priorities', 1, colors.BLACK)
  label_rect = label.get_rect()
  label_rect.center = (pos_x, pos_y)
  popup.blit(label, label_rect)

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

    if mergeCart[i] == '': stockcart_color = colors.WHITE
    else: stockcart_color = getattr(colors, mergeCart[i])

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
    pygame.draw.rect(popup, getattr(colors, chain), mergeChain_rect)

    # Draw the stock name
    label = font.render(chain, 1, colors.BLACK)
    label_rect = label.get_rect()
    label_rect.center = (pos_x + tile_chunk_width // 2, pos_y + tile_chunk_height // 2)
    popup.blit(label, label_rect)


  return (mergeChain_rects, mergecart_rects)

def draw_defunctPayout(popupInfo, statementsTup_vec):
  popup, popup_width, popup_height, font, font_size = popupInfo
  statementsTup, iofnStatement = statementsTup_vec

  # Draw the (i/n) notif statement
  pos_x = popup_width // 2
  pos_y = popup_height // 15
  pos_x, pos_y = int(pos_x), int(pos_y)
  label = font.render(f'Defunct Chain Payout ({iofnStatement[0]}/{iofnStatement[1]})', 1, colors.BLACK)
  label_rect = label.get_rect()
  label_rect.center = (pos_x, pos_y)
  popup.blit(label, label_rect)

  # Draw the defuncting information
  for i, statement in enumerate(statementsTup):
    # Calculate the position of the player information
    pos_x = popup_width // 2
    pos_y = (popup_height // 8) * (i+1)
    pos_x, pos_y = int(pos_x), int(pos_y)

    # Draw the player name
    label = font.render(statement, 1, colors.BLACK)
    label_rect = label.get_rect()
    label_rect.centerx = pos_x
    label_rect.centery = pos_y
    popup.blit(label, label_rect)
  return None

def draw_defuncter(popupInfo, drawinfo):
  popup, popup_width, popup_height, font, font_size = popupInfo
  knob1_x, knob2_x, tradeBanned, defunctingStocks, pDefuncting, defunctChain, bigchain = drawinfo
  keepnumb = int(knob1_x)
  tradenumb = int((defunctingStocks - knob2_x) / 2)
  sellnumb = int(defunctingStocks - (keepnumb + tradenumb))
  
  # Draw title
  pos_x = popup_width // 2
  pos_y = popup_height // 15
  pos_x, pos_y = int(pos_x), int(pos_y)
  label = font.render(f"{pDefuncting.name}'s {defunctChain} Stock Defunct Allocation", 1, colors.BLACK)
  label_rect = label.get_rect()
  label_rect.center = (pos_x, pos_y)
  popup.blit(label, label_rect)

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
  pygame.draw.rect(popup, getattr(colors, defunctChain), keep_bar_rect)
  pygame.draw.rect(popup, colors.BLACK, sell_bar_rect)
  pygame.draw.rect(popup, getattr(colors, bigchain), trade_bar_rect)
  pygame.draw.rect(popup, colors.RED, knob1_rect)
  pygame.draw.rect(popup, colors.RED if bank.stocks[bigchain] > 0 else colors.UNSELECTABLEGRAY, knob2_rect)

  # Create and Draw tradeBanned colors.GRAY left-half
  if tradeBanned:
    if bank.stocks[bigchain] > 0:
      tradeBanned_rect = knob2_rect.copy()
      tradeBanned_rect.width = tradeBanned_rect.width//2
      pygame.draw.rect(popup, colors.UNSELECTABLEGRAY, tradeBanned_rect)
    # Create and Draw overlap square if needed
    if knob1_x == knob2_x:
      pretty_rect = knob1_rect.copy()
      pretty_rect.y = slider_y + slider_height//2
      pretty_rect.height = pretty_rect.height//2
      pygame.draw.rect(popup, colors.RED, pretty_rect)

  # Create and draw numbers for keep, sell, trade
  pos_x = popup_width // 2
  pos_y = 4*popup_height // 5
  pos_x, pos_y = int(pos_x), int(pos_y)
  label = font.render(f"Keep: {keepnumb} Sell: {sellnumb} Trade: {tradenumb}", 1, colors.BLACK)
  label_rect = label.get_rect()
  label_rect.center = (pos_x, pos_y)
  popup.blit(label, label_rect)

  return [knob1_rect, knob2_rect, slider_rect]

def draw_yesorno(popupInfo, drawinfo):
  popup, popup_width, popup_height, font, font_size = popupInfo
  font_size = min(popup_width, popup_height) * 3

  # Calculate the size of each popup_select
  button_chunk_width = int(popup_width // 3)
  button_chunk_height = int(popup_height // 3)

  # Draw the title question
  # Calculate the position of the title question
  pos_x = popup_width // 2
  pos_y = popup_height // 15
  pos_x, pos_y = int(pos_x), int(pos_y)

  # Decide title text
  if drawinfo == 'loadSave': label_text = 'Would You Like to Load a Gamestate?'
  elif drawinfo == 'newGameInit': label_text = 'Use Standard Settings?'
  elif drawinfo == 'askToBuy': label_text = 'Would You Like to Buy Stock?'
  elif drawinfo == 'endGameConfirm': label_text = 'Would You Like to End the Game?'
  elif drawinfo == 'endGameStats': label_text = 'Would You Like to Show End Game Stats?'
  else: label_text = 'Default Yes/No Question?'

  # Draw the popup header
  label = font.render(label_text, 1, colors.BLACK)
  label_rect = label.get_rect()
  label_rect.center = (pos_x, pos_y)
  popup.blit(label, label_rect)

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
    pygame.draw.rect(popup, [colors.RED, colors.GREEN][i], button_rect)

    # Draw the stock name
    label = font.render(text, 1, colors.WHITE)
    label_rect = label.get_rect()
    label_rect.center = (pos_x + button_chunk_width // 2, pos_y + button_chunk_height // 2)
    popup.blit(label, label_rect)
  return button_rects

def draw_stockbuy(popupInfo, stock_p_vec):
  stockcart, p = stock_p_vec
  popup, popup_width, popup_height, font, font_size = popupInfo
  buyablechains = [chain for chain in board.fetchactivechains() if bank.stocks[chain] or chain in stockcart]
  chaingroup1 = [chain for chain in buyablechains if chain in tilebag.chainTierGrouped["cheap"]]
  chaingroup2 = [chain for chain in buyablechains if chain in tilebag.chainTierGrouped["med"]]
  chaingroup3 = [chain for chain in buyablechains if chain in tilebag.chainTierGrouped["high"]]
  buyablechainsgrouped = [chaingroup1, chaingroup2, chaingroup3]

  if len(stockcart) < 3:
    for i in range(3 - len(stockcart)):
      stockcart.append('')

  # Calculate the size of each popup_select
  tile_chunk_width = int(popup_width // 5)
  tile_chunk_height = int(popup_height // 10)
  plusmin_width = int(popup_width // (16*2))
  plusmin_height = int(popup_height // (9*2))

  # Draw the title question
  # Calculate the position of the title question
  pos_x = popup_width // 2
  pos_y = popup_height // 15
  pos_x, pos_y = int(pos_x), int(pos_y)

  # Draw the popup header
  label = font.render('Which Stock Would You Like To Buy?', 1, colors.BLACK)
  label_rect = label.get_rect()
  label_rect.center = (pos_x, pos_y)
  popup.blit(label, label_rect)

  # Draw the stockcart
  # Calculate the position of stockcart
  x_spacer = popup_width // 50
  pos_x = popup_width // 2 + x_spacer
  pos_y = 2*(popup_height // 15)
  pos_x, pos_y = int(pos_x), int(pos_y)
  

  # Draw the stockcart header
  label = font.render('Stock Cart:', 1, colors.BLACK)
  label_rect = label.get_rect()
  label_rect.center = (pos_x - 2 * x_spacer - label.get_width() // 2, pos_y)
  popup.blit(label, label_rect)

  # Draw the stockcart icons
  for i in range(3):
    # Create a rectangle for a stockcart square
    stockcart_rect = pygame.Rect(pos_x + (plusmin_width + plusmin_width // 5) * i, pos_y - label.get_height()//2, plusmin_width, plusmin_height)

    if stockcart[i] == '': stockcart_color = colors.WHITE
    else: stockcart_color = getattr(colors, stockcart[i])

    # Draw a stockcart square to screen
    pygame.draw.rect(popup, stockcart_color, stockcart_rect)

  stock_plusmin_rects = []
  # Draw the chain information
  for i, chaingroup in enumerate(buyablechainsgrouped):
    # Calculate the position of the chain group
    for j, chain in enumerate(chaingroup):
      pos_x = (popup_width // 15) * (4*j+2) if len(chaingroup) == 3 else popup_width // 5 * (2*j+1)
      pos_y = popup_height // 4 * (i+1)
      pos_x, pos_y = int(pos_x), int(pos_y)

      # Create a rectangle for the chain name
      newchain_rect = pygame.Rect(pos_x, pos_y, tile_chunk_width, tile_chunk_height)

      # Draw the popup_select
      pygame.draw.rect(popup, getattr(colors, chain), newchain_rect)

      # Draw the stock name
      label = font.render(chain, 1, colors.BLACK)
      label_rect = label.get_rect()
      label_rect.center = (pos_x + tile_chunk_width // 2, pos_y + tile_chunk_height // 2)
      popup.blit(label, label_rect)

      # Draw the stock's price
      stockprice = bank.stockcost(chain, board.fetchchainsize(chain))
      pricecolor = colors.BLACK if stockprice < p.bal else colors.RED
      label2 = font.render(f'${stockprice}', 1, pricecolor)
      label2_rect = label2.get_rect()
      label2_rect.center = (pos_x + tile_chunk_width // 2, pos_y - tile_chunk_height // 2 + popup_height // 50)
      popup.blit(label2, label2_rect)

      minusplus_iterlist = [-1, 1] if (bank.stocks[chain] and stockprice < p.bal) else [-1]
      for k in minusplus_iterlist: #minus and plus buttons
        offset_x = tile_chunk_width // 2 - plusmin_width // 2  + (popup_width // 25) * k
        offset_y = tile_chunk_height + popup_height // 60
        offset_x, offset_y = int(offset_x), int(offset_y)

        # Create a rectangle for the interactive piece and add to output rects list
        stock_plusmin_rect = pygame.Rect(pos_x + offset_x, pos_y + offset_y, plusmin_width, plusmin_height)
        stock_plusmin_rects.append(stock_plusmin_rect)
        if len(minusplus_iterlist) == 1: stock_plusmin_rects.append(None)

        # Draw the rect
        pygame.draw.rect(popup, colors.BLACK, stock_plusmin_rect)

        # Draw the plus/minus label
        label = font.render('-' if k == -1 else '+', 1, colors.WHITE)
        label_rect = label.get_rect()
        label_rect.center = (pos_x + offset_x + plusmin_width // 2, pos_y + offset_y + plusmin_height // 2)
        popup.blit(label, label_rect)

  return stock_plusmin_rects

def draw_slider(popupInfo, slider_vec):
  popup, popup_width, popup_height, font, font_size = popupInfo
  slider_pos, dragging, slider_value, p_stocks = slider_vec

  # Get the current mouse position and state
  mouse_pos = pygame.mouse.get_pos()
  mouse_pressed = pygame.mouse.get_pressed()

  # Calculate the x and y coordinates of the center of the slider
  x = popup_width // 2
  y = popup_height // 2

  # Calculate the length and height of the slider
  length = 4 * popup_width // 5
  height = popup_height // 80
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
  pygame.draw.rect(popup, (0, 0, 0), slider_rect)

  # Draw the slider handle
  bar_rect = pygame.Rect(x1 + slider_pos, y1, 10, height)
  pygame.draw.rect(popup, (0, 0, 0), bar_rect)

  # Display the current value of the slider
  text = font.render(str(slider_value), True, (0, 0, 0))
  popup.blit(text, (x - text.get_width() // 2, y - text.get_height() // 2))
  
  return [slider_rect, bar_rect]
