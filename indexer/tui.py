from sqlite3 import OperationalError
from textual import on
from textual.app import App, ComposeResult
from textual.containers import HorizontalGroup
from textual.reactive import reactive
from textual.screen import ModalScreen, Screen
from textual.widget import Widget
from textual.widgets import (
    Button, Footer, Header, Input, Label, OptionList, Static, TabbedContent,
    TabPane
)
from textual.widgets.option_list import Option
from typing import Any, cast, Iterable, Optional

import traceback

from .data import FileIndexRecord, PerformanceIndexRecord, PersonIndexRecord
from .indexerdem import Indexerdem, MetadataCheckResult
from .errors import InvalidDataClassState

# Source - https://stackoverflow.com/a/76333127
# Posted by winwin
# Retrieved 2026-02-17, License - CC BY-SA 4.0
def error_string(ex: Exception) -> str:
    return '\n'.join([
        ''.join(traceback.format_exception_only(None, ex)).strip(),
        ''.join(traceback.format_exception(None, ex, ex.__traceback__)).strip()
    ])

class Dynamic(Widget):
    """
    In contract to `Static`, this label is dynamic.
    """
    DEFAULT_CSS = """
    Dynamic {
        height: auto;
        width: auto;
    }
    """
    
    text: reactive[str] = reactive("text")

    def render(self) -> str:
        return self.text

class ErdemScreen(Screen):
    BINDINGS = [("backspace", "app.pop_screen", "Back")]

    @property
    def erdem_app(self) -> "ErdemApp":
        return cast("ErdemApp", self.app)

class ErdemHomeScreen(ErdemScreen):
    TITLE = "Erdem"
    SUB_TITLE = "Media Notes"
    NO_RESULTS_FOUND = Option("No results found.", disabled=True)

    def __init__(self):
        super().__init__()
        self.TITLES = self.app.index.fetch_files()
        self.title_count = Dynamic()
        self.__reset_title_list()
        self.PERFORMERS = self.app.index.fetch_persons(False)
        self.performer_count = Dynamic()
        self.__reset_performer_list()
        self.list_tabs = TabbedContent(initial="media-tab", id="list-tabs")

    def __reset_title_list(self):
        """
        Assumes that the following fields are set:

        - TITLES
        - title_count
        """
        self.shown_titles = OptionList(
            *self.__make_options_titles(self.TITLES), id="media-list"
        )
        # No idea what this unit is supposed to be. Could be "cells" which in
        # the context of an OptionList I guess would be "list items" but don't
        # quote me on that. Still, achieves what I want for now.
        self.shown_titles.styles.height = "30"
        self.title_count.text = self.__make_count_label("title", len(self.TITLES))

    def __reset_performer_list(self):
        """
        Assumes that the following fields are set:

        - PERFORMERS
        - performer_count
        """
        self.shown_performers = OptionList(
            *self.__make_options_performers(self.PERFORMERS), id="performers-list"
        )
        self.shown_performers.styles.height = "30"
        self.performer_count.text = self.__make_count_label("performer", len(self.PERFORMERS))

    def __make_options_titles(self, titles: Iterable[FileIndexRecord]) -> tuple[Option, ...]:
        title_options = []
        for title in titles:
            if title.id is None:
                raise InvalidDataClassState(f"id is None for {title}")

            title_options.append(Option(title.filename, id=str(title.id)))

        return tuple(title_options)

    def __make_count_label(self, list_noun: str, count: int) -> str:
        """
        Create string declaring count of items in the list.

        list_noun - right now, the only use case is either "title" or "performer"
        which is very easy to pluralize. In the future we might take in a
        pluralization function.
        """
        if count == 1:
            return f"Showing 1 {list_noun}."
        else:
            return f"Showing {count} {list_noun}s."

    def __make_options_performers(self, performers: Iterable[PersonIndexRecord]) -> tuple[Option, ...]:
        performer_options = []
        for p in performers:
            if p.id is None:
                raise InvalidDataClassState(f"id is None for {p}")

            performer_options.append(Option(str(p), id=str(p.id)))

        return tuple(performer_options)

    def compose(self) -> ComposeResult:
        yield Header()
        yield Input(placeholder="Search by title, tag, or performer", id="search-box")
        with self.list_tabs:
            with TabPane("Media", id="media-tab"):
                yield self.title_count
                yield self.shown_titles
            with TabPane("Performers", id="performers-tab"):
                yield self.performer_count
                yield self.shown_performers
        yield Footer()

    @on(OptionList.OptionSelected, "#performers-list")
    async def performer_selected(self, event: OptionList.OptionSelected) -> None:
        if event.option.id is not None:
            self.app.push_screen(PerformerView(int(event.option.id)))

    @on(OptionList.OptionSelected, "#media-list")
    async def media_selected(self, event: OptionList.OptionSelected) -> None:
        if event.option.id is not None:
            self.app.push_screen(MediaView(int(event.option.id)))

    @on(Input.Changed, "#search-box")
    async def search(self, event: Input.Changed) -> None:
        self.search_worker(event.input.value)

    @on(TabbedContent.TabActivated, "#list-tabs")
    async def tab_switched(self, event: Input.Changed) -> None:
        search_input: Input = cast(Input, self.query_one("#search-box"))
        self.search_worker(search_input.value)

    def search_worker(self, query: str) -> None:
        is_search_worthy = len(query) >= 3
        if is_search_worthy:
            if self.list_tabs.active == "media-tab":
                search_results = self.erdem_app.index.search_files(query)
                self.shown_titles.clear_options()

                if search_results:
                    self.shown_titles.add_options(self.__make_options_titles(search_results))
                else:
                    self.shown_titles.add_option(ErdemHomeScreen.NO_RESULTS_FOUND)

                self.title_count.text = self.__make_count_label("title", len(search_results))
            elif self.list_tabs.active == "performers-tab":
                search_results = self.erdem_app.index.search_performers(query)
                self.shown_performers.clear_options()

                if search_results:
                    self.shown_performers.add_options(self.__make_options_performers(search_results))
                else:
                    self.shown_performers.add_option(ErdemHomeScreen.NO_RESULTS_FOUND)

                self.performer_count.text = self.__make_count_label("performer", len(search_results))
        else:
            if self.list_tabs.active == "media-tab":
                self.shown_titles.clear_options()
                self.shown_titles.add_options(self.__make_options_titles(self.TITLES))
                self.title_count.text = self.__make_count_label("title", len(self.TITLES))
            elif self.list_tabs.active == "performers-tab":
                self.shown_performers.clear_options()
                self.shown_performers.add_options(self.__make_options_performers(self.PERFORMERS))
                self.performer_count.text = self.__make_count_label("performer", len(self.PERFORMERS))

