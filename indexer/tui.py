from textual import on
from textual.app import App, ComposeResult
from textual.containers import HorizontalGroup
from textual.screen import Screen
from textual.widgets import (
    Button, Footer, Header, Input, Label, OptionList, Static, TabbedContent,
    TabPane
)
from textual.widgets.option_list import Option
from typing import cast, Optional

from .indexerdem import FileIndexRecord, Indexerdem, PerformanceIndexRecord, PersonIndexRecord

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
            self.app.push_screen(PerformerView(int(event.option.id)))

    @on(OptionList.OptionSelected, "#media-list")
    async def media_selected(self, event: OptionList.OptionSelected) -> None:
        if event.option.id is not None:
            self.app.push_screen(MediaView(int(event.option.id)))

class MediaView(ErdemScreen):

    def __init__(self, id: int):
        super().__init__()
        self.record = FileIndexRecord.fetch(self.erdem_app.index.conn.cursor(), id)
        self.is_error_state = self.record is None
        # Don't use is_error_state for mypy
        if self.record is not None:
            performers_result = PerformanceIndexRecord.fetch(
                self.erdem_app.index.conn.cursor(),
                self.record
            )
            self.performers = cast(tuple[Optional[PersonIndexRecord], ...], performers_result.performers if performers_result is not None else tuple())

    def compose(self) -> ComposeResult:
        yield Header()
        yield Static(self.record.filename if self.record is not None else "Unknown")
        yield OptionList(
            *tuple(Option(str(performer)) for performer in self.performers),
            id="performers-list"
        )
        yield Footer()

    def on_mount(self) -> None:
        self.title = "Erdem"
        self.sub_title = f"Media Notes - {self.title}"

class PerformerView(ErdemScreen):

    def __init__(self, performer_id: int):
        super().__init__()
        self.performer = PersonIndexRecord.fetch(
            self.erdem_app.index.conn.cursor(), performer_id
        )
        self.is_error_state = self.performer is None
        # Don't use is_error_state for mypy
        if self.performer is not None:
            performances = PerformanceIndexRecord.fetch(
                self.erdem_app.index.conn.cursor(),
                self.performer
            )
            self.performances = cast(tuple[Optional[FileIndexRecord], ...], performances.files if performances is not None else tuple())

    def compose(self) -> ComposeResult:
        yield Header()
        yield Static(f"{self.performer}")
        yield OptionList(
            *tuple(Option(str(_file)) for _file in self.performances),
            id="performances-list"
        )
        yield Footer()

    def on_mount(self) -> None:
        self.title = "Erdem"
        self.sub_title = f"Performer Notes - {self.performer}"

class ErdemApp(App):

    SCREENS = {
        "home": ErdemHomeScreen
    }

    def __init__(self):
        super().__init__()
        self.index = Indexerdem("cache.db")

    def on_mount(self) -> None:
        self.push_screen("home")

app = ErdemApp()
if __name__ == "__main__":
    app.run()
