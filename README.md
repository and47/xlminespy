# Minesweeper Game Implementation Using Python and Excel COM Interoperability

Developed a Minesweeper game using Python, leveraging the .NET Common Language Runtime (CLR) to interact with Microsoft Excel. This implementation does not involve saving or extracting information from Excel file contents. Instead, it utilizes a COM connection to dynamically manipulate a worksheet's cells.

No VBA or PyXl is used, only Python and .NET (Microsoft.Office.Interop.Excel) DLL. 
Uses MVC (Model-View-Controller) design pattern to allow multiple instances of Minesweeper engine (e.g. versions) or UIs like Excel, CLI, web, etc.
To-do: use PyInstaller to create executable, which depends on user's Excel installation (DLL path).

Tested using Python 3.10.14 and pythonnet-3.0.1 from Anaconda.
