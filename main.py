import random
import json

class Space():
    '''
    Typ[e] can be:
        normal
        uphill = max 5 + no slip)
        downhill = min 5
        cobble = no slip
        supply = min 4
        start/finish/breakaway (special tiles)
    '''
    def __init__(self, tile: 'Tile', typ: str, size: int) -> None: 
        self.tile = tile # Parent tile
        self.lanes = [None for _ in range(size)]
        self.type = typ
        self.max_pw = 9
        self.min_pw = 2
        self.slip = True
        self.start = False
        self.finish = False
        self.breakaway = False
        self._setAttributes()
        # need to store relative coords as well

    def __repr__(self) -> str:
        return f"<Space '{self.type}' - tile '{self.tile}'>"
    
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
    def __init__(self, id: str) -> None:
        self.id=id
        with open(r'data\tiles.json') as file:
            tiles = json.load(file)
        
        self.spaces = []
        for space in tiles[id]:
            self.spaces.append(Space(self, space[0], space[1]))

    def __repr__(self) -> str:
        return f"<Tile {self.id}>"

class Course():
    '''
    Main class that stores most of the game state and serves as a connection between Player, Space and Rider classes.
    player_count is a string representation of the minimum and maximum number of players for the course.
    '''
    def __init__(self, name: str, player_count: str) -> None:
        self.name = name
        self.max_players = int(player_count[-1]) # E.g. player_count = '2-4' -> max players = 4
        # Load tiles
        with open(r'data/courses.json') as file:
            courses = tiles = json.load(file)
        self.tiles = []
        for tile_id in courses[name][player_count]:
            self.tiles.append(Tile(tile_id))
        # Put all spaces from tiles in a single list
        self.spaces = []
        for tile in self.tiles:
            self.spaces.extend(tile.spaces)

        # Initialize players and riders lists
        self.players = []
        self.riders = []

        # Initialize final arrival positions
        self.final_positions = []

    def __repr__(self) -> str:
        return f"<Course '{self.name}' - max {self.max_players} players>"

    def addPlayer(self, color: str) -> 'Player':
        '''
        Instantiate new player object and add it to course
        '''
        # Check if max players reached
        if len(self.players) == self.max_players:
            raise RuntimeError(f'Already at max players for course {self.name}: {self.max_players}')
        # Check if color already exists
        if next((player for player in self.players if player.color == color), None):
            raise ValueError(f'A player with color {color} already exists.')
        # Create player, object and add to list
        new_player = Player(color)
        self.players.append(new_player)
        # Add riders to list
        self.riders.append(new_player.sprinteur)
        self.riders.append(new_player.rouleur)
        return new_player

    def _sortRiders(self) -> None:
        '''
        Sorts every rider by position
        '''
        # lane criteria is negative because it can't be reversed
        self.riders.sort(key=lambda x: (x.location[0], -x.location[1]), reverse=True)
        
    
    def _placeRider(self, rider: 'Rider', target: int) -> list:
        '''
        Places a rider in a space, given the space index (and the index of the lane)
        If unsuccessful, recursevily try to place it in an earlier space
        Returns final location of rider
        '''
        # Get current location
        origin = rider.location
        
        if target < origin[0]:
            raise ValueError(f'{rider.color} {rider.type} cannot go backwards.')

        # Condition to break the recursion: try to place it where it already is
        if target == origin[0]:
            return rider.location
                
        # Try to place it in target space
        for i, lane in enumerate(self.spaces[target].lanes):
            if not lane: # lane empty. Place rider there.
                self.spaces[target].lanes[i] = rider
                rider.location = [target, i] # Update rider's location attribute
                if origin[0] != -1: # Erase current location (but not if being placed for first time)
                    self._updateSpace(origin)
                self._sortRiders() # Sort the list of riders by position
                return rider.location
        # Try to place it in next available space
        return self._placeRider(rider, target-1)

    def _updateSpace(self, target: list) -> None:
        '''
        Update a space after a rider moves out of it (i.e. erases rider from space and moves other to the right if needed)
        '''    
        # Erase reference to rider from target space
        self.spaces[target[0]].lanes[target[1]] = None
        # Move any riders on same space to next available lanes
        for i, lane in enumerate(self.spaces[target[0]].lanes):
            if lane is not None:
                lane.location[1] -= 1 # Update Rider object
                self.spaces[target[0]].lanes[i-1], self.spaces[target[0]].lanes[i] = self.spaces[target[0]].lanes[i], None # Update Space object

    def moveRider(self, rider: 'Rider', delta: int) -> list:
        '''
        Try to move rider a given number of spaces.
        Returns the location where they actually end up
        '''
        # Get rider location index
        origin = rider.location[0]
        # Modify delta if location has speed min/max (but not if slipstreaming)
        if delta != 1:
            delta = max(self.spaces[origin].min_pw, min(self.spaces[origin].max_pw, delta))
        # Get target index (limited by size of the course)
        target = min(origin + delta, len(self.spaces)-1)
        
        # Place rider in new location and update all spaces and sort self.lanes
        new_location = self._placeRider(rider, target)
        return new_location

    def _applySlip(self) -> None:
        '''
        Move riders according to slipstreaming rules
        After each peloton moves, a new peloton is formed, so function is called again recursively
        '''
        # Get dictionary of pelotons
        pelotons = self._getPelotons(pelotons={})
        
        # Iterate through each peloton to check if eligible for slipstream (one empty space between them + space type)
        # Exclude last peloton from list to avoid IndexError
        peloton_coords = list(pelotons.keys())
        for i, coord in enumerate(peloton_coords[:-1]):
            this_peloton_end = coord[1]
            next_peloton_start = peloton_coords[i+1][0]
            # Peloton eligible. Move each rider one space (if the space where they are allows it)
            if this_peloton_end+2 == next_peloton_start and self.spaces[next_peloton_start].slip:
                any_rider_moved = False
                for rider in pelotons[coord]:
                    # If space where rider is does not allow slipstream, them and all behind don't move
                    if not self.spaces[rider.location[0]].slip:
                        break
                    else:
                        self.moveRider(rider, 1)
                        any_rider_moved = True
                # If any rider moved, update pelotons
                if any_rider_moved:
                    return self._applySlip()

    def _getPelotons(self, pelotons: dict = {}, begin_at: int = 0) -> dict:
        '''
        Recursively build a dictionary of pelotons
        The key is the (start, end) index of each peloton
        The value is the list of riders in that peloton
        '''
        # Initialize variables
        peloton = []
        start = 0
        end = -1
        # Iterate through all spaces starting at begin_at index
        for i in range(begin_at, len(self.spaces)):
            # Initialize variable that determines if a rider was found this space
            at_least_one_rider_found = False
            
            # Iterate through each lane to search for riders
            riders_on_this_space = []
            for rider in self.spaces[i].lanes: 
                if rider is not None:
                    riders_on_this_space.append(rider)
                    at_least_one_rider_found = True
                    # If first rider was found, set start index to this index
                    if not start:
                        start = i
            # For slipstreaming each peloton is considered from back to front, but each rider has to be moved in order
            # Hence the need to insert at the beginning of the list
            peloton = riders_on_this_space + peloton
            
            # If a peloton was found and we reached and empty space, set previous space as end index
            # Call function again to find next peloton
            if peloton and not at_least_one_rider_found:
                end = i-1
                pelotons[(start,end)] = peloton
                return self._getPelotons(pelotons, end+2)
        return pelotons
    
    def _applyExhaustion(self, rider: 'Rider') -> bool:
        '''
        Draw an exhaustion card if lane ahead of the rider is empty
        Return True if a card is drawn this way
        '''
        # Get space and lane indexes
        space, lane = rider.location[0], rider.location[1]
        # Check if there is a space ahead
        if space+1 <= len(self.spaces)-1:
            # Get lane ahead. Account for a smaller space ahead
            lane_ahead = min(lane, len(self.spaces[space+1].lanes)-1)
            # Check if that space is empty
            if not self.spaces[space+1].lanes[lane_ahead]:
                rider.drawExhaustion()
                return True
    
    def _checkEndGame(self) -> bool:
        '''
        Checks if at least all but one rider already finished the race
        '''
        if len(self.final_positions) >= len(self.riders)-1:
            return True
        else:
            return False

    def _checkFinish(self, rider: 'Rider') -> bool:
        '''
        Check if rider crossed the finish line.
        '''
        # Get rider space index
        rider_location = rider.location[0]
        if self.spaces[rider_location].type == 'finish':
            return True
        else:
            return False

