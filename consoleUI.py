# Console interface
from main import Course, Player, Rider
from console import fg, bg, fx
import json
from typing import Union

# Make black color readable on console
fg.black = fg.darkgray

class App():
    '''
    Main class for IO and implementing the game loop
    '''
    player_colors = ['blue', 'green', 'red', 'pink', 'white', 'black']
    def __init__(self) -> None:
        # Series of prompts to set up the game
        self.setUp()

    def drawCourse(self) -> str: 
        '''
        Build a string representation of the board state (as a straight line)
        Use three lines (one for each potential lane)
        '''
        first_line = second_line = third_line =  '>'
        for i, space in enumerate(self.course.spaces):
            if space.type == 'uphill':
                sq = ' ' + fg.red + '|' + fx.default
            elif space.type == 'downhill':
                sq = ' ' + fg.blue + '|' + fx.default
            elif space.type == 'cobble':
                sq = ' ' + fg.yellowgreen + '|' + fx.default
            elif space.type == 'supply':
                sq = ' ' + fg.cyan + '|' + fx.default
            elif space.type in ['start', 'finish']:
                sq = ' ' + fg.yellow + '|' + fx.default
            else:
                sq = ' ' + fx.default + '|'
            
            if len(space.lanes) == 3:
                if space.lanes[2]:
                    first_line += sq.replace(' ', getattr(fg, space.lanes[2].color) + space.lanes[2].type[0])
                else:
                    first_line += sq
            else:
                first_line += '  '

            if len(space.lanes) >= 2:
                if space.type == 'breakaway' and len(space.lanes) == 3: # Color breakaway lane
                    sq = ' ' + fg.goldenrod + '|' + fx.default
                if space.lanes[1]:
                    second_line += sq.replace(' ', getattr(fg, space.lanes[1].color) + space.lanes[1].type[0])
                else:
                    second_line += sq
            else:
                second_line += '  '

            if space.type == 'breakaway': # Color breakaway lane
                sq = ' ' + fg.goldenrod + '|' + fx.default
            if space.lanes[0]:
                third_line += sq.replace(' ', getattr(fg, space.lanes[0].color) + space.lanes[0].type[0])
            else:
                third_line += sq

        border = '#'*(len(self.course.spaces)*2+1)
        if not first_line.count('|'): # No spaces have three lanes. No need to draw first line.
            final_string = '\n'.join([border, second_line, third_line, border])    
        else:
            final_string = '\n'.join([border, first_line, second_line, third_line, border])
        return final_string
    
    def _choosePlayerCount(self) -> int:
        '''
        Get player count from user
        '''
        player_count = getInput('How many players (or [q]uit)?', '23456', 'q')
        return int(player_count)

    def _chooseCourse(self) -> 'Course':
        '''
        Select a Course and return it as an object
        '''
        # Get player count range string (used as key when selecting a course)
        if self.player_count <= 4:
            count_range = '2-4'
        else:
            count_range = '5-6'
        
        # Load courses from file
        with open(r'data\courses.json') as file:
            courses = json.load(file)
        
        # Print each course name and index
        choices = ''
        for i, course in enumerate(courses.keys()):
            choices += str(i+1) # Add 1 to each index so the list starts at 1
            print(str(i+1) + ' - ' + course)
        # Prompt user for a choice
        chosen_course = getInput('Choose one of the courses above:', choices, 'q')
        # Get chosen course name
        course_name = list(courses.keys())[int(chosen_course)-1]
        try:
            # Create course object. Might fail if there is no version for the chosen player count
            return Course(course_name, count_range)
        except KeyError:
            input(f'{course_name} does not have a version for this player count: {count_range}. Press Enter to try again...')
            return self._chooseCourse()

    def _addPlayers(self) -> None:
        '''
        Add one player per player count.
        Colors are chosen from the class variable player_colors
        '''
        selected = set()
        while len(selected) < self.player_count:
            # Print options
            for i, color in enumerate(self.player_colors):
                # Skip a color that has been selected already
                if i in selected:
                    continue
                print(i+1, '-', color)
            
            # Prompt user for choice of a color index
            # Get list of valid choices
            valid_choices = [str(i+1) for i in range(len(self.player_colors)) if i not in selected]
            selected_index = getInput(f'Player {len(selected)+1}, select a color above:', valid_choices, 'q')
            # Add selected index to set (subtracting 1 to get actual index)
            selected.add(int(selected_index)-1)
            # Get color name and add player object of that color
            selected_color = self.player_colors[int(selected_index)-1]
            self.course.addPlayer(selected_color)

    def setUp(self) -> None:
        '''
        Initializing function to set up the game board.
        '''
        # Ask for input and set player count
        self.player_count = self._choosePlayerCount()
        # Ask for input and choose course
        self.course = self._chooseCourse()
        # Add players
        self._addPlayers()

    def _initialPlacement(self) -> None:
        '''
        Gets input from players to place their riders behind the start line
        '''
        valid_start_pos = [str(self.course.spaces.index(space)) for space in self.course.spaces if space.type in ['start', 'breakaway']]
        for player in self.course.players:
            for rider in [player.sprinteur, player.rouleur]:
                print(self.drawCourse())
                print('Valid positions: ', ' | '.join(valid_start_pos))
                start_pos = getInput(f'Player {player.color}, place your {rider.type}: ', valid_start_pos, 'q', color=player.color)
                self.course._placeRider(rider, int(start_pos))
                # If bemove breakaway position selected, remove it from list.
                # Otherwise when selecting an already taken position, riders will just be placed on the next available lane or space
                if start_pos == '9': # Breakaway tiles are always on index 9 of the course
                    if sum(isinstance(x, Rider) for x in self.course.spaces[9].lanes) == len(self.course.spaces[9].lanes)-1:
                        valid_start_pos.remove('9')

    def _cardSelectionRounds(self) -> dict:
        '''
        Have each player select one rider ande play one card.
        Return a dictionary with riders as keys and movement values as values.
        '''
        # Initialize dict of riders and played cards
        riders_and_cards = {rider: None for rider in self.course.riders}
        # Initialize string representation of cards played after first round
        cards_played_last_round = []
        for i in range(2):
            for player in self.course.players:
                # Print board
                print(self.drawCourse())
                
                # Get rider selection
                rider_selected = self.selectRider(player, riders_and_cards)
                # If there are no riders left to select, skip to next player
                if not rider_selected:
                    continue
                
                # If on second round, display cards played so far before playing a card
                if i == 1:
                    print('Cards played so far: ', ' | '.join(cards_played_last_round), sep='')
                # Select a card (return card index in rider's hand)
                card_index = self.selectCard(rider_selected)
                
                # Build string representation of rider and his played card
                if i == 0: # Can't display cards as they are played during second round
                    rider_as_str = _colorWrapper(rider_selected.type, rider_selected.color)
                    if rider_selected.hand[card_index] == -1: # Display an E instead of -1 for exhaustion cards
                        card_as_str = 'E'    
                    else:
                        card_as_str = str(rider_selected.hand[card_index])
                    cards_played_last_round.append(rider_as_str + ': ' + card_as_str)
                
                # Play the card and assign its move value to return variable
                move_value = rider_selected.playCard(card_index)
                riders_and_cards[rider_selected] = move_value

        return riders_and_cards

    def gameLoop(self) -> list:
        '''
        Main game loop.
        Returns the final positions after race is over
        '''
        print(f'The race is about to begin! Course: {self.course.name}')
        # Initial placement of riders
        self._initialPlacement()

        # Initialize turn counter (is an instance variable so we can know on which turn each rider finishes)
        self.turn = 1
        while True:
            print(_colorWrapper(f'Starting turn {self.turn}...', 'lightsalmon'))
            # Card selection and play loop
            played_cards = self._cardSelectionRounds()

            # Move riders in order and get string representation of played cards
            played_cards_as_str = []
            for rider in self.course.riders:
                delta = played_cards[rider]
                if delta: # If rider already finished, delta will be None
                    self.course.moveRider(rider, delta)
                    played_cards_as_str.append(_colorWrapper(rider.type, rider.color) + ': ' + str(delta))

            # Redraw board and wait for Enter to apply slipstream
            print('Moved this turn (before inclination effects): ', ' | '.join(played_cards_as_str))
            print(self.drawCourse())
            input(_colorWrapper('Riders have moved! Press Enter to apply slipstream...', 'lightsalmon'))

            # Apply slipstream
            self.course._applySlip()
            print(self.drawCourse())
            input(_colorWrapper('Slipstream applied! Press Enter to continue...', 'lightsalmon'))

            # Check if riders are finished already
            for rider in self.course.riders:
                is_finished = self.course._checkFinish(rider)
                if is_finished:
                    # If finished, add to final_positions and remove from board
                    if rider not in [r[0] for r in self.course.final_positions]:
                        self.course.final_positions.append([rider, self.turn])
                        self.course.spaces[rider.location[0]].lanes[rider.location[1]] = None
                    continue
            
            #Check if game over
            game_ended = self.course._checkEndGame()
            if game_ended:
                input(_colorWrapper(f'The race is over on turn {self.turn}! Press Enter to see results... ', 'lightsalmon'))
                # Build string representation of final positions
                final_positions_as_str = []
                for rider, turn in self.course.final_positions:
                    final_positions_as_str.append(_colorWrapper(rider.type, rider.color) + ': turn ' + str(turn))
                # Build string representation of riders that didn't finish
                not_finished_as_str = []
                for rider in self.course.riders:
                    if rider not in [r[0] for r in self.course.final_positions]:
                        not_finished_as_str.append(_colorWrapper(rider.type, rider.color))
                final_string = ' | '.join(final_positions_as_str) + '\n' + 'Riders that did not finish: ' + ', '.join(not_finished_as_str)
                input(final_string)
                return self.course.final_positions

            # If game not over, apply exhaustion
            # And build string representation of riders that had exhaustion applied
            exhausted_as_str = []
            for rider in self.course.riders:
                is_exhausted = self.course._applyExhaustion(rider)
                if is_exhausted:
                    exhausted_as_str.append(_colorWrapper(rider.type, rider.color))
                
                # Draw cards again
                rider.drawCards()
            print('These riders are getting tired: ' + ', '.join(exhausted_as_str) + '. Press Enter to start next turn...', end='')
            input('')

            self.turn += 1

            
    def selectRider(self, player: 'Player', riders_and_cards: dict) -> Union['Rider', None]:
        '''
        If both riders can still be selected, get input from player.
        Otherwise return the only selectable rider or None if both have already finished/been selected.
        '''
        # Initialize flags that determine whether each rider can be selected
        selectable = {player.sprinteur: True, player.rouleur: True}
        # Check if rider has already finished or has already been selected in a previous round
        for rider in selectable.keys():
            if self.course._checkFinish(rider) or riders_and_cards[rider]:
                selectable[rider] = False
        
        # Only prompt player for input if both riders are selectable
        if sum(selectable.values()) == 2:
            rider_selected = getInput(f'Player {player.color}, select a rider: [s]printeur or [r]ouleur? ', 'sr', 'q', color=player.color)
            if rider_selected == 's':
                return player.sprinteur
            else:
                return player.rouleur
        # Return whichever rider has not been selected yet
        elif sum(selectable.values()) == 1:
            return list(selectable.keys())[list(selectable.values()).index(True)]
        # No riders can be selected
        else:
            return None

    def selectCard(self, rider: 'Rider') -> int:
        # Generate printable list of cards in hand to play (convert -1 to E for exhaustion cards)
        hand = [str(i+1) + ': ' + _colorWrapper('E', rider.color) if card==-1 else str(i+1) + ': ' + _colorWrapper(str(card), rider.color) for i, card in enumerate(rider.hand)]
        print('\n'.join(hand))
        # Get list of valid indexes
        valid_indexes = [str(i+1) for i in range(len(hand))]
        card_selected = getInput(f'Hey, {rider.color} {rider.type}, select one of the cards above to play: ', valid_indexes, 'q', color=rider.color)
        return int(card_selected)-1

