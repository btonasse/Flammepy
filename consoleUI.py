# Console interface
from main import Course, Tile, Space, Player, Rider
from console import fg, bg, fx
import json
from typing import Union

# Make black color readable on console
fg.black = fg.darkgray

class App():
    player_colors = ['blue', 'green', 'red', 'pink', 'white', 'black']
    exit_prompt = 'Press Enter to quit...'
    def __init__(self) -> None:
        # Series of prompts to set up the game
        self.setUp()

        # Game loop (todo)

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
            
            if len(space.riders) == 3:
                if space.riders[2]:
                    first_line += sq.replace(' ', getattr(fg, space.riders[2].color) + space.riders[2].type[0])
                else:
                    first_line += sq
            else:
                first_line += '  '

            if len(space.riders) >= 2:
                if space.type == 'breakaway' and len(space.riders) == 3: # Color breakaway lane
                    sq = ' ' + fg.goldenrod + '|' + fx.default
                if space.riders[1]:
                    second_line += sq.replace(' ', getattr(fg, space.riders[1].color) + space.riders[1].type[0])
                else:
                    second_line += sq
            else:
                second_line += '  '

            if space.type == 'breakaway': # Color breakaway lane
                sq = ' ' + fg.goldenrod + '|' + fx.default
            if space.riders[0]:
                third_line += sq.replace(' ', getattr(fg, space.riders[0].color) + space.riders[0].type[0])
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
        if player_count == False:
            input(self.exit_prompt)
            exit()
        else:
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
        if chosen_course == False:
            input(self.exit_prompt)
            exit()
        else:
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
            if selected_index == False:
                input(self.exit_prompt)
                exit()
            else:
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
        #riders_left = {player.color: [player.sprinteur, player.rouleur] for player in self.course.players}
        valid_start_pos = [str(self.course.spaces.index(space)) for space in self.course.spaces if space.type in ['start', 'breakaway']]
        for player in self.course.players:
            for rider in [player.sprinteur, player.rouleur]:
                print(self.drawCourse())
                start_pos = getInput(f'Player {player.color}, place your {rider.type}: ', valid_start_pos, 'q', color=player.color)
                if start_pos == False:
                    input(self.exit_prompt)
                    exit()
                self.course._placeRider(rider, int(start_pos))

    def _cardSelectionRounds(self) -> dict:
        '''
        Have each player select one rider ande play one card.
        Return a dictionary with riders as keys and movement values as values.
        '''
        # Initialize dict of riders and played cards
        riders_and_cards = {player: {player.sprinteur: None, player.rouleur: None} for player in self.course.players}
        # Initialize string representation of cards played after first round
        cards_played_so_far = []
        for i in range(2):
            for player in self.course.players:
                # Print board
                print(self.drawCourse())
                # First round, the players needs to select one of their riders
                if i == 0:
                    rider_selected = self.selectRider(player)
                # Otherwise, pick whatever rider is left
                else:
                    rider_selected = list(riders_and_cards[player].keys())[list(riders_and_cards[player].values()).index(None)]
                    print('Cards played so far: ', ' | '.join(cards_played_so_far), sep='')
                # Select a card (return card index in rider's hand)
                card_index = self.selectCard(rider_selected)
                # Build string representation of rider and his played card
                if i == 0:
                    rider_as_str = _colorWrapper(rider_selected.type, rider_selected.color)
                    if rider_selected.hand[card_index] == -1:
                        card_as_str = 'E'    
                    else:
                        card_as_str = str(rider_selected.hand[card_index])
                    cards_played_so_far.append(rider_as_str + ': ' + card_as_str)
                # Play the card and assign its move value to return variable
                move_value = rider_selected.playCard(card_index)
                riders_and_cards[player][rider_selected] = move_value

        # Flatten dictionary to get k=rider, v=move_value (player is irrelevant when moving the rider)
        riders_and_cards = {rider: value for dic in riders_and_cards.values() for rider, value in dic.items()}
        return riders_and_cards



    def gameLoop(self) -> None:
        '''
        Main game loop
        '''
        print(f'The race is about to begin! Course: {self.course.name}')
        # Initial placement of riders
        self._initialPlacement()
        
        # Initialize turn counter
        turn = 1
        while True:
            print(_colorWrapper(f'Starting turn {turn}...', 'lightsalmon'))
            # Card selection and play loop
            played_cards = self._cardSelectionRounds()

            # Move riders in order and get string representation of played cards
            played_cards_as_str = []
            for rider in self.course.riders:
                delta = played_cards[rider]
                self.course.moveRider(rider, delta)
                played_cards_as_str.append(_colorWrapper(rider.type, rider.color) + ': ' + str(delta))

            # Redraw board and wait for Enter to apply slipstream
            print('Movement this turn: ', ' | '.join(played_cards_as_str))
            print(self.drawCourse())
            input(_colorWrapper('Riders have moved! Press Enter to apply slipstream...', 'lightsalmon'))

            # Apply slipstream
            self.course._applySlip()
            print(self.drawCourse())
            input(_colorWrapper('Slipstream applied! Press Enter to apply exhaustion...', 'lightsalmon'))
            
            # Apply exhaustion
            self.course._applyExhaustion()
            # Build string representation of riders that had exhaustion applied
            exhausted_as_str = []
            for rider in self.course.riders:
                if rider.discard_deck[-1] == -1:
                    exhausted_as_str.append(_colorWrapper(rider.type, rider.color))
                # Draw cards again
                rider.drawCards()
            print('These riders are getting tired: ' + ', '.join(exhausted_as_str) + '. Press Enter to start next turn...', end='')
            input('')

            

            #Check if game over -todo
            turn += 1


            
    def selectRider(self, player: 'Player') -> 'Rider':
        rider_selected = getInput(f'Player {player.color}, select a rider: [s]printeur or [r]ouleur? ', 'sr', 'q', color=player.color)
        if rider_selected == False:
            input(self.exit_prompt)
            exit()
        if rider_selected == 's':
            return player.sprinteur
        else:
            return player.rouleur

    def selectCard(self, rider: 'Rider') -> int:
        # Generate printable list of cards in hand to play (convert -1 to E for exhaustion cards)
        hand = [str(i+1) + ': ' + _colorWrapper('E', rider.color) if card==-1 else str(i+1) + ': ' + _colorWrapper(str(card), rider.color) for i, card in enumerate(rider.hand)]
        print('\n'.join(hand))
        # Get list of valid indexes
        valid_indexes = [str(i+1) for i in range(len(hand))]
        card_selected = getInput(f'Hey, {rider.color} {rider.type}, select one of the cards above to play: ', valid_indexes, 'q', color=rider.color)
        if card_selected == False:
            input(self.exit_prompt)
            exit()
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
    If quit, return False instead of the quit string
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
            return False

def main():
    app = App()
    #for player in app.course.players:
    #    print(player.__dict__)
    #for rider in app.course.riders:
    #    app.course._placeRider(rider, 4)
    #print(app.drawCourse())
    app.gameLoop()
    input('')

if __name__ == '__main__':
    main()
