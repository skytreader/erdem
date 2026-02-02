from textual import on
from textual.app import App, ComposeResult
from textual.containers import HorizontalGroup
from textual.screen import Screen
from textual.widgets import Button, Header, Input, Label, OptionList, Static, TabbedContent, TabPane
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
        with TabbedContent(initial="media-tab"):
            with TabPane("Media", id="media-tab"):
                yield OptionList(
                    Option("Casino Royale"),
                    Option("Quantum of Solace"),
                    Option("Skyfall"),
                    Option("Spectre"),
                    Option("No Time to Die"),
                    id="media-list"
                )
            with TabPane("Performers", id="performers-tab"):
                yield OptionList(
                    Option("Craig, Daniel", id="James Bond"),
                    Option("de Armas, Ana", id="Paloma"),
                    Option("Green, Eva", id="Vesper Lynd"),
                    Option("Mikkelsen, Mads", id="Le Chiffre"),
                    id="performers-list"
                )

    @on(OptionList.OptionSelected, "#performers-list")
    async def performer_selected(self, event: OptionList.OptionSelected) -> None:
        self.app.push_screen(PerformerView(event.option.id))

    @on(OptionList.OptionSelected, "#media-list")
    async def media_selected(self, event: OptionList.OptionSelected) -> None:
        pass

class MediaView(Screen):

    def __init__(self, title: str):
        super().__init__()
        self.title = title

    def compose(self) -> ComposeResult:
        yield Header()
        yield Static(self.title)

    def on_mount(self) -> None:
        self.title = "Erdem"
        self.sub_title = f"Media Notes - {self.title}"

class PerformerView(Screen):

    def __init__(self, performer_name: str):
        super().__init__()
        self.performer_name = performer_name

    def compose(self) -> ComposeResult:
        yield Header()
        yield Static(f"[h1]{self.performer_name}[/h1]")

    def on_mount(self) -> None:
        self.title = "Erdem"
        self.sub_title = f"Performer Notes - {self.performer_name}"

class ErdemApp(App):

    SCREENS = {
        "home": ErdemHomeScreen
    }

    def on_mount(self) -> None:
        self.push_screen("home")

if __name__ == "__main__":
    app = ErdemApp()
    app.run()
