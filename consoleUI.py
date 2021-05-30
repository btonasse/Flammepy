# Console interface
from main import Course, Tile, Space, Player, Rider
from console import fg, bg, fx
import json
from typing import Union

class App():
    player_colors = ['blue', 'green', 'red', 'pink', 'white', 'black']
    exit_prompt = 'Press Enter to quit...'
    def __init__(self) -> None:
        # Series of prompts to set up the game
        self.setUp()

    def _choosePlayerCount(self) -> int:
        '''
        Get player count from user
        '''
        player_count = getInput('How many players (or [q]uit)?', '23456', 'q')
        if not player_count:
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
        if not chosen_course:
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
            if not selected_index:
                input(self.exit_prompt)
                exit()
            else:
                # Add selected index to set (subtracting 1 to get actual index)
                selected.add(int(selected_index)-1)
                # Get color name and add player object of that color
                selected_color = self.player_colors[int(selected_index)-1]
                self.course.addPlayer(selected_color)

    def setUp(self) -> None:
        # Set player count
        self.player_count = self._choosePlayerCount()
                
        # Choose course
        self.course = self._chooseCourse()

        # Add players
        self._addPlayers()


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
    for player in app.course.players:
        print(player.__dict__)
    input('')

if __name__ == '__main__':
    main()
