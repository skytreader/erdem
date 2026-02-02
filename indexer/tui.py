from textual import on
from textual.app import App, ComposeResult
from textual.containers import HorizontalGroup
from textual.screen import Screen
from textual.widgets import Button, Header, Input, Label, ListView, ListItem, OptionList, Static, TabbedContent, TabPane
from textual.widgets.option_list import Option

class ErdemSearch(HorizontalGroup):

    def compose(self) -> ComposeResult:
        search_box = Input(placeholder="Search by title, tag, or performer", id="search-box")
        search_box.styles.width = "93%"
        yield search_box
        search_btn = Button("Search", id="search")
        yield search_btn

class ErdemHomeScreen(Screen):
    TITLE = "Erdem"
    SUB_TITLE = "Media Notes"

    def compose(self) -> ComposeResult:
        yield Header()
        yield ErdemSearch()
        with TabbedContent(initial="media-list"):
            with TabPane("Media", id="media-list"):
                yield ListView(
                    ListItem(Label("Casino Royale")),
                    ListItem(Label("Quantum of Solace")),
                    ListItem(Label("Skyfall")),
                    ListItem(Label("Spectre")),
                    ListItem(Label("No Time to Die"))
                )
            with TabPane("Performers", id="performers-list"):
                yield OptionList(
                    Option("Craig, Daniel", id="James Bond"),
                    Option("de Armas, Ana", id="Paloma"),
                    Option("Green, Eva", id="Vesper Lynd"),
                    Option("Mikkelsen, Mads", id="Le Chiffre")
                )

    @on(OptionList.OptionSelected)
    async def option_selected(self, event: OptionList.OptionSelected) -> None:
        self.app.push_screen(PerformerView(event.option.id))

class PerformerView(Screen):

    def __init__(self, performer_name: str):
        super().__init__()
        self.performer_name = performer_name

    def compose(self) -> ComposeResult:
        yield Header()
        yield Static(f"[h1]{self.performer_name}[/h1]")

    def on_mount(self) -> None:
        self.title = "Erdem"
        self.sub_title = f"Media Notes - {self.performer_name}"

class ErdemApp(App):

    SCREENS = {
        "home": ErdemHomeScreen
    }

    def on_mount(self) -> None:
        self.push_screen("home")

if __name__ == "__main__":
    app = ErdemApp()
    app.run()
