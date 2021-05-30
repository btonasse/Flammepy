# Console interface
from main import Course, Tile, Space, Player, Rider
from console import fg, fx
import json
from typing import Union


def getInput(text: str, valids: Union[list, str], quit: str, color: str = 'lightsalmon', case_sensitive: bool = False) -> Union[str, bool]:
    colored_input = getattr(fg, color) + text + fx.default + ' '
    while True:
        answer = input(colored_input)
        if not case_sensitive:
            answer = answer.lower()
        if answer in valids:
            return answer
        elif answer == quit:
            return False


def setUp() -> 'Course':
    # Get player count
    player_count = getInput('How many players (or [q]uit)?', '23456', 'q')
    if not player_count:
        print('Quitting...')
        return
    else:
        player_count = int(player_count)
    if player_count <= 4:
        count_range = '2-4'
    else:
        count_range = '5-6'
    
    # Choose course
    with open(r'data\courses.json') as file:
        courses = json.load(file)
    choices = ''
    for i, course in enumerate(courses.keys()):
        choices += str(i+1)
        print(str(i+1) + ' - ' + course)
    chosen_course = getInput('Choose one of the courses above:', choices, 'q')
    if not chosen_course:
        print('Quitting...')
        return
    else:
        course_name = list(courses.keys())[int(chosen_course)-1]
        try:
            course = Course(course_name, count_range)
        except KeyError:
            print(f'{course_name} does not have a version for this player count: {count_range}.')
            # Separate each of these steps in functions so they can be called again

    # Add players
    player_colors = ['blue', 'green', 'red', 'pink', 'white', 'black']
    selected_colors = set()
    for i in range(player_count):
        for I, color in enumerate(player_colors):
            print(I+1, '-', color)
        selected_color = getInput(f'Player {i+1}, select a color above:', [str(i+1) for i, _ in enumerate(player_colors)], 'q')
        if not selected_color:
            print('Quitting...')
            return
        else:
            selected_colors.add(player_colors[int(selected_color)-1])
            # Handle selecting same color twice TO DO
    for color in selected_colors:
        course.addPlayer(color)
    return course


def main():
    course = setUp()
    for player in course.players:
        print(player.__dict__)
    input('')

if __name__ == '__main__':
    main()
