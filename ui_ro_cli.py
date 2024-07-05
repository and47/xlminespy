import numpy as np
import os
from time import sleep


class View:
    def __init__(self, cols: int, rows: int, content_view: np.ndarray) -> None:
        self.content_view = content_view
        self.flag_counter, self.clock, self.smile = 0, 0, '  '
        self.w, self.h = cols, rows

    def format_grid(self):
        """Prepare initial UI"""
        pass

    def refresh_grid(self, cells_coords: list[tuple]):
        pass


class CLIViewReadOnly(View):

    empty = f"\N{middle dot}"
    indent = ' ' * 5

    def __init__(self, cols, rows, content_view, clock_loc: tuple | None = None, flagc_loc: tuple | None = None):
        super().__init__(cols, rows, content_view)
        self.spacing = cols + 2*2  # top_panel: flag, smilee, time counter, each ~3 chars, equally spaced

    def display_top_panel(self):
        w1, w2, spc = str(self.flag_counter), str(self.clock), self.spacing
        formatted_line = f" {w1:<{max(0, spc - len(w1))}}{self.smile:^{len(self.smile)}}{w2:>{max(0, spc - len(w2))}}"
        print(formatted_line)

    def format_grid(self):
        """Prepare initial UI. Also, print it. Can make starting screen different here."""
        self.refresh_grid()

    def refresh_grid(self, cells_coords: list[tuple] | None = None):
        """Prints the grid (to-do: update only required parts, use framework, etc)."""
        sleep(0.5)
        os.system('cls||clear')
        pretty_grid = np.where(np.isin(self.content_view, ['', ' ']), self.empty, self.content_view)
        self.display_top_panel()
        for r in range(self.h):
            print(self.indent + " ".join(pretty_grid[r, :]))

    def __setattr__(self, name, value):
        if name == 'clock':  # custom setter-only, which renders time in addition to setting it
            self.__dict__[name] = int(value)  # not really needed, can just pass through
            # self.refresh_grid()  # temporary, to-do: update only req'd parts
        else:
            super().__setattr__(name, value)  # default behavior for other attributes
