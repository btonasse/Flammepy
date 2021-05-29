import random
import json

class Space():
    def __init__(self, tile: object, typ: str, size: int) -> None: 
        '''
        Typ[e] can be:
            normal
            uphill = max 5 + no slip)
            downhill = min 5
            cobble = no slip
            supply = min 4
            start/finish/breakaway (special tiles)
        '''
        self.tile = tile # Parent tile
        self.riders = [None for _ in range(size)]
        self.type = typ
        self.max_pw = 9
        self.min_pw = 2
        self.slip = True
        self.start = False
        self.finish = False
        self.breakaway = False
        self._setAttributes()
        # need to store relative coords as well

    def _setAttributes(self) -> None:
        '''
        Change default attributes if special space
        '''
        if self.type == 'uphill':
            self.max_pw = 5
            self.slip = False
        elif self.type == 'downhill':
            self.min_pw = 5
        elif self.type == 'cobble':
            self.slip = False
        elif self.type == 'supply':
            self.min_pw = 4
        elif self.type == 'start':
            self.start = True
        elif self.type == 'finish':
            self.finish = True
        elif self.type == 'breakaway':
            self.breakaway = True

class Tile():
    def __init__(self, id) -> None:
        with open(r'data\tiles.json') as file:
            tiles = json.load(file)
        
        self.spaces = []
        for space in tiles[id]:
            self.spaces.append(Space(self, space[0], space[1]))

        #self.vertices = TO DO (get from json file too)

class Player():
    def __init__(self, color) -> None:
        self.color = color

class Rider():
    def __init__(self, player, typ) -> None:
        self.player = player


if __name__ == '__main__':
    x = Tile('4a')
