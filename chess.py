"""
Chess!
Copyright (C) 2023  kitkat3141

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <https://www.gnu.org/licenses/>.
"""

# Remove red dots when user right clicks
from kivy.config import Config
Config.set('input', 'mouse', 'mouse,multitouch_on_demand')

import os   # For executable (_MEIPASS)
import sys  # For executable (_MEIPASS)
import trio # For async code
from copy import deepcopy # Used for board copying operations (nested list)
from typing import Literal, List, Optional
from kivymd.app import MDApp
from kivy.lang import Builder
from kivy.core.window import Window
from kivy.graphics import Rectangle, Color
from kivy.uix.popup import Popup
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.widget import Widget
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.screenmanager import Screen, ScreenManager
from kivy.uix.modalview import ModalView
from kivy.uix.gridlayout import GridLayout
from kivymd.uix.button import MDFlatButton

"""
Error Classes
"""

class InvalidMove(Exception):
    pass

class KingMissing(Exception):
    pass


"""
Chess Game Logic
"""

class Game:
    """
    This class consists of the chess game logic.
    """
    def __init__(self):
        self.board = [
            ["BR", "BN", "BB", "BQ", "BK", "BB", "BN", "BR"],
            ["BP", "BP", "BP", "BP", "BP", "BP", "BP", "BP"],
            ["  ", "  ", "  ", "  ", "  ", "  ", "  ", "  "],
            ["  ", "  ", "  ", "  ", "  ", "  ", "  ", "  "],
            ["  ", "  ", "  ", "  ", "  ", "  ", "  ", "  "],
            ["  ", "  ", "  ", "  ", "  ", "  ", "  ", "  "],
            ["WP", "WP", "WP", "WP", "WP", "WP", "WP", "WP"],
            ["WR", "WN", "WB", "WQ", "WK", "WB", "WN", "WR"],
        ]
        self.turn = "white"
        self.moves = 0
        self.winner = None
        self.warning = ""
        self.pawn_promotion_view = None
        self.wait_for_promotion = trio.Event()
        self.pawn_promoted_to = None
        self.castle_status = {
            "W": [True, True], # O-O, O-O-O
            "B": [True, True]
        }
        self.letter_match = {
            "a": 0,
            "b": 1,
            "c": 2,
            "d": 3,
            "e": 4,
            "f": 5,
            "g": 6,
            "h": 7
        }
        self.pieces = {
            "WQ": "\u2655",
            "WR": "\u2656",
            "WB": "\u2657",
            "WN": "\u2658",

            "BQ": "\u265B",
            "BR": "\u265C",
            "BB": "\u265D",
            "BN": "\u265E",
        }

    def coords_to_index(self, coords: str, to_return: Literal["int", "str"]="int") -> str | list:
        """
        This function converts coords to index form so it can be
        located in the nested list (board)
        """
        x, y = coords[0], coords[1]
        return [self.letter_match[x], 8 - int(y)] if to_return == "int" else f"{self.letter_match[x]}{8 - int(y)}"

    def index_to_coords(self, index: str):
        """
        This function converts board indicies to coordinate form! 
        E.g. "00" -> "a8"
        """
        return f"{chr(int(index[0])+97)}{8 - int(index[1])}"

    def get_king_coords(self, color: str, board: Optional[List[list]]=None):
        """
        This function gets the coods of the king
        Returns "0" if king cannot be found
        """
        if board is None:
            board = self.board
        for y in range(8):
            for x in range(8):
                if board[y][x] == f"{color}K":
                    return self.index_to_coords(f"{x}{y}")
        raise KingMissing("The king cannot be found on the board!")

    def find_pawn_moves(self, color: Literal["W", "B"], piece_x: int, piece_y: int, return_check: bool=False) -> List[str]:
        # Find valid pawn movements
        ret = []
        if not return_check: # if return_check, only check for takes 
            ## Find valid vert movements (1/ 2 up for first move)
            can_move_vertically = False
            # Single vert moves
            new_x, new_y = (piece_x, piece_y+1) if color == "B" else (piece_x, piece_y-1)
            if self.board[new_y][new_x] == "  " and piece_x == new_x:
                can_move_vertically = True
                ret.append(f"{new_x}{new_y}")

            # Double vert moves
            # First, check if the pawn is on it's home square
            if can_move_vertically and ((piece_y == 1 and color == "B") or (piece_y == 6 and color == "W")):
                new_x, new_y = (piece_x, piece_y+2) if color == "B" else (piece_x, piece_y-2)
                if self.board[new_y][new_x] == "  " and piece_x == new_x:
                    ret.append(f"{new_x}{new_y}")

        # Check for diagonal movement
        new_y = piece_y+1 if color == "B" else piece_y-1
        ## Check for left/right diagonals
        for i in (-1, 1):
            new_x = piece_x + i
            if 0 <= new_x < 8:
                if self.board[new_y][new_x][0] == ("W" if color == "B" else "B"):
                    ret.append(f"{new_x}{new_y}")
                    if return_check and self.board[new_y][new_x][1] == "P":
                        return True

        return ret if not return_check else False

    def find_horizontal_moves(self, color: Literal["W", "B"], piece_x: int, piece_y: int, return_check: bool=False) -> List[str] | bool:
        ret = []
        # Check for valid left movements and right movements
        ind = 0
        for movements in (range(1, piece_x + 1), range(1, 8-piece_x)):
            for x in movements:
                new_x = piece_x - x if ind == 0 else piece_x + x

                # Check if potential square is not occupied by your own piece, else stop checking further
                if self.board[piece_y][new_x][0] != color:
                    ret.append(f"{new_x}{piece_y}")

                    # If that spot is occupied by opponent's piece, stop checking for moves further along axis
                    if self.board[piece_y][new_x][0] == ("W" if color == "B" else "B"):
                        if return_check and self.board[piece_y][new_x][1] in ["R", "Q"]:
                            return True
                        break
                else:
                    break

            ind += 1
        return ret if not return_check else False

    def find_vertical_moves(self, color: Literal["W", "B"], piece_x: int, piece_y: int, return_check: bool=False) -> List[str] | bool:
        ret = []
        # Check for valid up movements and down movements
        ind = 0
        for movements in (range(1, piece_y + 1), range(1, 8-piece_y)):
            for y in movements:
                new_y = piece_y - y if ind == 0 else piece_y + y

                # Check if potential square is not occupied by your own piece, else stop checking further
                if self.board[new_y][piece_x][0] != color:
                    ret.append(f"{piece_x}{new_y}")

                    # If that spot is occupied by opponent's piece, stop checking for moves further along axis
                    if self.board[new_y][piece_x][0] == ("W" if color == "B" else "B"):
                        if return_check and self.board[new_y][piece_x][1] in ["R", "Q"]:
                            return True
                        break
                else:
                    break

            ind += 1
        return ret if not return_check else False

    def find_diagonal_moves(self, color: Literal["W", "B"], piece_x: int, piece_y: int, return_check: bool=False) -> List[str] | bool:
        ret = []
        for y in (-1, 1):
            for x in (-1, 1):
                modx, mody = x, y
                while 0 <= piece_x+modx < 8 and 0 <= piece_y+mody < 8:
                    if self.board[piece_y+mody][piece_x+modx][0] != color:
                        ret.append(f"{piece_x+modx}{piece_y+mody}")

                        # If that spot is occupied by opponent's piece, stop checking for moves further along axis
                        if self.board[piece_y+mody][piece_x+modx][0] == ("W" if color == "B" else "B"):

                            if return_check and self.board[piece_y+mody][piece_x+modx][1] in ["B", "Q"]:
                                return True
                            break
                    else:
                        break

                    modx += x
                    mody += y

        return ret if not return_check else False

    def find_knight_moves(self, color: Literal["W", "B"], piece_x: int, piece_y: int, return_check: bool=False) -> List[str] | bool:
        ret = []
        for mody in (-2, -1, 1, 2):
            for modx in (-2, -1, 1, 2):
                if 0 <= piece_x+modx < 8 and 0 <= piece_y+mody < 8:
                    if abs(modx) == abs(mody): continue # Skip check if x and y change is same because only L shaped movements should be checked
                    if self.board[piece_y+mody][piece_x+modx][0] != color:
                        ret.append(f"{piece_x+modx}{piece_y+mody}")
                        if return_check and self.board[piece_y+mody][piece_x+modx][1] == "N":
                            return True

        return ret if not return_check else False

    def find_adj_moves(self, color: Literal["W", "B"], piece_x: int, piece_y: int, return_check: bool=False) -> List[str]:
        ret = []
        for mody in (-1, 0, 1):
            for modx in (-1, 0, 1):
                if mody == 0 and modx == 0: continue
                if 0 <= piece_x+modx < 8 and 0 <= piece_y+mody < 8:
                    if self.board[piece_y+mody][piece_x+modx][0] != color:
                        ret.append(f"{piece_x+modx}{piece_y+mody}")
                        if return_check and self.board[piece_y+mody][piece_x+modx][1] == "K":
                            return True

        return ret if not return_check else False

    def is_in_check(self, color: Literal["W", "B"], piece_x: int, piece_y: int, temp_board: Optional[List[list]]=None) -> bool:
        """
        This function checks if a "potential" position
        on the board is threatened.
        Will be used for kind movements and castling to ensure the
        players don't castle into check ect.
        """
        original_board = deepcopy(self.board)
        if temp_board is None: temp_board = self.board
        self.board = deepcopy(temp_board)
        in_check = []
        in_check.append(self.find_horizontal_moves(color, piece_x, piece_y, True))
        in_check.append(self.find_vertical_moves(color, piece_x, piece_y, True))
        in_check.append(self.find_diagonal_moves(color, piece_x, piece_y, True))
        in_check.append(self.find_knight_moves(color, piece_x, piece_y, True))
        in_check.append(self.find_adj_moves(color, piece_x, piece_y, True))
        in_check.append(self.find_pawn_moves(color, piece_x, piece_y, True))
        self.board = original_board
        return True if True in in_check else False

    def get_valid_moves(self, curr_pos: str) -> list:
        """
        Returns a list of all valid moves the piece can make. (In list index format)
        """
        piece_x, piece_y = self.coords_to_index(curr_pos)
        piece = self.board[piece_y][piece_x]
        color = piece[0]
        valid_moves = []

        if piece[0] not in ("W", "B"):
            raise InvalidMove

        # Check for valid pawn movement
        if piece[-1] == "P": # "P" in "WP"
            valid_moves += self.find_pawn_moves(piece[0], piece_x, piece_y)

        # Check for rook movement
        if piece[-1] == "R":
            valid_moves += self.find_horizontal_moves(piece[0], piece_x, piece_y)
            valid_moves += self.find_vertical_moves(piece[0], piece_x, piece_y)

        # Check for knight movement
        if piece[-1] == "N":
            valid_moves += self.find_knight_moves(piece[0], piece_x, piece_y)

        # Check for bishop movement
        if piece[-1] == "B":
            valid_moves += self.find_diagonal_moves(piece[0], piece_x, piece_y)

        if piece[-1] == "Q":
            valid_moves += self.find_horizontal_moves(piece[0], piece_x, piece_y)
            valid_moves += self.find_vertical_moves(piece[0], piece_x, piece_y)
            valid_moves += self.find_diagonal_moves(piece[0], piece_x, piece_y)

        if piece[-1] == "K":
            valid_moves += self.find_adj_moves(piece[0], piece_x, piece_y)
            # Check if player is allowed to castle
            """
            Castle status is defined as such:
            self.castle_status = {
            "W": [O-O: bool, O-O-O: bool],
            "B": ...
            }
            """
            if not self.is_in_check(color, piece_x, piece_y): # king cannot castle if in check!
                castling = self.castle_status[color]
                num = 7 if color == "W" else 0 # row coord
                # King's side castling (O-O)
                if not self.is_in_check(color, 5, num) and castling[0] and all(self.board[num][i] == "  " for i in range(5, 7)) and self.board[num][7] == f"{color}R":
                    valid_moves.append(f"6{num} O-O")
                # Queen's side castling (O-O-O)
                if not self.is_in_check(color, 3, num) and castling[1] and all(self.board[num][i] == "  " for i in range(1, 4)) and self.board[num][0] == f"{color}R":
                    valid_moves.append(f"2{num} O-O-O")

        # Check if king is in check.
        for move in valid_moves.copy():
            x, y = int(move[0]), int(move[1])
            temp_board = deepcopy(self.board)
            temp_board[piece_y][piece_x] = "  "
            temp_board[y][x] = piece
            king_pos = self.coords_to_index(self.get_king_coords(piece[0], temp_board))
            if self.is_in_check(piece[0], king_pos[0], king_pos[1], temp_board):
                valid_moves.remove(move)


        print("Valid Moves:", [self.index_to_coords(i) for i in valid_moves])
        return valid_moves
    
    def select_piece(self, button):
        self.pawn_promotion_view.dismiss()
        self.pawn_promoted_to = list(self.pieces)[list(self.pieces.values()).index(button.text)]
        self.wait_for_promotion.set()

    def prompt_for_promotion(self, color: Literal["W", "B"]) -> Literal["Q", "R", "B", "N"] | None:
        """
        Open a ModalView to prompt for pawn promotion piece choice
        """
        print("Prompting for pawn promotion!")
        if not self.pawn_promotion_view:
            box = GridLayout(rows=4, cols=1)
            box.add_widget(MDFlatButton(text=self.pieces["WQ"], on_release=self.select_piece))
            box.add_widget(MDFlatButton(text=self.pieces["WR"], on_release=self.select_piece))
            box.add_widget(MDFlatButton(text=self.pieces["WB"], on_release=self.select_piece))
            box.add_widget(MDFlatButton(text=self.pieces["WN"], on_release=self.select_piece))
            self.pawn_promotion_view = ModalView(
                size_hint=(None, None),
                size=(75, 310),
                background_color=(255, 255, 255, 1),
                overlay_color=(0, 0, 0, 0.4),
                padding=5
                )
            self.pawn_promotion_view.add_widget(box)
        self.pawn_promotion_view.open()

    async def move(self, curr_pos: str, new_pos: str) -> None:
        """
        This function helps move a piece on the board

        curr_pos: the current position of the piece
        new_pos: the new position of the piece
        """
        self.pawn_promotion = False
        # Get the piece type based on curr_pos (WR, WN, BP, etc)
        # Get x and y pos of pieces
        piece_x, piece_y = self.coords_to_index(curr_pos)
        new_x, new_y = self.coords_to_index(new_pos)
        # Reset warning
        self.warning = ""

        piece_type = self.board[piece_y][piece_x]
        color = piece_type[0]

        valid_moves = self.get_valid_moves(curr_pos)
        castling_moves = [i[:2] for i in valid_moves if len(i) > 2]

        # Get ready to move piece
        pos = self.coords_to_index(new_pos, to_return="str")
        if pos in [i[:2] for i in valid_moves]:
            # If rook/king moves, make castling illegal
            if piece_type[1] == "R":
                num = "1" if color == "W" else "8"
                # O-O-O
                if self.board[8-int(num)][self.coords_to_index(f"a{num}")[0]] == "  ":
                    self.castle_status[color][1] = False
                # O-O
                if self.board[8-int(num)][self.coords_to_index(f"h{num}")[0]] == "  ":
                    self.castle_status[color][0] = False
            if piece_type[1] == "K":
                self.castle_status[piece_type[0]] = [False, False]
            # Check for pawn promotion
            num = 0 if color == "W" else 7
            print(num, new_y)
            if piece_type[1] == "P" and new_y == num:
                self.pawn_promotion = True
                
            self.args_to_pass = piece_x, piece_y, new_x, new_y, piece_type, pos, castling_moves, color
            if self.pawn_promotion:
                self.pawn_promoted_to = None
                self.wait_for_promotion = trio.Event()
                self.prompt_for_promotion(color)
                await self.wait_for_promotion.wait()
            
            # Check pawn promotion
            if self.pawn_promoted_to is not None:
                piece_type = self.pawn_promoted_to

            # Move piece
            self.board[piece_y][piece_x] = "  "
            self.board[new_y][new_x] = piece_type
            # Check if move is a castling move
            if pos in castling_moves:
                self.board[new_y][new_x+1 if pos[0] < "4" else new_x-1] = f"{color}R"
                self.board[new_y][0 if pos[0] < "4" else 7] = "  "
                # mark castling as illegal now
                self.castle_status[color] = [False, False]

            # Check if opponent has ANY valid moves
            color = "W" if color == "B" else "B"
            has_valid_moves = False
            king_pos = self.coords_to_index(self.get_king_coords(color))
            if self.is_in_check(color, king_pos[0], king_pos[1]):
                for y, row in enumerate(self.board):
                    for x, col in enumerate(row):
                        if col[0] == color and self.get_valid_moves(self.index_to_coords(f"{x}{y}")) != []:
                            has_valid_moves = True
                            break
                if not has_valid_moves:
                    winner = "White" if color == "B" else "Black"
                    return winner
            return True
    


