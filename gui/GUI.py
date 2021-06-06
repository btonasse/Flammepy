from tkinter import Tk, Frame, Canvas
from main import Tile, Space, Course, Player, Rider
import gui.geometry as geo # Import geometry functions

class App(Tk):
    '''
    Main class
    '''
    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.title('Flamme Rouge')
        self.geometry('1280x960')
        self.rowconfigure(0, weight=1)
        self.columnconfigure(0, weight=1)
        self.mainframe = MainFrame(self, bg='cyan')
        self.mainframe.grid(row=0, column=0, sticky='nsew')
    
    def run(self) -> None:
        self.mainloop()


class MainFrame(Frame):
    '''
    Main application frame
    '''
    def __init__(self, master, *args, **kwargs) -> None:
        super().__init__(master=master, *args, **kwargs)
        self.master = master
        self.left_pane = Frame(self, bg='green')
        self.board_pane = Frame(self, bg='yellow')
        self.bot_pane = Frame(self, bg='red')
        
        self.board = Board(self.board_pane, bg='white', highlightthickness=0)
        self.showWidgets()

    def showWidgets(self) -> None:
        self.rowconfigure(0, weight=3)
        self.rowconfigure(1, weight=1)
        self.columnconfigure(0, weight=1)
        self.columnconfigure(1, weight=4)
        self.left_pane.grid(row=0, column=0, sticky='nsew')
        self.board_pane.grid(row=0, column=1, sticky='nsew')
        self.bot_pane.grid(row=1, column=0, columnspan=2, sticky='nsew')

        self.board.pack(fill="both", expand=True, padx=2, pady=2)

