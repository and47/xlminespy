import sys  # without this Excel complains of "Unlicensed product"
import time
from numbers import Integral as int_like

import clr  # provide own path (may depend on your Excel installation):
clr.AddReference(r"C:\Program Files (x86)\Microsoft Office\root\Office16\DCF\Microsoft.Office.Interop.Excel.dll")
from System import Activator, Type, Reflection
from Microsoft.Office.Interop import Excel


class ExcelViewController:  # inherit from generic Minefield ViewController?

    def __init__(self, cols, rows, content_view, clock_loc: tuple | None = None, flagc_loc: tuple | None = None):
        excel_type = Type.GetTypeFromProgID("Excel.Application")
        self.excel = Activator.CreateInstance(excel_type)
        workbook = self.excel.Workbooks.Add()
        self.ws = Excel.Worksheet(workbook.Worksheets[1])

        self.start_rowcol, self.end_rowcol = self.arr_rowcol_range_from_dims(w=cols, h=rows)
        self.y0, self.x0 = self.start_rowcol

        self.content_view = content_view.reshape((rows, cols))

        self.format_score_time(clock_loc, flagc_loc)
        self.flag_counter, self.clock, self.smile = 0, 0, ''

    def format_score_time(self, clock_loc: tuple | None, flagc_loc: tuple | None) -> None:
        clock_loc = self.end_rowcol[1] + 1, self.y0 - 1 if clock_loc is None else clock_loc
        self.clock_cell = self.get_xl_range(coord=clock_loc)
        flagc_loc = self.x0 - 1, self.y0 - 1 if flagc_loc is None else flagc_loc
        self.flagc_cell = self.get_xl_range(coord=flagc_loc)
        smile_loc = flagc_loc[0] + (clock_loc[0] - flagc_loc[0]) // 2, self.y0 - 1
        self.smile_cell = self.get_xl_range(coord=smile_loc)

    def __setattr__(self, name, value):
        if name == 'clock':  # custom setter-only, which renders time in addition to setting it
            # self.clock = value  # not really needed, can just pass through
            self.set_xl_value(self.clock_cell, value=int(value))
        elif name == 'flag_counter':  # render flag count
            self.set_xl_value(self.flagc_cell, value=int(value))
        elif name == 'smile':  # render flag count
            self.set_xl_value(self.smile_cell, value=str(value))
        else:
            super().__setattr__(name, value)  # default behavior for other attributes

    def get_xl_cell(self, row: int_like, col: int_like) -> "Cells":
        return self.ws.GetType().InvokeMember("Cells", Reflection.BindingFlags.GetProperty, None, self.ws,
                                              [int(row + 1), int(col + 1)])  # .NET will error with e.g. numpy.int32

    def get_xl_range(self, top_left: "Cells" = None, bottom_right: "Cells" = None,
                     coord: tuple[int_like] | None = None) -> "Range":
        if coord is not None and top_left is None and bottom_right is None:
            single_cell_from_coords = self.get_xl_cell(col=coord[0], row=coord[1])
            return self.ws.get_Range(single_cell_from_coords, single_cell_from_coords)
        elif coord is None:
            if bottom_right is None:
                return self.ws.get_Range(top_left, top_left)  # single cell range from Cells obj
            return self.ws.get_Range(top_left, bottom_right)  # rectangular multi-cell Range

    @staticmethod
    def arr_rowcol_range_from_dims(w: int, h: int, vpanel: int = 1, hpanel: int = 1) -> tuple:
        return (hpanel, vpanel), (hpanel + h - 1, vpanel + w - 1)

    def set_xl_value(self, cell_range: "Range", value: int | str) -> None:
        retries, max_retries = 0, 60

        while retries < max_retries:

            while not self.excel.Ready:
                time.sleep(0.1)
            try:
                cell_range.Value2 = value
                return
            except Exception as e:
                print(f"Attempt {retries + 1}: An error occurred: {e}")
                retries += 1
                time.sleep(1)  # wait more before retrying, user could be e.g. editing cell
        raise RuntimeError("Couldn't set Excel cell value")

    def set_grid(self, values) -> None:
        while not self.excel.Ready:
            time.sleep(0.1)
        self.grid_range.Value2 = values

    def read_grid(self) -> "Value2":
        return self.grid_range.Value2

    def format_grid(self) -> None:  # to-do: center value inside each cell
        self.start_cell = self.get_xl_cell(*self.start_rowcol)  # ws.get_Cells or ws.Cells error
        self.end_cell = self.get_xl_cell(*self.end_rowcol)

        self.grid_range = grid = self.get_xl_range(top_left=self.start_cell, bottom_right=self.end_cell)
        grid.set_ColumnWidth(2.14)  # default row height (20 px)

        borders = grid.Borders
        borders.LineStyle = Excel.XlLineStyle.xlContinuous
        thicker = 4  # Excel.XlBorderWeight.xlThick == 4
        edges = [Excel.XlBordersIndex.xlEdgeTop, Excel.XlBordersIndex.xlEdgeRight,
                 Excel.XlBordersIndex.xlEdgeBottom, Excel.XlBordersIndex.xlEdgeLeft]
        for outer_border in edges:
            borders.get_Item(outer_border).set_Weight(thicker)
        self.excel.Visible = True
        grid.HorizontalAlignment = Excel.XlHAlign.xlHAlignCenter
        grid.VerticalAlignment = Excel.XlVAlign.xlVAlignCenter

    def reveal(self, cells_coords: list[tuple]) -> None:
        num_cells = len(cells_coords)
        if num_cells:
            if num_cells == 1:  # refresh a single cell
                x, y = cells_coords[0]
                range1x1 = self.get_xl_range(coord=(x, y)).Cells[self.y0, self.x0]  # adjust for grid loc.
                self.set_xl_value(range1x1, str(self.content_view[y, x]))
            else:  # or many (one cell at a time, as it may not be rectangular form)
                for i, _ in enumerate(cells_coords):
                    self.reveal([cells_coords[i]])