"""
Game GUI code below!
"""

def resource_path(relative_path):
    """
    PyInstaller creates a temp folder and stores path in _MEIPASS
    This function tries to find that path 

    Note: This function is for EXEs. Feel free to remove it when compiling it to APKs.
    """

    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")

    return os.path.join(base_path, relative_path)

class WindowManager(ScreenManager):
    pass

class WelcomeWindow(Screen):
    pass


class GameWindow(Screen):
    def on_enter(self):
        game = Game()
        chessgame = Chessboard(game)
        self.add_widget(chessgame)


class Chessboard(Widget):
    def __init__(self, game, **kwargs):
        super().__init__(**kwargs)
        self.game = game
        self.board = game.board
        self.selected = ""
        self.pawn_promotion_view = None
        self.piece_map = {
            "WK": "\u2654",
            "WQ": "\u2655",
            "WR": "\u2656",
            "WB": "\u2657",
            "WN": "\u2658",
            "WP": "\u2659",
            "BK": "\u265A",
            "BQ": "\u265B",
            "BR": "\u265C",
            "BB": "\u265D",
            "BN": "\u265E",
            "BP": "\u265F",
            "  ": "  "
        }
        self.valid_moves = []
        self.pieces = deepcopy(self.board)
        self.squares = deepcopy(self.board) # to store pos of board squares
        self.coords = {
            "y": [i for i in range(1, 9)], # [1, 2, ...]
            "x": [chr(i) for i in range(97, 105)] # ["a", "b", ...]
        }

    def draw_board(self, size, pos):
        coord_size = size[0]/4, size[1]/4
        with self.canvas:
            # Draw board squares
            for y in range(8):
                for x in range(8):
                    if (x + y) % 2 == 0:
                        Color(0.98, 0.98, 0.88, 1)  # light square
                    else:
                        Color(0.5, 0.7, 0.4, 1)  # dark square
                    
                    final_pos = (
                        x*pos + Window.size[0]//2 - size[0]*4,
                        y*pos + Window.size[1]//2 - size[1]*4
                        )
                    if self.squares[y][x] == self.board[y][x]:
                        rect = Rectangle(pos=final_pos, size=size)
                        self.squares[y][x] = rect
                    else:
                        self.squares[y][x].pos = final_pos
                        self.squares[y][x].size = size

            # Draw row indices
            for j in range(8):
                if self.coords["y"][7] == 8:
                    label = Label(
                        text=str(j+1),
                        font_size=coord_size[0],
                        pos=(0, j*pos+size[1]/1.5),
                        size=coord_size,
                        halign="center",
                        valign="middle",
                        color=(0, 0, 0, 1)
                        )
                    self.coords["y"][j] = label
                    self.add_widget(label)
                else:
                    self.coords["y"][j].font_size = coord_size[0]
                    self.coords["y"][j].pos = (0, j*pos+size[1]/1.5)
                    self.coords["y"][j].size = coord_size

            # Draw column indices
            for i, col in enumerate("abcdefgh"):
                if self.coords["x"][-1] == "h":
                    label = Label(
                        text=col,
                        font_size=coord_size[0],
                        pos=(i*pos+size[0]/1.33, 0),
                        size=coord_size,
                        halign="center",
                        valign="middle",
                        color=(0, 0, 0, 1)
                        )
                    self.coords["x"][i] = label
                    self.add_widget(label)
                else:
                    self.coords["x"][i].font_size = coord_size[0]
                    self.coords["x"][i].pos = (i*pos+size[0]/1.33, 0)
                    self.coords["x"][i].size = coord_size

    def draw_pieces(self, size, pos):
        """
        todo: add the ability to remove/add a single chess piece
        """
        with self.canvas:
            for y, row in enumerate(self.board):
                for x, col in enumerate(row):
                    final_pos = (
                        x*pos + Window.size[0]//2 - size[0]*4,
                        (7-y)*pos + Window.size[1]//2 - size[1]*4
                        )
                    if self.pieces[y][x] == col: # check if pieces store board or btns. if board, it means it hasnt been modified yet
                        button = Button(
                            text=self.piece_map[self.board[y][x]],
                            font_name="DejaVuSans",
                            font_size=min(size[0]/1.5, 60),
                            pos=final_pos, # display fix
                            size=size,
                            halign="center",
                            valign="middle",
                            color=(0, 0, 0, 1),
                            background_color=(0, 0, 0, 0)
                            )
                        button.bind(on_release=self.click)
                        self.pieces[y][x] = button
                        self.add_widget(button)
                    else:
                        values = (
                            self.piece_map[self.board[y][x]], # text
                            min(size[0]/1.5, 60), # font_size
                            final_pos, # pos
                            size, # size
                        )
                        self.pieces[y][x].text, self.pieces[y][x].font_size, self.pieces[y][x].pos, self.pieces[y][x].size = values

    def on_size(self, *args): # this func gets called when screen size changes (i think)
        """
        Whenever the screen size is changed or the board needs updating,
        this function gets called.

        Handles screen updates
        """
        if args != ():
            screen_size = min(args[1])
        else:
            screen_size = min(Window.size)
        size = (screen_size * 0.125, screen_size * 0.125)
        pos_mult = screen_size/8
        self.board = self.game.board
        self.draw_board(size, pos_mult)
        self.draw_pieces(size, pos_mult)

    def click(self, btn: str):
        """
        This event gets called when piece is selected.
        This will start a trio task to enable async behaviour!
        """
        inst.nursery.start_soon(self.async_click, btn)
        
    async def async_click(self, btn: str):
        """
        Handles piece selection
        """
        index = None
        for y, row in enumerate(self.pieces):
            for x, col in enumerate(row):
                if col == btn:
                    index = f"{x}{y}"
                    break
            if index is not None: break
        square = self.game.index_to_coords(index)
        valid_moves = []
        if btn.text != "  ": 
            valid_moves = self.game.get_valid_moves(square)
            valid_moves = [self.game.index_to_coords(ind) for ind in valid_moves]

        if btn.text != "  " and square not in self.valid_moves:
            self.selected = square
            self.valid_moves = valid_moves

        elif btn.text == "  " and self.selected == "":
            pass

        else:
            if square in self.valid_moves:
                try:
                    movement = await self.game.move(self.selected, square) # returns color if there is a winner
                    print("movement:", movement)
                    if movement in ("White", "Black"):
                        winner = movement
                        print(f"Checkmate!!! {winner} won!")

                        content = BoxLayout(orientation="vertical")

                        close_popup = Button(text="Close")
                        win_msg = Label(text=f"{winner} won by checkmate!")

                        content.add_widget(win_msg)
                        content.add_widget(close_popup)

                        winner_popup = Popup(
                            title=f"{winner} wins",
                            title_align="center",
                            title_size=Window.size[0]*0.05,
                            content=content,
                            size_hint=(0.7, 0.5)
                        )
                        close_popup.bind(on_press=winner_popup.dismiss)
                        winner_popup.open()

                except InvalidMove:
                    pass
                self.on_size()

            self.selected = ""
            self.valid_moves = []
        
        valids = [self.game.coords_to_index(i) for i in self.valid_moves]
        for y, row in enumerate(self.squares):
            for x, col in enumerate(row):
                if [x, y] in valids:
                    self.squares[7-y][x].source = resource_path(f"assets/move_indicator.jpg")
                else:
                    self.squares[7-y][x].source = None


class ChessApp(MDApp):
    def __init__(self, nursery):
        super().__init__()
        self.nursery = nursery

    def build(self):
        self.use_kivy_settings = False # to be used in the future!
        self.theme_cls.theme_style = "Dark"
        kv = Builder.load_file(resource_path("chess.kv"))
        return kv
    
inst = None
async def main():
    global inst
    async with trio.open_nursery() as nursery:
        inst = ChessApp(nursery)
        await inst.async_run(async_lib="trio") # start app!
        nursery.cancel_scope.cancel()
    
if __name__ == '__main__':
    trio.run(main)

"""
To-Do:
- En Passant
- Switch between black and white moves
    - disabled for now so it is easier to test stuff!
- Add stalemate. (game currently just does not allow the player to move)
- Make move indicator smaller
- If piece can be taken, change move indicator shape to a grey square with transparent circle in the center
- Make board centered on screen
- Make pawn promotion GUI dynamically sized

Verified Bugs:
- 

Unverified Bugs:
-

"""