class Board(Canvas):
    '''
    Main board
    '''
    SPACE_W = 30
    SPACE_H = 50
    def __init__(self, master, *args, **kwargs) -> None:
        super().__init__(master=master, *args, **kwargs)
        self.master = master
        self.shapes = [] #List of all shape objects
        self.bind('<Button-1>', self.test)

    def test(self, event):
        if not self.shapes:
            first_pol = self.buildStraightTile([event.x, event.y], 6)
            first_pol_rotated = geo.rotatePolygon(first_pol, 0) 
            self.createPolygon(first_pol_rotated, 'straight') 
        else:
            self.createPolygon(self.fitPolygon(self.shapes[-1], 'sharp_corner'), 'sharp_corner', outline='blue')
            self.createPolygon(self.fitPolygon(self.shapes[-1], 'wide_corner'), 'wide_corner', outline='blue')
            self.createPolygon(self.fitPolygon(self.shapes[-1], 'straight'), 'straight', outline='blue')

    def createPolygon(self, coords: list, typ: str, fill: str = '', outline: str = 'black') -> 'Shape':
        '''
        Draws a polygon and returns it as a Shape object
        '''
        shapeid = self.create_polygon(*coords, fill=fill, outline=outline)
        shape = Shape(shapeid, coords, typ)
        self.shapes.append(shape)
        return shape

    def fitPolygon(self, shape: 'Shape', typ: str, spaces: int = 6) -> list:
        '''
        Given a starting shape, generates coordinates of another one that fits right after it
        '''
        # Get origin shape inclination
        inclination = geo.getInclination(shape.end_line[1], shape.end_line[0], True)

        # Build a horizontal polygon starting from shape.end_line[0]
        if typ == 'straight':
            new_coords_horizontal = self.buildStraightTile(shape.end_line[0], spaces)
        elif typ == 'sharp_corner':
            new_coords_horizontal = self.buildSharpCornerTile(shape.end_line[0])
        elif typ == 'wide_corner':
            new_coords_horizontal = self.buildWideCornerTile(shape.end_line[0])

        # Rotate coordinates to match origin's inclination.
        new_coords_rotated = geo.rotatePolygon(new_coords_horizontal, inclination, shape.end_line[0])

        # Check if any resulting coordinate is outside the canvas
        for coord in geo.flatToTupleCoords(new_coords_rotated):
            if any(c < 0 for c in coord) or coord[0] >= self.winfo_width() or coord[1] >= self.winfo_height():
                raise ValueError("Can't create object outside canvas")

        return new_coords_rotated

    
    def buildWideCornerTile(self, root_coord: list, flipped: bool = False) -> list:
        '''
        Takes a root coord and generates a wide corner (45/135 degrees) with two spaces
        '''
        # Build two straight tiles of size 2
        s1 = self.buildStraightTile(root_coord, 2)
        s2 = self.buildStraightTile(s1[2:4], 2)
        # Calculation variables
        theta = 45 
        sin_45 = 0.7071067811865476
        pivot_point = s2[:2]
        coord_to_offset = 8 # By default, 5th vertex will be shortened to account for the intersection of the two tiles
        # If building a flipped polygon, modify variables accordingly
        if flipped:
            theta *= -1
            pivot_point = s2[6:8]
            coord_to_offset = 2
        # Rotate second tile
        s2_rotated = geo.rotatePolygon(s2, theta, pivot_point)
        # Merge first tile with two rotated vertices
        new_coords = s1[:4] + s2_rotated[2:6] + s1[4:]
        # Offset necessary for the 5th vertex of resulting polygon to be at the intersection of the two tiles
        offset = self.SPACE_H/sin_45 - self.SPACE_H
        # Adjust 5th vertex with the offset x value
        new_coords[coord_to_offset] -= offset
        return new_coords

    def buildSharpCornerTile(self, root_coord: list, flipped: bool = False) -> list:
        '''
        Takes a root coord and generates a sharp corner with two spaces
        '''
        # Initialize return variable
        final_coords = [root_coord[0], root_coord[1]]

        final_coords.append(root_coord[0] + self.SPACE_W+self.SPACE_H)
        final_coords.append(root_coord[1])
        final_coords.append(root_coord[0] + self.SPACE_W+self.SPACE_H)
        final_coords.append(root_coord[1] + self.SPACE_W+self.SPACE_H)
        final_coords.append(root_coord[0] + self.SPACE_W)
        final_coords.append(root_coord[1] + self.SPACE_W+self.SPACE_H)
        final_coords.append(root_coord[0] + self.SPACE_W)
        final_coords.append(root_coord[1] + self.SPACE_H)
        final_coords.append(root_coord[0])
        final_coords.append(root_coord[1] + self.SPACE_H)

        if flipped:
            # Swap 2nd and 5th vertices' x value
            final_coords[2], final_coords[8] = final_coords[8], final_coords[2]
            # Flip 3rd and 4th vertices upwards
            final_coords[5] = final_coords[11] - (final_coords[5]-final_coords[1])
            final_coords[7] = final_coords[1] - (final_coords[7]-final_coords[11])
            # Swap 3nd and 4th vertices' x value
            final_coords[4], final_coords[6] = final_coords[6], final_coords[4]

        return final_coords

    def buildStraightTile(self, root_coord: list, spaces: int = 6) -> list:
        '''
        Takes a root coord and a number of spaces and return a flat list of vertices
        '''
        # Initialize return variable
        final_coords = [root_coord[0], root_coord[1]]
        
        # Get other coords
        x2 = root_coord[0] + self.SPACE_W*spaces
        y2 = root_coord[1]
        x3 = root_coord[0] + self.SPACE_W*spaces
        y3 = root_coord[1] + self.SPACE_H
        x4 = root_coord[0]
        y4 = root_coord[1] + self.SPACE_H
        
        final_coords.extend([x2,y2,x3,y3,x4,y4])
        
        return final_coords    

class Shape():
    '''
    Every polygon drawn on the canvas
    '''
    def __init__(self, id: int, coords: list, typ: str) -> None:
        self.id = id
        self.coords = coords
        self.type = typ
        self.root_coord = coords[0:2]
        # The line whose inclination will determine the inclination of the next shape (will change depending on type)
        if self.type == 'straight':
            self.end_line = [coords[2:4], coords[4:6]] 
        elif self.type in ['sharp_corner', 'wide_corner']:
            self.end_line = [coords[4:6], coords[6:8]] 
        

    def __repr__(self) -> str:
        return f"<Shape id={self.id} | coords={self.coords}"



if __name__ == '__main__':
    app = App()
    app.mainloop()