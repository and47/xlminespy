import time
from engine import MineField, Grid
from typing import Callable


class MVC_Mines_Controller:

    def __init__(self, cols: int, rows: int, mines: int, engine: 'MineSweeperModel', ui: 'MineSweeperView'):
        self.model = engine(w=cols, h=rows)
        self.players_view = self.model.complete_field_init(int(mines))
        self.view = ui(cols, rows, content_view=self.players_view)
        self.flags_left = self.view.flag_counter = self.model.flags_left
        self.displayed_grid = self.view.format_grid()
        # print(model.underneath.reshape((rows, cols)))  # debug

    @classmethod
    def from_CLI_settings(cls, ui: 'MineSweeperView', engine: 'MineSweeperModel' = MineField) -> 'MVC_Mines_Controller':
        print("Excel controls. After setting difficulty here:")
        print("1) Select a cell on the grid using the arrow keys.")
        print("2) Enter a symbol: j to click/open selected cell, f to (f)lag mine, or ? to mark for yourself.\n\n")
        difficulty = 0
        while not difficulty:
            difficulty = input("Select difficulty (1 - Beginner, 2 - Normal, 3 - Expert, 0 - Custom: ")
        rows, cols, mines = {
            1: (9, 9, 10),
            2: (16, 16, 40),
            3: (16, 30, 99),
        }.setdefault(int(difficulty), (0, 0, 0))

        while not rows:
            rows = input("Enter the number of rows: ")
        while not cols:
            cols = input("Enter the number of columns: ")
        cols, rows = int(cols), int(rows)

        while not mines:
            mines = input("Enter the number of mines: ")  # to-do move game creation into Excel (take all from cells)

        return cls(cols=cols, rows=rows, mines=mines, engine=engine, ui=ui)

    def start_game(self, bot_strategy: Callable | None = None):
        model, view = self.model, self.view  # shorten names
        get_move = self.get_user_move if bot_strategy is None else self._feed(bot_strategy)
        starting_time = time.time()

        while not model.game_over:  # make a generator loop?
            move = get_move()
            if move:
                changed_cell_idx, changed_cell_val = move
                affected_cells = model.cell_action(cell_idx=changed_cell_idx, user_input=changed_cell_val)
                if affected_cells:  # universal engine, in other games may be used, in minesweeper always True
                    view.flag_counter, view.smile = model.flags_left, model.reaction.value
                    self.displayed_grid = view.refresh_grid(affected_cells)  # record updated grid state
            view.clock = time.time() - starting_time  # display time passed for the player
        return

    def get_user_move(self) -> tuple[int, str] | None:
        """Checks for and returns a valid user input (i.e. change in a cell on the grid/minefield range)"""
        time.sleep(1)  # poll user (not bot) "move" every second
        chgs, prior_values = 0, self.displayed_grid  # contains state (cell values/contents) prior to user input
        new_values = self.view.read_grid()
        for i, (old_val, new_val) in enumerate(zip(prior_values, new_values)):
            if old_val != new_val:
                chgs += 1
                changed_cell_idx, changed_cell_val = i, str(new_val)
        if chgs == 1:
            return changed_cell_idx, changed_cell_val
        elif chgs > 1:
            self._invalid_move_rollback(grid_prev_state=prior_values)
        return None  # chgs == 0 or > 1

    def _invalid_move_rollback(self, grid_prev_state: "Value2") -> None:
        print("User tried to change multiple cells")
        self.view.smile = self.model.emoticons.WAITS.value  # place in parent class of ExcelViewController (to-do)?
        self.view.set_grid(grid_prev_state)  # reset cell values to before last user's move

    def _feed(self, bot_strategy: Callable) -> Callable:
        """ Supplement bot with what user sees (programmatically). Alternatively, use functools.partial.
         Minesweeper is Markovian (probabilities can be computed from current state and do not depend on priors),
         therefore no need to maintain state and use coroutine; thus, a simple call of external function."""
        grid_methods = Grid(w=self.model.w, h=self.model.h)  # only to provide access to (fixed) coordinate plane
        def move_by_bot() -> tuple[int, str]:
            return bot_strategy(visible_grid=self.players_view, mines_left=self.flags_left, grid_methods=grid_methods)
        return move_by_bot
