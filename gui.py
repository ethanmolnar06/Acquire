import pygame
from pygame import Surface, Rect
from pygame.font import Font

from objects import Board, Player, Bank
from common import Colors, Fonts, iter_flatten
from gui_fullscreen import create_square_dims, dynamic_font, blit_font_to_rect, gridifier, dropdown, single_button, draw_player_info, top_rect_title

# region gui components

class GUI_area:
  def __init__(self, levelEditor: bool = False):
    self.game_board = True
    self.other_player_stats = False
    self.newchain = None
    self.mergeChainPriority = None
    self.defuncter = None
    self.stockbuy = None
    self.random_tiles = None if not levelEditor else False
  
  # Don't want the dropdown overwritten when iterating through self.__dict__
  def dropdown_text(self):
    return {
      "game_board": "View Game Board",
      "other_player_stats": "View Player Assets",
      "newchain": "Select New Chain",
      "mergeChainPriority": "Select Merge Order",
      "defuncter": "Handle Defunct Stock",
      "stockbuy": "Purchase Stock",
      "random_tiles": "Give Random Tiles",
    }
  
  def dropdown(self) -> list[str]:
    dropdown = []
    for k, v in self.__dict__.items():
      if v == False:
        dropdown.append(self.dropdown_text()[k])
    if len(dropdown) < 2:
      dropdown += [""]*(2 - len(dropdown))
    return dropdown
  
  def clear(self, show: str | None = None) -> None:
    for k in self.__dict__.keys():
      setattr(self, k, None)
    self.other_player_stats = False
    if show is not None:
      self.game_board = False
      setattr(self, show, True)
    else:
      self.game_board = True
  
  def change_showing(self, i) -> None:
    labels = [k for k in self.__dict__.keys()]
    options = [v for v in self.__dict__.values()]
    if i == 1:
      labels = labels[::-1]
      options = options[::-1]
    toHide = labels[options.index(True)] # only one True at a time
    toShow = labels[options.index(False)] # 1 or 2, correct one chosen via i -> flip
    setattr(self, toHide, False)
    setattr(self, toShow, True)

def get_focus_area(surface: Surface) -> Rect:
  # Get the current window size
  surface_rect = surface.get_rect()
  
  width = surface_rect.w * (9/12)
  height = surface_rect.h * (19/20)
  
  focus_area = Rect(0, 0, width, height)
  focus_area.centery = surface.get_rect().centery
  focus_area.centerx += surface_rect.w // 60
  
  return focus_area

# endregion

