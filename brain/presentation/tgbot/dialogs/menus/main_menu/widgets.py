from aiogram_dialog.widgets.kbd import Start
from aiogram_dialog.widgets.text import Const
from aiogram_dialog import Window

from brain.presentation.tgbot.states import ViewNotes, MainMenu


main_menu_window = Window(
    Const(
        "Hello, I'm brain bot.\n"
        "\n"
        "Just send me a message and I'll save it for you.",
    ),
    Start(
        text=Const("View your notes"), id="start_view_notes", state=ViewNotes.notes_list,
    ),
    state=MainMenu.main_menu,
)