class Player():
    '''
    Player class. Stores the color and two Rider objects.
    '''
    def __init__(self, color: str) -> None:
        self.color = color
        self.sprinteur = Rider(self, 'sprinteur')
        self.rouleur = Rider(self, 'rouleur')
    
    def __repr__(self) -> str:
        return f"<Player {self.color}>"

class Rider():
    '''
    Represents each individual rider.
    Stores a reference to its owner player, its color and type.
    Also tracks its current location on the board (an index of -1 == not yet on the board)
    Also manages the rider's deck and hand
    '''
    def __init__(self, player: 'Player', typ: str) -> None:
        self.player = player
        self.color = self.player.color
        self.type = typ
        self.location: list['int'] = [-1, 0] # Track rider's location (space and lane index)
        self.discard_deck = []
        self.draw_deck = self._buildDeck()
        self.hand = []
        self.drawCards()
        
    def __repr__(self) -> str:
        return f"<Rider '{self.color} {self.type}'>"

    def _buildDeck(self) -> list:
        '''
        Build rider deck and shuffle it.
        '''
        deck = []
        if self.type == 'sprinteur':
            for value in range(2, 6):
                for _ in range(3):
                    deck.append(value)
            for _ in range(3):
                deck.append(9)
        else:
            for value in range(3, 8):
                for _ in range(3):
                    deck.append(value)
        random.shuffle(deck)
        return deck

    def reshuffleDeck(self) -> None:
        '''
        Transfer all cards from discard deck to draw deck again
        Reshuffle draw deck
        '''
        self.draw_deck, self.discard_deck = self.discard_deck[:], []
        random.shuffle(self.draw_deck)

    def drawCards(self) -> None:
        '''
        Draw four cards into hand
        When draw deck is empty, reshuffle discard into it
        '''
        for i in range(4):
            try:
                self.hand.append(self.draw_deck.pop(0))
            except IndexError:
                self.reshuffleDeck()
                self.hand.append(self.draw_deck.pop(0))

    def playCard(self, card_index: int) -> int:
        '''
        Play a card from hand
        Exhaustion cards are represented by -1
        Return the value of the chosen card and discard the whole hand
        '''
        if self.hand[card_index] == -1: # Exhaustion card
            value = 2
        else:
            value = self.hand[card_index]
        # Remove card from the game
        self.hand.pop(card_index)
        # Discard the whole hand
        self.discard_deck.extend(self.hand)
        self.hand = []
        return value

    def drawExhaustion(self) -> None:
        '''
        Add an exhaustion card (represented by a -1) to hand
        '''
        self.discard_deck.append(-1)


def main():
    '''
    Just for testing purposes
    '''
    course = Course('La Classicissima', '2-4')
    p1 = course.addPlayer('red')
    p2 = course.addPlayer('blue')
    course._placeRider(p1.sprinteur, 3)
    course._placeRider(p1.rouleur, 3)
    course._placeRider(p2.sprinteur, 3)
    course._placeRider(p2.rouleur, 3)

    
    
    print(course.spaces[0])
    print(p1)
    print(p1.sprinteur)



if __name__ == '__main__':
    main()

    
    

        
        
        
    