def draw_main_screen(surface: Surface, p: Player, showTiles: bool, prohibitedTiles: list[bool] | None, defunctMode: bool, highlight_player_name: bool, focus_content: GUI_area) -> tuple[list[Rect] | None, list[Rect] | None, list[Rect],]:
  window_width, window_height = surface.get_size()
  
  # region Draw Tiles or Tile Hider
  tile_rects = tilehider_rect = None
  if showTiles and p.tiles:
    subrect = Rect(int(window_width * (81/100)), int(window_height * (66/100)),
                  window_width // 6.2, window_height // 2.9)
    
    cols, rows = create_square_dims(p.tiles)
    
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
    
    tile_rects = gridifier(surface, subrect, p.tiles, cols, rows, rect_color_func, label_color_func, 
                          font_name=Fonts.tile, extra_render_func=extra_render_func)
  elif not showTiles:
    label = f"Tiles Hidden: Defuncting" if defunctMode else f"Click to Reveal {p.name}'s Tiles"
    tilehider_rect = single_button(surface, label, Colors.BLACK, Colors.WHITE, rect_width_div=5.1, rect_offest_x=9, rect_offest_y=1.2)
  # endregion
  
  popup_select_labels = focus_content.dropdown()
  header_rect, choice_rects = draw_player_info(surface, p, extra_text=popup_select_labels, highlight_player_name=highlight_player_name)
  player_stat_rects = [header_rect,] + choice_rects[:-len(popup_select_labels)]
  popup_select_rects = choice_rects[-len(popup_select_labels):]
  
  return tilehider_rect, tile_rects, player_stat_rects, popup_select_rects

def draw_game_board(surface: Surface, board: Board) -> list[Rect]:
  focus_area = get_focus_area(surface)
  
  labels = board._tilebag.alltiles
  active_tiles = board.tilesinplay
  cols = board._tilebag.cols
  rows = board._tilebag.rows
  
  rect_color_tup = [(Colors.chain(board.chaindict[label]) if label in board.chaindict else Colors.BLACK) if label in active_tiles else Colors.YELLOW for label in labels]
  def rect_color_func(i):
    return rect_color_tup[i]
  
  def label_color_func(i):
    return Colors.WHITE if rect_color_tup[i] == Colors.BLACK else Colors.BLACK
  
  board_rects = gridifier(surface, focus_area, labels, cols, rows, rect_color_func, label_color_func, 
                        lambda x: Colors.OUTLINE, outline_width=4, underfill=True, underfill_color=Colors.OUTLINE, 
                        font_name=Fonts.tile, share_font_size=True, default_font_size=45)
  
  return board_rects

def draw_other_player_stats(surface: Surface, bank: Bank, otherplayers: list[Player]) -> None:
  focus_area = get_focus_area(surface)
  pygame.draw.rect(surface, Colors.GRAY, focus_area)
  
  otherplayers = [bank] + otherplayers
  div = focus_area.w // len(otherplayers)
  focus_area.w = div
  focus_area.left += (div//len(otherplayers)//4)
  
  # player_rects = []
  for i, p in enumerate(otherplayers):
    header_rect, player_rect = draw_player_info(surface, p, subrect=focus_area, label_justification="left", choice_justification="left")
    # player_rects.append(player_rect)
    focus_area.left += div
  
  return None

def draw_newChain_fullscreen(surface: Surface, board: Board) -> list[Rect]:
  unopenedchainsgrouped = board.fetchchainsgrouped(invert_subset=True)
  
  focus_area = get_focus_area(surface)
  pygame.draw.rect(surface, Colors.GRAY, focus_area)
  title_rect = top_rect_title(surface, 'Which Chain Would You Like To Found?', surface_subrect=focus_area)
  
  def rect_color_func(i):
    return Colors.chain(iter_flatten(unopenedchainsgrouped)[i])
  
  def label_color_func(i):
    return Colors.BLACK
  
  bottom_anchor = focus_area.bottom
  focus_area.scale_by_ip(1, .9)
  focus_area.bottom = bottom_anchor
  newchain_rects = gridifier(surface, focus_area, unopenedchainsgrouped, None, None,
                          rect_color_func, label_color_func, allignment="center", share_font_size=True)
  
  return newchain_rects

def draw_mergeChainPriority_fullscreen(surface: Surface, board: Board, 
                                       mergeCart: list[str] | tuple[list[str], list[str]], chainoptions: list[str] | tuple[list[str], list[str]]) -> Rect:
  focus_area = get_focus_area(surface)
  pygame.draw.rect(surface, Colors.GRAY, focus_area)
  title_rect = top_rect_title(surface, 'Set Merger Priorities', surface_subrect=focus_area)
  
  # region Draw mergeCart
  if isinstance(mergeCart, tuple):
    quadMerge_2_2 = True
    mergeCart = mergeCart[0] + mergeCart[1]
    chainoptions = chainoptions[0] + chainoptions[1]
  else:
    quadMerge_2_2 = False
  
  bottom_anchor = focus_area.bottom
  focus_area.scale_by_ip(1, .94)
  focus_area.bottom = bottom_anchor
  
  mergecart_label = 'Merge Order: '
  mergecart_title_subrect = title_rect.copy()
  mergecart_title_subrect.top = title_rect.bottom
  mergecart_title_subrect.right = focus_area.centerx
  font, font_size = dynamic_font(mergecart_title_subrect, mergecart_label, Fonts.main)
  mergecart_title_rect = blit_font_to_rect(surface, font, mergecart_title_subrect, mergecart_label, Colors.BLACK, justification="right",
                                 vert_justification="top", font_offset_div=50)
  
  subrect = focus_area.copy().scale_by(1/8, 1/12)
  subrect.centery = mergecart_title_rect.centery
  subrect.left = focus_area.centerx
  
  def rect_color_func(i):
    if not mergeCart[i]:
      return Colors.WHITE
    return Colors.chain(mergeCart[i])
  
  mergecart_rects = gridifier(surface, subrect, ["None",]*len(mergeCart), len(mergeCart), 1, rect_color_func, None)
  
  # endregion
  
  # region Draw Chain Labels
  def rect_color_func(i):
    return Colors.chain(chainoptions[i])
  
  chain_subrect = focus_area.copy()
  chain_subrect.top = (title_rect.bottom + mergecart_title_rect.bottom)//2
  chain_subrect.height = confirm_rect.top - mergecart_title_rect.bottom
  # pygame.draw.rect(surface, Colors.GREEN, chain_subrect)
  chain_rects = gridifier(surface, chain_subrect, chainoptions, len(chainoptions), 1, rect_color_func, lambda x: Colors.BLACK, 
                          allignment="center", share_font_size=True)
  
  # endregions
  
  confirm_rect = single_button(surface, "CONFIRM", surface_subrect=focus_area, rect_height_div=10, rect_offest_x=8, rect_offest_y=6)
  
  return chain_rects, mergecart_rects

def draw_stockbuy_fullscreen(surface: Surface, board: Board, bank: Bank, p: Player, stockcart: list[str]) -> list[Rect]:
  focus_area = get_focus_area(surface)
  pygame.draw.rect(surface, Colors.GRAY, focus_area)
  title_rect = top_rect_title(surface, 'Which Stock Would You Like To Buy?', surface_subrect=focus_area)
  
  # region Draw stockcart
  if len(stockcart) < 3:
    for i in range(3 - len(stockcart)):
      stockcart.append('')
  
  bottom_anchor = focus_area.bottom
  focus_area.scale_by_ip(1, .94)
  focus_area.bottom = bottom_anchor
  
  stockcart_label = 'Stock Cart: '
  stockcart_title_subrect = title_rect.copy()
  stockcart_title_subrect.top = title_rect.bottom
  stockcart_title_subrect.right = focus_area.centerx
  font, font_size = dynamic_font(stockcart_title_subrect, stockcart_label, Fonts.main)
  stockcart_title_rect = blit_font_to_rect(surface, font, stockcart_title_subrect, stockcart_label, Colors.BLACK, justification="right",
                                 vert_justification="top", font_offset_div=50)
  
  subrect = focus_area.copy().scale_by(1/8, 1/12)
  subrect.centery = stockcart_title_rect.centery
  subrect.left = focus_area.centerx
  
  def rect_color_func(i):
    if not stockcart[i]:
      return Colors.WHITE
    return Colors.chain(stockcart[i])
  
  stockcart_rects = gridifier(surface, subrect, ["None",]*len(stockcart), len(stockcart), 1, rect_color_func, None)
  # endregion
  
  confirm_rect = single_button(surface, "CONFIRM", surface_subrect=focus_area, rect_height_div=10, rect_offest_x=8, rect_offest_y=6)
  
  # region Draw Chain Labels
  chainsgrouped = board.fetchchainsgrouped()
  chains = iter_flatten(chainsgrouped)
  
  def rect_color_func(i):
    return Colors.chain(chains[i])
  
  chain_subrect = focus_area.copy()
  chain_subrect.top = (title_rect.bottom + stockcart_title_rect.bottom)//2
  chain_subrect.height = confirm_rect.top - stockcart_title_rect.bottom
  # pygame.draw.rect(surface, Colors.GREEN, chain_subrect)
  chain_rects = gridifier(surface, chain_subrect, chainsgrouped, None, None, rect_color_func, lambda x: Colors.BLACK, 
                          allignment="center", share_font_size=True, rect_height_spacing_factor=4)
  # endregion
  
  # region Draw Chain + and - and stock price
  plus_min_subrect = chain_rects[0].scale_by(1, .5)
  stock_plusmin_rects = []
  for i, chain_rect in enumerate(chain_rects):
    plus_min_subrect.top = chain_rect.bottom
    plus_min_subrect.centerx = chain_rect.centerx
    
    stockprice = bank.stockcost(chains[i], board.fetchchainsize(chains[i]))
    price_label = "$"+str(stockprice)
    font, font_size = dynamic_font(plus_min_subrect, price_label, Fonts.main, font_scale_max=.8)
    price_title_rect = blit_font_to_rect(surface, font, plus_min_subrect, price_label, Colors.BLACK)
    
    stock_plusmin_label = ["", ""] 
    if chains[i] in stockcart:
      stock_plusmin_label[0] = "-"
    if bank.stocks[chains[i]] and stockprice < p.bal and "" in stockcart:
      stock_plusmin_label[1] = "+"
    
    def rect_color_func(i):
      return Colors.BLACK if stock_plusmin_label[i] else None
    
    stock_plusmin_rect = gridifier(surface, plus_min_subrect, stock_plusmin_label, 2, 1, rect_color_func, lambda x: Colors.WHITE,
                            allignment="center", share_font_size=True, rect_width_spacing_factor=10, rect_width_factor=.5)
    stock_plusmin_rects.extend(stock_plusmin_rect)
  # endregion
  
  return confirm_rect, stock_plusmin_rects

# TODO transition non-popups to new focus_area format
def draw_popup(surface: Surface, subdraw_tag: str, drawinfo):
  # Calculate the size of the popup
  focus_area = get_focus_area(surface)
  popup_rect = focus_area.scale_by(7/8, 4/5)
  font_size = min(popup_rect.w, popup_rect.h) // 20
  font = pygame.font.SysFont(Fonts.main, font_size)
  
  # Create a surface for the popup
  popup = pygame.Surface((popup_rect.w, popup_rect.h))
  popup.fill(Colors.GRAY)
  
  # Draw info into the popup
  closeable = True
  popupInfo = [popup, popup_rect.w, popup_rect.h, font, font_size]
  
  if subdraw_tag == 'mergeChainPriority':
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
  # elif subdraw_tag == 'stockBuy':
  #   subdraw_output = draw_stockbuy(popupInfo, drawinfo)
  
  # Draw the close button on the popup for closeable popups, update offset
  if closeable:
    close_button_rect = pygame.Rect(popup_rect.w - font_size, 0, font_size, font_size)
    pygame.draw.rect(popup, Colors.RED, close_button_rect)
    
    # Create an "x" for the closeable popup button
    font_size = min(popup_rect.w, popup_rect.h) // 25
    font = pygame.font.Font(Fonts.oblivious, font_size)
    label = font.render('x', 1, Colors.WHITE)
    label_rect = label.get_rect()
    label_rect.center = (close_button_rect.centerx + 1, close_button_rect.centery - 2)
    popup.blit(label, label_rect)
    
    close_button_rect.move_ip(popup_rect.left, popup_rect.top)
  else: 
    close_button_rect = None
  
  #Commit popup to the screen
  surface.blit(popup, popup_rect)
  
  # Update the output recs with the position of the popup
  if isinstance(subdraw_output, Rect) == pygame.Rect:
    subdraw_output.move_ip(popup_rect.left, popup_rect.top)
  elif isinstance(subdraw_output, list):
    for rect in subdraw_output:
      if isinstance(rect, pygame.Rect): 
        rect.move_ip(popup_rect.left, popup_rect.top)
  elif isinstance(subdraw_output, tuple):
    for rectList in subdraw_output: 
      for rect in rectList:
        if isinstance(rect, pygame.Rect):
          rect.move_ip(popup_rect.left, popup_rect.top)
  
  return close_button_rect, subdraw_output

def draw_yesorno(popupInfo: tuple[Surface, int, int, Font, int], drawinfo):
  popup, popup_width, popup_height, font, font_size = popupInfo
  
  # Decide title text
  if drawinfo == 'loadSave': label_text = 'Would You Like to Load a Gamestate?'
  elif drawinfo == 'setPlayerNamesLocal': label_text = 'Use Standard Settings?'
  elif drawinfo == 'askToBuy': label_text = 'Would You Like to Buy Stock?'
  elif drawinfo == 'endGameConfirm': label_text = 'Would You Like to End the Game?'
  elif drawinfo == 'endGameStats': label_text = 'Would You Like to Show End Game Stats?'
  else: label_text = 'Default Yes/No Question?'
  
  title_rect = top_rect_title(popup, label_text, y_offset_div=20)
  
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

def draw_mergeChainPriority(popupInfo: tuple[Surface, int, int, Font, int], mergeCart_vec):
  popup, popup_width, popup_height, font, font_size = popupInfo
  mergeCart, chainoptions = mergeCart_vec
  
  if type(mergeCart) == tuple:
    quadMerge_2_2 = True
    mergeCart = mergeCart[0]+mergeCart[1]
    chainoptions = chainoptions[0]+chainoptions[1]
  else:
    quadMerge_2_2 = False
  
  title_rect = top_rect_title(popup, 'Set Merger Priorities')
  
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
  
  title_rect = top_rect_title(popup, f'Defunct Chain Payout ({iofnStatement[0]}/{iofnStatement[1]})', 30, 0)
  
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

def draw_defuncter(popupInfo: tuple[Surface, int, int, Font, int], drawinfo: tuple[Bank, int, int, bool, bool, Player, str, str]):
  popup, popup_width, popup_height, font, font_size = popupInfo
  bank, knob1_x, knob2_x, tradeBanned, defunctingStocks, pDefuncting, defunctChain, bigchain = drawinfo
  keepnumb = int(knob1_x)
  tradenumb = int((defunctingStocks - knob2_x) / 2)
  sellnumb = int(defunctingStocks - (keepnumb + tradenumb))
  
  title_rect = top_rect_title(popup, f"{pDefuncting.name}'s {defunctChain} Stock Defunct Allocation", 30, 0)
  
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
