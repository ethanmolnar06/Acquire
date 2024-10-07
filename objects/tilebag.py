import string
import itertools
import random

def make_tileLetterTable(n: int) -> list[str]:
  maxletterlenght = (n-1)//26
  tileLetters = [[]]*(maxletterlenght+1)
  letters = [''] + list(string.ascii_uppercase)
  for i in range(maxletterlenght+1):
    tileLetters[i] = [letters[i] + l for l in letters[1:]]
  if n%26 != 0: tileLetters[-1] = tileLetters[-1][:n%26]
  return list(itertools.chain(*tileLetters))

def make_chainTierGrouped(cheap: int = 2, med: int = 3, high: int = 2) -> dict[list]:
  defCheap = ['Tower', 'Luxor']
  defMed = ['American', 'Festival', 'Worldwide']
  defHigh = ['Imperial', 'Continental']
  custCheap = ["Surfside", "Nomad", "Keystone", "Eclipse"]
  custMed = ["Highrise", "Boulevard", "Rendezvous", "Voyager", "Journeyman"]
  custHigh = ["Wynand", "Mirage", "Panorama"]
  cheap = min(max(cheap, 0), len(defCheap)+len(custCheap))
  med = min(max(med, 0), len(defMed)+len(custMed))
  high = min(max(high, 0), len(defHigh)+len(custHigh))
  chainTierGrouped = {'cheap': (defCheap+custCheap)[:cheap],
                      'med': (defMed+custMed)[:med],
                      'high': (defHigh+custHigh)[:high]}
  return chainTierGrouped

class TileBag:
  def __init__(self, numbers = 12, letters = 9, cheapChains = 2, mediumChains = 3, pricyChains = 2):
    self.cols = int(numbers) 
    self.rows = int(letters)
    self.tilelettertable = make_tileLetterTable(self.rows)
    self.alltiles = [str(n+1)+l for n in range(self.cols) for l in self.tilelettertable]
    self.tilesleft = list(range(len(self.alltiles)))
    self.chainTierGrouped = make_chainTierGrouped(int(cheapChains), int(mediumChains), int(pricyChains))
    self.chainnames = list(itertools.chain(*self.chainTierGrouped.values()))
    # self.chainnames = [name[0] for name in self.chainnames]
  
  def drawtile(self):
    if len(self.tilesleft) <= 0:
      return None
    drawntileID = self.tilesleft[random.randrange(0, len(self.tilesleft))]
    self.tilesleft.remove(drawntileID)
    return drawntileID
  
  def resetbag(self):
    self.tilesleft = list(range(len(self.alltiles)))
  
  def tileIDinterp(self, tileIDs: list[int]) -> list[str]:
    return [str((ID//self.rows)+1 ) + self.tilelettertable[ID%self.rows] for ID in tileIDs]
  
  def tilesToIDs(self, tiles: list[str]) -> list[int]:
    return [ (int(tile[0:-1])-1)*self.rows + self.tilelettertable.index(tile[-1]) for tile in tiles]
