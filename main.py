from __future__ import annotations

import os
from dataclasses import dataclass
import random

import pygame as pg
from rich import print


@dataclass
class Vec2:
  x: int
  y: int

  @property
  def xy(self) -> tuple[int]: return (self.x, self.y)

  def __add__(self, other: Vec2) -> Vec2: return Vec2(self.x + other.x, self.y + other.y)
  def __sub__(self, other: Vec2) -> Vec2: return Vec2(self.x - other.x, self.y - other.y)
  def __mul__(self, other: int) -> Vec2: return Vec2(self.x * other, self.y * other)


@dataclass
class Tile:
  pos:        Vec2
  isMine:     bool
  flagged:    bool = False
  isRevealed: bool = False
  mines:      int  = 0
  
  @property
  def color(self) -> tuple[int]:
    # Main            Revealed
    # 179	214	101     223	195	163	
    # 172	208	94      203	179	152
    v = self.pos.x + self.pos.y
    if not self.isRevealed:
      return (179, 214, 101) if v % 2 else (172, 208, 94)
    return (223, 195, 163) if v % 2 else (203, 179, 152)


class Display:
  __slots__ = '_surface'

  def __init__(self, width: int, height: int) -> None:
    self._surface = pg.display.set_mode((width, height))
  
  def clear(self) -> None:
    self._surface.fill((18, 18, 18))
  
  def update(self) -> None:
    pg.display.update()


class Game:
  __slots__ = '_display', 'tilemap', 'tilesize', '_hTiles', '_vTiles', '_running', '__minesSet', 'font'

  def __init__(self, horizontalTiles: int, verticalTiles: int) -> None:
    self.tilemap: list[list[Tile]] = []
    self.tilesize = 32
    self._hTiles, self._vTiles = horizontalTiles, verticalTiles
    self._display: Display = Display(self.tilesize * (self._hTiles - 2), self.tilesize * (self._vTiles - 2))
    self._running = True
    self.__minesSet = False
    self.font = pg.font.SysFont('Arial', self.tilesize)

    self.init_tilemap()

  def draw_text(self, text: str, pos: Vec2) -> None:
    text = str(text)
    text_surface = self.font.render(text, True, (255, 255, 255))
    self._display._surface.blit(text_surface, pos.xy)
  
  def init_tilemap(self) -> None:
    for y in range(self._vTiles):
      if (y == 0) or (y == self._vTiles - 1):
        self.tilemap.append([None for _ in range(self._hTiles)])
        continue

      self.tilemap.append([]) # Add a empty row to tilemap
      for x in range(self._hTiles):
        if (x == 0) or (x == self._hTiles - 1):
          self.tilemap[y].append(None)
          continue
        
        pos = Vec2(x, y)
        self.tilemap[y].append(Tile(pos, False))

  def get_neighbour_tiles(self, pos: Vec2) -> list[Tile]:
    return [i for i in [
      self.tilemap[pos.y - 1][pos.x - 1], self.tilemap[pos.y - 1][pos.x], self.tilemap[pos.y - 1][pos.x + 1],
      self.tilemap[pos.y][pos.x - 1],                                     self.tilemap[pos.y][pos.x + 1],
      self.tilemap[pos.y + 1][pos.x - 1], self.tilemap[pos.y + 1][pos.x], self.tilemap[pos.y + 1][pos.x + 1],
    ] if i is not None]

  def set_mines(self, start_pos: Vec2) -> None:
    self.__minesSet = True
    
    # Generate mines
    for y in range(1, self._vTiles - 1):
      for x in range(1, self._hTiles - 1):
        if not random.randint(0, 6):
          self.tilemap[y][x].isMine = True
    
    self.tilemap[start_pos.y][start_pos.x].isMine = False
    neighbours = self.get_neighbour_tiles(start_pos)
    for neighbour in neighbours:
      neighbour.isMine = False
    
    # Get amount of mines attached to tile
    for y in range(1, self._vTiles - 1):
      for x in range(1, self._hTiles - 1):
        tile = self.tilemap[y][x]
        pos = tile.pos
        
        count = 0
        neighbours: list[Tile] = self.get_neighbour_tiles(pos)
        
        for _tile in neighbours:
          if _tile.isMine: count += 1
        
        tile.mines = count
  
  def reveal_tiles(self, pos: Vec2) -> None:
    if self.tilemap[pos.y][pos.x].mines == 0:
      neighbours = self.get_neighbour_tiles(pos)
      for neighbour in neighbours:
        if not neighbour.isRevealed and not neighbour.mines:
          neighbour.isRevealed = True
          self.reveal_tiles(neighbour.pos)
        neighbour.isRevealed = True

  def handle_events(self) -> None:
    for event in pg.event.get():
      if event.type == pg.QUIT:
        self._running = False
      
      if event.type == pg.MOUSEBUTTONDOWN:
        mPos = pg.mouse.get_pos()
        pos = Vec2(mPos[0] + self.tilesize, mPos[1] + self.tilesize)
        pos.x = pos.x // self.tilesize
        pos.y = pos.y // self.tilesize
        
        tile = self.tilemap[pos.y][pos.x]
        if event.button == 1:
          if tile.flagged: continue # Check if tile has a flag, if so continue
          if tile.isRevealed: continue # Check if tile is already visible, if so continue
          if tile.isMine: self._running = False # Check if tile is a mine, if True exit game
          # Set mines if mines havent been set
          if not self.__minesSet: self.set_mines(pos)
          tile.isRevealed = True # Reveal tile
          self.reveal_tiles(pos)
        
        if event.button == 3:
          tile.flagged = not tile.flagged

  def run(self) -> None:
    clock = pg.time.Clock()

    while self._running:
      clock.tick(120)
      self.handle_events()

      self._display.clear()

      offset = Vec2(self.tilesize, self.tilesize)
      for row in self.tilemap:
        for tile in row:
          if not tile: continue
          pos = (tile.pos * self.tilesize - offset).xy
          pg.draw.rect(self._display._surface, tile.color, (*pos, self.tilesize, self.tilesize))
          if tile.flagged:
            pg.draw.rect(self._display._surface, (255, 0, 0), (*(Vec2(*pos) + Vec2(8, 8)).xy, self.tilesize - 16, self.tilesize - 16))

          if not tile.isRevealed or not tile.mines: continue
          self.draw_text(tile.mines, Vec2(*pos) + Vec2(8, 0))

      self._display.update()


def main() -> None:
  game = Game(48, 32)
  game.run()

if __name__ == '__main__':
  os.system('clear')
  pg.init()
  main()
