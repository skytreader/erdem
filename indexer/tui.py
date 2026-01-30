from textual.app import App, ComposeResult
from textual.containers import HorizontalGroup
from textual.screen import Screen
from textual.widgets import Button, Header, Input, Label, ListView, ListItem, TabbedContent, TabPane

class ErdemHeader(Header):

    def compose(self) -> ComposeResult:
        yield Header()

class ErdemSearch(HorizontalGroup):

    def compose(self) -> ComposeResult:
        search_box = Input(placeholder="Search by title, tag, or performer", id="search-box")
        search_box.styles.width = "93%"
        yield search_box
        search_btn = Button("Search", id="search")
        yield search_btn

class ErdemHomeScreen(Screen):

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
                yield ListView(
                    ListItem(Label("Craig, Daniel")),
                    ListItem(Label("de Aramas, Ana")),
                    ListItem(Label("Green, Eva")),
                    ListItem(Label("Mikkelsen, Mads"))
                )

    def on_mount(self) -> None:
        self.title = "Erdem"
        self.sub_title = "Media Notes"

class ErdemApp(App):

    SCREENS = {
        "home": ErdemHomeScreen
    }

    def on_mount(self) -> None:
        self.push_screen("home")

if __name__ == "__main__":
    app = ErdemApp()
    app.run()
