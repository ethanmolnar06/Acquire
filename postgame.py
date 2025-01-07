import pygame
from plotly import graph_objects as ptgo

from objects import *
from common import ALLOW_SAVES, MAX_FRAMERATE, VARIABLE_FRAMERATE, NO_RENDER_EVENTS, unpack_gameState, write_save
from gui_fullscreen import draw_fullscreenSelect, draw_endGameStats

def postgame(gameUtils: tuple[pygame.Surface, pygame.time.Clock], gameCompleted: bool, saveData: bytes):
  if saveData is None:
    return
  
  screen, clock = gameUtils
  _, _, players, bank = unpack_gameState(saveData)
  
  postGaming = True
  forceRender = True
  
  askMakeSave = not gameCompleted
  askShowStats = True
  selectStatsGraph = False
  
  popup_open = False
  
  while postGaming:
    event = pygame.event.poll()
    # region Render Process
    if forceRender or event.type not in NO_RENDER_EVENTS:
      forceRender = False
      # Clear the screen
      screen.fill((255, 255, 255))
      #Draw ask to make savestate
      if ALLOW_SAVES and askMakeSave:
        yesandno_rects = draw_fullscreenSelect(screen, 'makeSave')
      elif askShowStats:
        yesandno_rects = draw_fullscreenSelect(screen,'endGameStats')
      elif selectStatsGraph:
        statswap_rects, viewByField_rect = draw_endGameStats(players, statlist, hover_stat_int, clicked_stat_int, viewByField, graphfig)
      # Update the display
      pygame.display.flip()
      # endregion
    
    # region Handle common events
    if event.type == pygame.QUIT:
      postGaming = False
      break
    elif event.type == pygame.VIDEORESIZE:
      # Update the window size
      screen = pygame.display.set_mode((event.w, event.h), pygame.RESIZABLE)
    # endregion
    
    if ALLOW_SAVES and askMakeSave:
      if event.type == pygame.MOUSEBUTTONDOWN:
        # Get the mouse position
        pos = pygame.mouse.get_pos()
        if not popup_open:
          # Check if makeSave was clicked
          for i, yesorno_rect in enumerate(yesandno_rects):
            if yesorno_rect.collidepoint(pos):
              askMakeSave = False
              if i == 1:
                write_save(saveData, [p.name for p in players], bank.stats.turnCounter[-1])
              else:
                askShowStats = True
    
    elif askShowStats:
      if event.type == pygame.MOUSEBUTTONDOWN:
        # Get the mouse position
        pos = pygame.mouse.get_pos()
        if not popup_open:
          # Check if askToBuy was clicked
          for i, yesorno_rect in enumerate(yesandno_rects):
            if yesorno_rect.collidepoint(pos):
              askShowStats = False
              if i == 1:
                forceRender = True
                selectStatsGraph = True
                viewByField = True
                graphrends = {}
                graphfig = None
                statlist = list(players[0].stats.__dict__.keys())
                hover_stat_int, clicked_stat_int = [None]*2
              else:
                postGaming = False
    
    elif selectStatsGraph:
      # Get the mouse position
      pos = pygame.mouse.get_pos()
      for i, statswap_rect in enumerate(statswap_rects):
        if statswap_rect.collidepoint(pos):
          hover_stat_int = i
          break
        else:
          hover_stat_int = None
      if event.type == pygame.MOUSEBUTTONDOWN:
        if viewByField_rect.collidepoint(pos):
          clicked_stat_int = graphfig = None
          viewByField = not viewByField
        elif hover_stat_int is not None:
          clicked_stat_int = (hover_stat_int if clicked_stat_int != hover_stat_int else None)
          if clicked_stat_int is not None:
            if not viewByField:
              p = players[clicked_stat_int]
              if p.name not in graphrends.keys():
                graph_yaxes = [getattr(p.stats, stat) for stat in statlist if stat not in ('stockChainsOwned', 'stocks', 'mostExpandedChain')]
                graph_yaxes += [ [len(chain_perturn) for chain_perturn in p.stats.stockChainsOwned] ]
                graph_yaxes += [[sum([p.stats.stocks[chain][i] for chain in p.stats.stocks]) for i in bank.stats.turnCounter]]
                graph_yaxes += [[sum([p.stats.stocks[chain][i] for chain in p.stats.mostExpandedChain]) for i in bank.stats.turnCounter]]
                scatterNames = [stat for stat in statlist if stat not in ('stockChainsOwned', 'stocks', 'mostExpandedChain')] + ['stockChainsOwned', 'stocks', 'mostExpandedChain']
                graphTitle = f"{p.name}'s Stats"
                graphTraces = [ptgo.Scatter(x=bank.stats.turnCounter, y=y, mode='lines+markers', name=scatterNames[i]) for i, y in enumerate(graph_yaxes)]
                graphLayout = ptgo.Layout(title=graphTitle)
                graphfig = ptgo.Figure(data=graphTraces, layout=graphLayout)
                graphrends[p.name] = graphfig
              else:
                graphfig = graphrends[p.name]
            else:
              stat = statlist[clicked_stat_int]
              if stat not in graphrends.keys():
                if stat not in ('stockChainsOwned', 'stocks', 'mostExpandedChain'):
                  graph_yaxes = [getattr(p.stats, stat) for p in players]
                elif stat == 'stockChainsOwned':
                  graph_yaxes = [ [len(chain_perturn) for chain_perturn in p.stats.stockChainsOwned] for p in players ]
                elif stat == 'stocks':
                  graph_yaxes = [[sum([p.stats.stocks[chain][i] for chain in p.stats.stocks.keys()]) for i in bank.stats.turnCounter] for p in players]
                elif stat == 'mostExpandedChain':
                  graph_yaxes = [[sum([p.stats.mostExpandedChain[chain][i] for chain in p.stats.mostExpandedChain.keys()]) for i in bank.stats.turnCounter] for p in players]
                scatterNames = [p.name for p in players]
                graphTitle = f"{stat} Over Time"
                graphTraces = [ptgo.Scatter(x=bank.stats.turnCounter, y=y, mode='lines+markers', name=scatterNames[i]) for i, y in enumerate(graph_yaxes)]
                graphLayout = ptgo.Layout(title=graphTitle)
                graphfig = ptgo.Figure(data=graphTraces, layout=graphLayout)
                graphrends[stat] = graphfig
              else:
                graphfig = graphrends[stat]
    
    clock.tick(1 if VARIABLE_FRAMERATE and not pygame.key.get_focused() else MAX_FRAMERATE)
