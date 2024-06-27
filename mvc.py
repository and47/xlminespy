import time
from engine import MineField
from ui_excel import ExcelViewController


class MVC_Mines_Excel_Controller:

    def __init__(self, cols: int, rows: int, mines: int):
        self.model = MineField(w=cols, h=rows)

        values_view = self.model.complete_field_init(int(mines))
        self.view = ExcelViewController(cols, rows, values_view)
        self.view.format_grid()
        # print(model.underneath.reshape((rows, cols)))  # debug

    @classmethod
    def from_CLI_settings(cls) -> 'MVC_Mines_Excel_Controller':
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

        return cls(cols=cols, rows=rows, mines=mines)

    def start_game(self):
        model, view = self.model, self.view
        view.flag_counter = model.flags_left
        starting_values = view.read_grid()  # waits for user input in the grid range
        starting_time = time.time()

        while not model.game_over:  # make a generator loop?
            chgs = 0
            values = view.read_grid()  # see methods with dir(values), e.g. GetEnumerator, GetValue
            for i, (old_val, new_val) in enumerate(zip(starting_values, values)):
                if old_val != new_val:
                    chgs += 1
                    changed_cell_idx, changed_cell_val = i, new_val
            if chgs == 1:
                affected_cells = model.cell_action(cell_idx=changed_cell_idx, user_input=changed_cell_val)
                if affected_cells:  # universal engine, in other games may be used, in minesweeper always True
                    view.flag_counter, view.smile = model.flags_left, model.reaction.value
                    view.reveal(affected_cells)
                    starting_values = view.read_grid()  # valid move, else? try catch?
            elif chgs > 1:
                print("User tried to change multiple cells")
                view.smile = model.emoticons.WAITS.value
                view.set_grid(starting_values)  # reset cell values to before last user's move
            time.sleep(1)  # poll every second
            view.clock = time.time() - starting_time  # display time passed for the player
        return