class MediaView(ErdemScreen):

    CSS_PATH = "tcss/erdem.tcss"

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
        yield Label(self.record.filename if self.record is not None else "Unknown", id="record-title")
        yield HorizontalGroup(
            Button("Save", id="save-record", flat=True),
            Button("Delete", id="delete-record", flat=True),
            classes="save-delete-button-group"
        )
        yield HorizontalGroup(
            Label("Performers:", classes="actionable-title"),
            Button("+", id="add-performer", flat=True),
            Button("x", variant="warning", id="remove-performer", flat=True)
        )
        yield OptionList(
            *tuple(Option(str(performer), id=str(performer.id)) for performer in self.performers if performer is not None),
            id="performers-list"
        )
        yield Footer()

    def on_mount(self) -> None:
        self.title = "Erdem"
        self.sub_title = f"Media Notes - {self.title}"

    @on(OptionList.OptionSelected, "#performers-list")
    async def show_performer_modal(self, event: OptionList.OptionSelected) -> None:
        if event.option.id is not None:
            self.erdem_app.push_screen(PerformerModal(int(event.option.id)))
        else:
            self.erdem_app.notify("No ID for given performer. Please check index", severity="warning")

class PerformerView(ErdemScreen):

    def __init__(self, performer_id: int):
        super().__init__()
        self.performer = PersonIndexRecord.fetch(
            self.erdem_app.index.conn.cursor(), performer_id
        )
        self.error_str: Optional[str] = None

        if self.performer is not None:
            try:
                performances = PerformanceIndexRecord.fetch(
                    self.erdem_app.index.conn.cursor(),
                    self.performer
                )
                self.performances = cast(tuple[Optional[FileIndexRecord], ...], performances.files if performances is not None else tuple())
            except OperationalError as e:
                self.error_str = error_string(e)
        else:
            self.error_str = "Performer not found"

    def compose(self) -> ComposeResult:
        yield Header()
        yield Static(f"{self.performer}")
        if self.error_str is None:
            yield OptionList(
                *tuple(Option(str(_file)) for _file in self.performances),
                id="performances-list"
            )
        else:
            error = Static(f"Error: {self.error_str}")
            error.styles.background = "red"
            error.styles.color = "white"
            error.styles.padding = (1, 2)
            yield error
        yield Footer()

    def on_mount(self) -> None:
        self.title = "Erdem"
        self.sub_title = f"Performer Notes - {self.performer}"

class PerformerModal(ModalScreen):
    DEFAULT_CSS = """
        #performances-list {
            width: 60
        }
    """
    BINDINGS = [
        ("backspace", "close", "Close")
    ]

    def __init__(self, performer_id: int):
        super().__init__()
        self.parent_screen = PerformerView(performer_id)

    def compose(self) -> ComposeResult:
        return self.parent_screen.compose()

    def action_close(self):
        self.app.pop_screen()

class ErdemApp(App):

    SCREENS = {
        "home": ErdemHomeScreen
    }

    def __init__(self):
        super().__init__()
        self.index = Indexerdem("cache.db")
        compatibility_check = self.index.check_compatibility()
        CHECK_TITLE = "Index Compatibility Check"

        if compatibility_check == MetadataCheckResult.COMPLETELY_COMPATIBLE:
            self.notify("Passed.", title=CHECK_TITLE)
        elif compatibility_check == MetadataCheckResult.LIKELY_COMPATIBLE:
            self.notify("Slight compatibility discrepancies detected. Reindex soon.", severity="warning", title=CHECK_TITLE)
        elif compatibility_check == MetadataCheckResult.INDETERMINATE:
            self.notify("Unable to determine compatibility. Reindexing strongly suggested", severity="error", title=CHECK_TITLE)
        elif compatibility_check == MetadataCheckResult.INCOMPATIBLE:
            self.notify("Compatibility not guaranteed. Reindexing strongly suggested.", severity="error", title=CHECK_TITLE)

    def on_mount(self) -> None:
        self.app.push_screen("home")

app = ErdemApp()
if __name__ == "__main__":
    app.run()