def _colorWrapper(text: str, fg_color: str = '', bg_color: str = '') -> str:
    '''
    Wraps color from console module onto a text string
    Color must be a valid webcolor string (or any string recognized by the console module)
    '''
    # Foreground
    if fg_color:
        try:
            fg_color = getattr(fg, fg_color)
        except AttributeError as err:
            print(err)
            fg_color = ''
    # Background
    if bg_color:
        try:
            bg_color = getattr(bg, bg_color)
        except AttributeError as err:
            print(err)
            bg_color = ''

    colored_text = fg_color + bg_color + text + fx.default
    return colored_text


def getInput(text: str, valids: Union[list, str], quit: str, color: str = 'lightsalmon', case_sensitive: bool = False) -> Union[str, bool]:
    '''
    Convenience function to get input from user.
    Will repeat prompt until a valid input (or the string for 'quit') is entered
    If 'quit', immediately exit the app after another prompt
    '''
    # Change color of prompt
    colored_input = _colorWrapper(text, color) + ' '
    while True:
        answer = input(colored_input)
        if not case_sensitive:
            answer = answer.lower()
        if answer in valids:
            return answer
        elif answer == quit:
            input('Press Enter to quit...')
            exit()

def main():
    app = App()
    app.gameLoop()
    input('')

if __name__ == '__main__':
    main()
