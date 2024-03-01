import pygame
from plotly import graph_objects as ptgo
from __main__ import HIDE_PERSONAL_INFO, ALLOW_SAVES, ALLOW_QUICKSAVES
from common import write_save
from gui_fullscreen import draw_fullscreenSelect, draw_endGameStats

def postgame(dir_path, screen, clock, framerate, players, currentOrderP, globalStats, saveData):
  pygame.display.set_caption('Postgame')
  postGaming = True
  askMakeSave = True
  askShowStats = True
  selectStatsGraph = False
  popup_open = False
  
  while postGaming:
    # region Render Process
    # Clear the screen
    screen.fill((255, 255, 255))
    #Draw ask to make savestate
    if ALLOW_SAVES and askMakeSave:
      yesandno_rects = draw_fullscreenSelect('makeSave')
    elif askShowStats:
      yesandno_rects = draw_fullscreenSelect('endGameStats')
    elif selectStatsGraph:
      statswap_rects, viewmode_rect = draw_endGameStats(players, statlist, hover_stat_int, clicked_stat_int, viewmode, graphfig)
    # Update the display
    pygame.display.flip()
    # endregion
    
    # region Handle common events
    event = pygame.event.poll()
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
                write_save(dir_path, currentOrderP, globalStats, saveData)
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
                selectStatsGraph = True
                viewmode = "STATS"
                graphfig = None
                statlist = list(p.stats.__dict__.keys())
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
        if hover_stat_int != None:
          clicked_stat_int = (hover_stat_int if clicked_stat_int != hover_stat_int else None)
          if clicked_stat_int != None:
            if viewmode == "USER":
              p = players[clicked_stat_int]
              graph_yaxes = [getattr(p.stats, stat) for stat in statlist if stat not in ('stockChainsOwned', 'stocks', 'mostExpandedChain')]
              graph_yaxes += [ [len(chain_perturn) for chain_perturn in p.stats.stockChainsOwned] ]
              graph_yaxes += [[sum([p.stats.stocks[chain][i] for chain in p.stats.stocks]) for i in globalStats.turnCounter]]
              graph_yaxes += [[sum([p.stats.stocks[chain][i] for chain in p.stats.mostExpandedChain]) for i in globalStats.turnCounter]]
              scatterNames = [stat for stat in statlist if stat not in ('stockChainsOwned', 'stocks', 'mostExpandedChain')] + ['stockChainsOwned', 'stocks', 'mostExpandedChain']
              graphTitle = f"{p.name}'s Stats"
            else:
              stat = statlist[clicked_stat_int]
              if stat not in ('stockChainsOwned', 'stocks', 'mostExpandedChain'):
                graph_yaxes = [getattr(p.stats, stat) for p in players]
              elif stat == 'stockChainsOwned':
                graph_yaxes = [ [len(chain_perturn) for chain_perturn in p.stats.stockChainsOwned] for p in players ]
              elif stat == 'stocks':
                graph_yaxes = [[sum([p.stats.stocks[chain][i] for chain in p.stats.stocks.keys()]) for i in globalStats.turnCounter] for p in players]
              elif stat == 'mostExpandedChain':
                graph_yaxes = [[sum([p.stats.mostExpandedChain[chain][i] for chain in p.stats.mostExpandedChain.keys()]) for i in globalStats.turnCounter] for p in players]
              scatterNames = [p.name for p in players]
              graphTitle = f"{stat} Over Time"
            graphTraces = [ptgo.Scatter(x=globalStats.turnCounter, y=y, mode='lines+markers', name=scatterNames[i]) for i, y in enumerate(graph_yaxes)]
            graphLayout = ptgo.Layout(title=graphTitle)
            graphfig = ptgo.Figure(data=graphTraces, layout=graphLayout)
        elif viewmode_rect.collidepoint(pos):
          clicked_stat_int = graphfig = None
          if viewmode == "STATS": viewmode = "USER"
          else: viewmode = "STATS"
    
    clock.tick(framerate)