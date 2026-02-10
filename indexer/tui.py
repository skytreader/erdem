from textual import on
from textual.app import App, ComposeResult
from textual.containers import HorizontalGroup
from textual.screen import Screen
from textual.widgets import (
    Button, Footer, Header, Input, Label, OptionList, Static, TabbedContent,
    TabPane
)
from textual.widgets.option_list import Option
from typing import cast

from .indexerdem import FileIndexRecord, Indexerdem

class ErdemSearch(HorizontalGroup):

    def compose(self) -> ComposeResult:
        search_box = Input(placeholder="Search by title, tag, or performer", id="search-box")
        search_box.styles.width = "93%"
        yield search_box
        search_btn = Button("Search", id="search")
        yield search_btn

class ErdemScreen(Screen):

    @property
    def erdem_app(self) -> "ErdemApp":
        return cast("ErdemApp", self.app)

class ErdemHomeScreen(ErdemScreen):
    TITLE = "Erdem"
    SUB_TITLE = "Media Notes"

    def __init__(self):
        super().__init__()
        self.titles = self.app.index.fetch_files()
        self.performers = self.app.index.fetch_persons(False)

    def compose(self) -> ComposeResult:
        yield Header()
        yield ErdemSearch()
        with TabbedContent(initial="media-tab"):
            with TabPane("Media", id="media-tab"):
                yield OptionList(
                    *tuple(Option(title.filename, id=title.id) for title in self.titles),
                    id="media-list"
                )
            with TabPane("Performers", id="performers-tab"):
                yield OptionList(
                    *tuple(Option(str(p), id=p.id) for p in self.performers),
                    id="performers-list"
                )
        yield Footer()

    @on(OptionList.OptionSelected, "#performers-list")
    async def performer_selected(self, event: OptionList.OptionSelected) -> None:
        if event.option.id is not None:
            self.app.push_screen(PerformerView(event.option.id))

    @on(OptionList.OptionSelected, "#media-list")
    async def media_selected(self, event: OptionList.OptionSelected) -> None:
        if event.option.id is not None:
            self.app.push_screen(MediaView(int(event.option.id)))

class MediaView(ErdemScreen):

    def __init__(self, id: int):
        super().__init__()
        self.record = FileIndexRecord.fetch(self.erdem_app.index.conn.cursor(), id)

    def compose(self) -> ComposeResult:
        yield Header()
        yield Static(self.record.filename if self.record is not None else "Unknown")
        yield Footer()

    def on_mount(self) -> None:
        self.title = "Erdem"
        self.sub_title = f"Media Notes - {self.title}"

class PerformerView(ErdemScreen):

    def __init__(self, performer_name: str):
        super().__init__()
        self.performer_name = performer_name

    def compose(self) -> ComposeResult:
        yield Header()
        yield Static(f"[h1]{self.performer_name}[/h1]")
        yield Footer()

    def on_mount(self) -> None:
        self.title = "Erdem"
        self.sub_title = f"Performer Notes - {self.performer_name}"

class ErdemApp(App):

    SCREENS = {
        "home": ErdemHomeScreen
    }

    def __init__(self):
        super().__init__()
        self.index = Indexerdem("cache.db")

    def on_mount(self) -> None:
        self.push_screen("home")

if __name__ == "__main__":
    app = ErdemApp()
    app.run()
