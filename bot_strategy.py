import numpy as np
from random import choice
from collections import defaultdict

from engine import Grid


def demo_bot(visible_grid: np.ndarray, mines_left: int, grid_methods: Grid) -> tuple[int, str]:
    """
    Returns a move (cell index and open/flag action) in a game of minesweeper.
    Markovian approach, simulating a human player by estimating probabilities p of mines in each cell and returning the
     cell with the closest to 0 or 1 (lowest or highest), choosing randomly if > 1 with same p, unless function
     terminates early (finding certain, p=0 or p=1). Function first traverses all cells to obtain initial ps for empty
     ones, and in particular empty neighbours of cells with known digits (subtracting number of nearby flags from them).
     It also iterates over pairs and checks sets of empty neighbours for obvious placement. It also has some simplest
     back-tracking in case grid is filled but game isn't over (to-do: proper one).
    :param visible_grid: numpy 2D-array, where str (object) elements represent visible minefield to a player:
        digits '1'-'8' mean nearby N of mines, player-placed flags are 'f', and empty cells are ' ' or ''.
    :param mines_left: number of mines known to be left on the grid, i.e. = initial N of mines - number of placed flags
    :param grid_methods: Grid object with helper functions, see engine.py.
    :return: int cell index (from 0, which is always a top-left cell) and str 'f' flag or 'j' jump/open action.
    """
    rowcol_arr = np.fromiter(np.ndindex(visible_grid.shape), dtype=object).reshape(visible_grid.shape)
    coords_arr = np.fromiter(grid_methods.coordinates, dtype=object).reshape(visible_grid.shape)
    # 2D array like grid (x, y) but with numpy (y, x)  "coordinates" (row, col)
    probs = np.full_like(visible_grid, np.nan, dtype=float)
    is_empty = np.isin(visible_grid, ['', ' '])
    is_flagged = visible_grid == 'f'
    nempty = is_empty.sum()
    if nempty == 0:  # bot filled the whole grid but game is not over -> to-do: proper back-track
        all_flagged_coords = np.extract(is_flagged, coords_arr)
        flagged_coord_to_open = choice(all_flagged_coords)  # random back-track for now (opens randomly one past flag)
        return grid_methods.translate_coords(flagged_coord_to_open), "j"
    near_digits = defaultdict(set)  # digit cell (x, y) and its N neighbors [(x_ni, y_ni)]
    digits = {}  # will update surrounding mine number here based on actual nearby cells
    for coord, rowcol in zip(coords_arr.flatten(), rowcol_arr.flatten()):
        if is_empty[rowcol]:
            p = mines_left / nempty
            if p >= 1.0:  # early stop and flag mine if obvious
                return grid_methods.translate_coords(coord), "f"
            elif p <= 0.0:
                return grid_methods.translate_coords(coord), "j"
            probs[rowcol] = np.nanmax((p, probs[rowcol]))  # "default" or larger p
        elif visible_grid[rowcol] != 'f':  # is digit str
            digit = int(visible_grid[rowcol])
            empty_neighbors = []
            for c in grid_methods.get_neighbors(coord):
                rc = c[::-1]  # translate coordinate (x, y) to numpy row-column index (y, x)
                if is_empty[rc]:
                    near_digits[rowcol].add(rc)  # all neighbors
                    empty_neighbors.append(rc)  # current
                elif is_flagged[rc]:
                    digit -= 1  # mines left = the digit - known mines (flagged f)
            digits[rowcol] = max(digit, 0)
            for rc in empty_neighbors:
                if (p := digit / len(empty_neighbors)) >= 1.0:
                    return grid_methods.translate_coords(rowcol=rc), "f"
                elif p <= 0.0:
                    return grid_methods.translate_coords(rowcol=rc), "j"
                probs[rc] = np.nanmax((p, probs[rc]))  # update if larger p (in case already was visited)

    certain = _do_empty_neighbor_sets_of_digit_pairs(empty_neighbors=near_digits, digits=digits)
    if certain:
        rc, action = certain
        return grid_methods.translate_coords(rowcol=rc), action

    return _pick_most_probable(probs)


def _pick_most_probable(probs: np.ndarray) -> tuple[int, str]:
    # select from probabilities (minefield-shaped array) the closest to the bounds 0 or 1:
    most_obvious = np.nanmax(np.abs(probs - 0.5))  # its centered (subtracted 0.5) absolute value that is closest to 0.5
    most_obvious_idxs = np.where(np.isclose(np.abs(probs - 0.5).flatten(), most_obvious))[0]

    idx = choice(most_obvious_idxs)
    action = "j" if (probs.flatten()[idx] - 0.5) <= 0 else "f"  # least (most) likely to have a mine => flag (open)

    return idx, action


def _do_empty_neighbor_sets_of_digit_pairs(empty_neighbors: dict, digits: dict) -> tuple[tuple, str] | None:
    """Iterate over every possible pair of digits (updated values given number of flags around), checking for possible
       unfilled neighbor sets intersections (of not too distant digit cells) and return if certain (mine or not). """
    for i, digit_a_rc in enumerate(empty_neighbors):
        for j, digit_b_rc in enumerate(empty_neighbors):
            if j > i:  # skip checked pairs
                digit_a = digits[digit_a_rc]
                digit_b = digits[digit_b_rc]
                neighbs_a_set = empty_neighbors[digit_a_rc]
                neighbs_b_set = empty_neighbors[digit_b_rc]
                if (digit_a - digit_b) == len(neighbs_a_set - neighbs_b_set):
                    rc_to_flag = tuple(neighbs_a_set - neighbs_b_set)
                    rc_to_open = tuple(neighbs_b_set - neighbs_a_set)
                    if rc_to_flag:
                        return choice(rc_to_flag), "f"
                    if rc_to_open:
                        return choice(rc_to_open), "j"
    return None
