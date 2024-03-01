import datetime
import os
import pickle
class Colors:
  def __init__(self):
    self.BLACK = (0, 0, 0)
    self.WHITE = (255, 255, 255)
    self.GRAY = (192, 192, 192)
    self.UNSELECTABLEGRAY = (158, 158, 158)
    self.RED = (255, 0, 0)
    self.LIGHTGREEN = (72, 178, 72)
    self.GREEN = (34, 139, 34)
    self.DARKGREEN = (27, 108, 27)
    self.YELLOW = (240, 230, 140)
    self.OUTLINE = (189, 183, 107)

    self.Tower = (255, 255, 0) #bright yellow
    self.Luxor = (255, 145, 0), # bright orange
    self.Surfside = (32, 178, 170), # teal
    self.Nomad = (78, 49, 82), # murky purple
    self.Keystone = (27, 108, 27), # green
    self.Eclipse = (99, 38, 95), # deep purple

    self.American = (0, 0, 230), # blue
    self.Festival = (35, 70, 41), # dark green
    self.Worldwide = (130, 76, 0), # brown
    self.Highrise = (219, 120, 130), # rose/peach
    self.Boulevard = (185, 20, 20), # deep brick red
    self.Rendezvous = (34, 205, 66), # neon green
    self.Voyager = (71, 71, 71), # smoggy dark gray
    self.Journeyman = (123, 249, 206), # mint 

    self.Imperial = (255, 51, 153), # bright pink
    self.Continental = (100, 149, 237), # light blue
    self.Wynand = (153, 122, 141), # gray
    self.Mirage = (211, 57, 238), # magenta
    self.Panorama = (84, 248, 254) #searing bright blue

    self.colorcount = 10
    self.chaincolorcount = 19

class Fonts:
  def __init__(self) -> None:
    self.main = 'timesnewroman'
    self.tile = "arial"
    self.oblivious = r'fonts/oblivious-font.regular.ttf'

colors = Colors()
fonts = Fonts()

def colortest(screen, clock, colors):
  import pygame
  while colorLoop:
    for color in colors.__dict__.keys():
      screen.fill(colors.__getattribute__(color))
      pygame.display.flip()
      event = pygame.event.poll()
      if event.type == pygame.QUIT:
        colorLoop = False
        break
      clock.tick(1)

def write_save(dir_path, currentOrderP, globalStats, saveData, quicksave = False):
  date = datetime.date.isoformat(datetime.date.today())
  if quicksave:
    save_file_new = "quicksave"
  else:
    save_file_new = f'{date}_{len(currentOrderP)}players_{"".join([p.name for p in currentOrderP])}_turn{globalStats.turnCounter[-1]}'
  if not os.path.exists(rf'{dir_path}\saves\{save_file_new}'):
    with open(rf'{dir_path}\saves\{save_file_new}', 'x') as file:
      pass
  with open(rf'{dir_path}\saves\{save_file_new}', 'wb') as file:
    prevdata = None
    for data in saveData:
      prevdata = pickle.dumps((prevdata, data))
    pickle.dump(prevdata, file)
  return
