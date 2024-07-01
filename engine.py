import numpy as np
from functools import cache
from itertools import product
from numbers import Integral as int_like
from enum import Enum


class Grid:
    def __init__(self, w: int, h: int):
        assert (w > 0 and h > 0), "incorrect grid dimensions (width and height)"
        self.dims = self.h, self.w = h, w  # rows x cols as numpy shape
        self.coordinates = self.generate_coords(w, h)  # immutable tuples
        self.int_coordinates = tuple(coord[1] * w + coord[0] for coord in self.coordinates)
        # mutable set of coords as integers (indices)
        self.remained_coords = set(self.int_coordinates)

    @staticmethod
    def generate_coords(w, h) -> tuple:
        xs, ys = range(w), range(h)  # can add more dimensions, use numpy
        coords = list(product(xs, ys))
        coords.sort(key=lambda xy: (xy[1], xy[0]))
        return tuple(coords)  # "human-readable" sorted tuple (memoization requires this obj to be hashable)

    @cache
    def translate_coords(self, coord: tuple | int_like = None, rowcol: tuple | None = None) -> int_like | tuple:
        if rowcol is not None:
            return self.translate_coords(coord=rowcol[::-1])  # numpy uses (y, x) for indexing; e.g. (0, 1) to 1
        if isinstance(coord, int_like):
            return divmod(coord, self.w)[::-1]  # int to (x, y); e.g. 0 to (0, 0)
        else:
            return coord[1] * self.w + coord[0]  # (x,y) to int; e.g. (1, 0) to 1

    def get_neighbors(self, coord: tuple[int, int]) -> set[tuple[int, int]]:
        moves = [-1, 1, 0]
        neighbors00 = set(product(moves, repeat=2)) - {(0, 0)}
        neighbors_of_coord = {(x + coord[0], y + coord[1]) for (x, y) in neighbors00}
        valid_neighbors_of_coord = {(x, y) for (x, y) in neighbors_of_coord if (0 <= x < self.w and 0 <= y < self.h)}
        return valid_neighbors_of_coord


