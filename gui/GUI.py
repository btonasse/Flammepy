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
        self.geometry('1024x768')
        self.mainframe = MainFrame(self, bg='cyan')
        
    
    def run(self) -> None:
        self.rowconfigure(0, weight=1)
        self.columnconfigure(0, weight=1)
        self.mainframe.grid(row=0, column=0, sticky='nsew')
        self.mainloop()


class MainFrame(Frame):
    '''
    Main application frame
    '''
    def __init__(self, master, *args, **kwargs):
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
    def __init__(self, master, *args, **kwargs):
        super().__init__(master=master, *args, **kwargs)
        self.master=master


if __name__ == '__main__':
    app = App()
    app.mainloop()