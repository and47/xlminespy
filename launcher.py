# you may need to provide your own path (may depend on your Excel installation) in ui_excel.py
from mvc import MVC_Mines_Controller
from ui_ro_cli import CLIViewReadOnly
from ui_excel import ExcelViewController
from bot_strategy import demo_bot


def start_Excel_demo(excel: bool = True) -> None:
    launched_instance = MVC_Mines_Controller.from_CLI_settings(ui=ExcelViewController if excel else CLIViewReadOnly)
    launched_instance.start_game(bot_strategy=demo_bot)


if __name__ == "__main__":
    # start_Excel_demo()  # for a bot to play

    default_launched_instance = MVC_Mines_Controller.from_CLI_settings(ui=ExcelViewController)
    default_launched_instance.start_game()  # for a user to play