class MineField(Grid):
    # Game Engine; unlike Excel, here coords start from 0, 0
    emoticons = Enum('Emoticon', zip(['GAME', 'WAITS', 'WON', 'LOST'], [":)", ":o", "8)", ";("]))

    def __init__(self, w: int, h: int, mines: int | None = None):
        assert (w > 1 or h > 1), "Incorrect minefield dimensions (width and height)"
        if mines is not None:
            assert (w * h > mines), "Incorrect minefield difficulty (mines > cells)"

        super().__init__(w=w, h=h)

        self.n_mines = mines
        self.flags_left = 0
        self.game_over = False
        self.reaction = MineField.emoticons.GAME

    def complete_field_init(self, mines: int | None = None) -> np.ndarray:
        assert (self.n_mines is None) ^ (mines is None), ("Already complete! " if self.n_mines else "") + \
                f"Minefield requires the number of mines, one of {mines=}, {self.n_mines=} "
        if self.n_mines is None:
            self.flags_left = self.n_mines = mines
        mined = self.spread_mines(n_mines=self.n_mines)
        self.mined_set = set(mined)  # indices
        # this is how user sees the grid (starts blank). 0 = empty open, 1 - one mine near, 9 - mine:
        self.visible = np.full(self.w * self.h, ' ')
        self.underneath = np.full(self.w * self.h, 0, dtype=np.uint8)
        self.underneath[mined] = 9  # cell at a max is surrounded by 8 mines, reserve digit 9 for an actual mine itself

        for idx in mined:  # for each mine, increment cell values around it
            mine_coord = self.translate_coords(idx)  # to-do: vectorize
            surrounding = self.get_neighbors(mine_coord)  # valid nearby cells
            surrounding_idxs = {self.translate_coords(xy) for xy in surrounding}
            surrounding_idxs -= self.mined_set
            self.underneath[list(surrounding_idxs)] += 1  # increment nearbies (up to 9, i.e. except for nearby mines)

        self.victorious = np.where(self.underneath == 9, 'f', self.underneath.astype(str))  # all mines flagged
        view_array = self.visible.view().reshape(self.dims)
        view_array.flags.writeable = False
        return view_array

    def spread_mines(self, n_mines: int) -> np.ndarray:
        rng = np.random.default_rng()
        return rng.choice(self.int_coordinates, size=n_mines, replace=False)  # choose cells to plant

    def is_victory(self) -> bool:
        if np.all(self.victorious == self.visible):
            # print("Win!")
            self.reaction = MineField.emoticons.WON
            self.game_over = True
            return True
        return False

    def expand_empty_cells(self, cell_idx: int) -> list[tuple]:
        coord = self.translate_coords(cell_idx)
        # BFS
        visited = set()
        queue_like = [coord]
        qstart = 0
        while qstart < len(queue_like):
            cell_coord = queue_like[qstart]
            qstart += 1
            if cell_coord in visited:
                continue
            else:
                visited.add(cell_coord)
                nearbies_xy = self.get_neighbors(cell_coord) - visited
            for xy in nearbies_xy:
                neighbor_idx = self.translate_coords(xy)
                if self.underneath[neighbor_idx] == 0 and self.visible[neighbor_idx] == ' ':
                    queue_like.append(xy)
                elif self.visible[neighbor_idx] == ' ':
                    queue_like.append(xy)  # reveal 1-8 (9 cannot happen before 1-8, guaranteed to be surrounded by 1-8)
                    visited.add(xy)  # but do not expand, visit neighbors of 1-8
        return queue_like

    def cell_action(self, cell_idx: int, user_input: str) -> list[tuple]:
        # assert len(user_input) < 2, "Invalid input, (f)lag, (?) mark, or (j)ust try!"
        match self.visible[cell_idx], user_input:
            case ('' | ' ' | 'f' | '?') as sees, 'j':  # valid cell chosen (not previously opened 0-8)
                match self.underneath[cell_idx]:
                    case 9:  # end game, show mines (stop time?, change cell color to red?)
                        self.game_over = True
                        self.reaction = MineField.emoticons.LOST
                        self.visible[cell_idx] = 'X'  # to-do: format red bg, exploded mine
                        revealed = [cell_idx]
                        for cell_i in np.where(self.underneath == 9)[0]:  # reveal remaining mined cells
                            if cell_i != cell_idx:
                                if self.visible[cell_i] != 'f':
                                    self.visible[cell_i] = '*'  # "not exploded" mine
                                else:
                                    self.visible[cell_i] = 'F'  # "not exploded" and flagged mine
                                revealed.append(cell_i)
                        return [self.translate_coords(c) for c in revealed]  # reveals all mines
                    case shown_digit if shown_digit != 0:  # cell (1-8) near a mine
                        if sees == 'f':
                            self.flags_left += 1
                        self.visible[cell_idx] = shown_digit  # to-do: select appropriate digit color, darken cell
                        self.is_victory()
                    case 0:
                        squares = self.expand_empty_cells(cell_idx)  # to-do: set digit color (edges), darken all cells
                        idxs = [self.translate_coords(square) for square in squares]
                        self.visible[idxs] = self.underneath[idxs]
                        self.is_victory()
                        return squares

            case (' ' | '?'), 'f':  # the user wants to flag the cell
                self.visible[cell_idx] = 'f'  # add flag, increment flag counter
                self.flags_left -= 1
                self.is_victory()

            case 'f', (' ' | '' | '?') as replaces_flag:
                self.flags_left += 1
                if replaces_flag:
                    self.visible[cell_idx] = replaces_flag or ' '

            case (' ' | '' | '?'), '?':  # user wants to mark non-'f' cell with '?' (cannot mark already opened cell)
                self.visible[cell_idx] = '?'

            case (' ' | '' | '?'), (' ' | ''):  # user wants to clear the ? or already empty cell (sets to empty space)
                self.visible[cell_idx] = ' '

            case _:  # Default case: Do nothing (invalid input)
                pass

        return [self.translate_coords(cell_idx)]
