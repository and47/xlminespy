# you may need to provide your own path (may depend on your Excel installation) in ui_excel.py
from mvc import MVC_Mines_Excel_Controller

def start_demo():
    from bot_strategy import demo_bot
    launched_instance = MVC_Mines_Excel_Controller.from_CLI_settings()
    launched_instance.start_game(bot_strategy=demo_bot)

if __name__ == "__main__":
    launched_instance = MVC_Mines_Excel_Controller.from_CLI_settings()
    launched_instance.start_game()
