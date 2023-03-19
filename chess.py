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

from typing import Literal, List, Optional
from copy import deepcopy # Used for board copying operations (nested list)
import os # used to clear console after a chess board change
import time
from kivy.app import App
from kivy.uix.widget import Widget
from kivy.graphics import Rectangle, Color
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.core.window import Window

class InvalidMove(Exception):
    pass

class Game:
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
        # modified for testing
        self.board1 = [
            ["BR", "  ", "  ", "  ", "BK", "  ", "  ", "BR"],
            ["BP", "BP", "BP", "BP", "BQ", "BP", "BP", "BP"],
            ["  ", "  ", "  ", "  ", "  ", "  ", "  ", "  "],
            ["  ", "  ", "  ", "  ", "  ", "  ", "  ", "  "],
            ["  ", "  ", "  ", "  ", "  ", "  ", "  ", "  "],
            ["  ", "  ", "  ", "  ", "  ", "  ", "  ", "  "],
            ["WP", "WP", "WP", "WP", "  ", "WP", "WP", "WP"],
            ["WR", "  ", "  ", "WP", "WK", "WP", "  ", "WR"],
        ]
        self.turn = "white"
        self.moves = 0
        self.winner = None
        self.warning = ""
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

    def coords_to_index(self, coords: str, to_return: Literal["int", "str"]="int") -> str | list:
        """
        This function converts coords to index form so it can be
        located in the nested list (board)
        """
        x, y = coords[0], coords[1]
        return [self.letter_match[x], 8 - int(y)] if to_return == "int" else f"{self.letter_match[x]}{8 - int(y)}"

    def index_to_coords(self, index: str):
        return f"{chr(int(index[0])+97)}{8 - int(index[1])}"

    def get_king_coords(self, color: str, board: Optional[List[list]]=None):
        """
        This function gets the coods of the king
        """
        if board is None:
            board = self.board
        for y in range(8):
            for x in range(8):
                if board[y][x] == f"{color}K":
                    return self.index_to_coords(f"{x}{y}")

    def find_pawn_moves(self, color: Literal["W", "B"], piece_x: int, piece_y: int) -> List[str]:
        # Find valid pawn movements
        ret = []
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

        return ret

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

    def find_adj_moves(self, color: Literal["W", "B"], piece_x: int, piece_y: int) -> List[str]:
        ret = []
        for mody in (-1, 0, 1):
            for modx in (-1, 0, 1):
                if mody == 0 and modx == 0: continue
                if 0 <= piece_x+modx < 8 and 0 <= piece_y+mody < 8:
                    if self.board[piece_y+mody][piece_x+modx][0] != color:
                        ret.append(f"{piece_x+modx}{piece_y+mody}")

        return ret

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
            castling = self.castle_status[color]
            num = 7 if color == "W" else 0 # row coord
            # King's side castling (O-O)
            if castling[0] and all(self.board[num][i] == "  " for i in range(5, 7)):
                valid_moves.append(f"6{num} O-O")
            # Queen's side castling (O-O-O)
            if castling[1] and all(self.board[num][i] == "  " for i in range(1, 4)):
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

    def move(self, curr_pos: str, new_pos: str) -> None:
        """
        This function helps move a piece on the board

        curr_pos: the current position of the piece
        new_pos: the new position of the piece
        """

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
                    winner = "W" if color == "B" else "B"
                    print(self.display())
                    print(f"Checkmate!!! {winner} won!")
                    exit()
            return True

        self.warning = "That was an invalid move!"
        raise InvalidMove("Invalid Move!")

    def display(self):
        """
        This function displays the chess board
        """
        # Clear the console
        #os.system("clear")

        # Draw the board
        res = "  " + "-"*41 + "\n"
        for y, row in enumerate(self.board):
            res += f"{8 - y} |"
            for x in self.board[y]:
                res += f" {x} |"
            res += f"\n   {'-'*40} \n"

        letters = ["a", "b", "c", "d", "e", "f", "g", "h"]

        res += "  "
        for letter in letters:
            res += f"   {letter} "
        res += f"\n{self.warning}"
        return res

def main():
    game = Game()

    # Game Loop
    running = True
    while running:
        print(game.display())

        try:
            old, new = input("Enter piece to move: "), input("Enter coords to move to: ")
            letters = [chr(i) for i in range(97, 105)]
            numbers = [str(i) for  i in range(1, 9)]
            # Check if coord is not malformed
            if len(old) == len(new) == 2 and (old[0] in letters and new[0] in letters and old[1] in numbers and new[1] in numbers):
                game.move(old, new)
            else:
                print("Invalid Coords provided")
        except InvalidMove:
            print("Sorry, that was an invalid move!") # doesnt show for now as game.display clears the console

    time.sleep(20)


class Chessboard(Widget):
    def __init__(self, game, **kwargs):
        super().__init__(**kwargs)
        self.game = game
        self.board = game.board
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
            for i in range(8):
                for j in range(8):
                    if (i + j) % 2 == 0:
                        Color(0.98, 0.98, 0.88, 1)  # light square
                    else:
                        Color(0.5, 0.7, 0.4, 1)  # dark square
                    if self.squares[i][j] == self.board[i][j]:
                        rect = Rectangle(pos=(i*pos, j*pos), size=size)
                        self.squares[i][j] = rect
                    else:
                        self.squares[i][j].pos = (i*pos, j*pos)
                        self.squares[i][j].size = size

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
                    self.coords["y"][i] = label
                    self.add_widget(label)
                else:
                    self.coords["y"][i].font_size = coord_size[0]
                    self.coords["y"][i].pos = (0, j*pos+size[1]/1.5)
                    self.coords["y"][i].size = coord_size

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
                    if self.pieces[y][x] == col: # check if pieces store board or btns. if board, it means it hasnt been modified yet
                        button = Button(
                            text=self.board[y][x],
                            font_size=size[0]/2,
                            pos=(x*pos, y*pos),
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
                            self.board[y][x], # text
                            size[0]/2, # font_size
                            (x*pos, y*pos), # pos
                            size, # size
                        )
                        print(self.pieces[y][x])
                        self.pieces[y][x].text, self.pieces[y][x].font_size, self.pieces[y][x].pos, self.pieces[y][x].size = values

    def on_size(self, *args): # this func gets called when screen size changes (i think)
        screen_size = min(args[1])
        print(screen_size)
        size = (screen_size * 0.125, screen_size * 0.125)
        pos_mult = screen_size/8
        self.draw_board(size, pos_mult)
        self.draw_pieces(size, pos_mult)

    def click(self, btn: str):
        if btn.text == "  ": return
        index = None
        print(self.pieces[0][0].text)
        for y, row in enumerate(self.pieces):
            for x, col in enumerate(row):
                if col == btn:
                    index = f"{x}{y}"
                    print(index)
                    break
            if index is not None: break
        square = self.game.index_to_coords(index)
        print(square)
        valid_moves = self.game.get_valid_moves(square)
        print(valid_moves)


class ChessApp(App):
    def build(self):
        game = Game()
        chessgame = Chessboard(game)
        return chessgame

if __name__ == '__main__':
    ChessApp().run()

"""
To-Do:
- En Passant
- Switch between black and white moves
    - disabled for now so it is easier to test stuff!

Bugs:
- Castling:
    - Check if player can castle into check (low chance)
    - Fix player being able to castle out of check
    - Fix player being able to castle the rook into check
- white and black pos are swapped :/
"""