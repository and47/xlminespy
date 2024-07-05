# doesn't require Excel; bot demo only, as CLI implementation doesn't take player's input
from mvc import MVC_Mines_Controller
from ui_ro_cli import CLIViewReadOnly
from bot_strategy import demo_bot


def start_demo():
    launched_instance = MVC_Mines_Controller.from_CLI_settings(ui=CLIViewReadOnly)
    launched_instance.start_game(bot_strategy=demo_bot)


if __name__ == "__main__":
    start_demo()
