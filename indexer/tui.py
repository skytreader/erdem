from collections.abc import Callable
from dataclasses import dataclass
from enum import auto, Enum
from sqlite3 import OperationalError
from textual import on
from textual.app import App, ComposeResult
from textual.containers import CenterMiddle, Grid, HorizontalGroup
from textual.screen import ModalScreen, Screen
from textual.widget import Widget
from textual.widgets import (
    Button, Footer, Header, Label, Markdown, OptionList, Static,
    TabbedContent, TabPane, TextArea
)
from textual.widgets.option_list import Option
from textual import log
from typing import Any, cast, Generic, Iterable, Optional, TypeVar

import os
import traceback

from .custom import Dynamic, GoodInput
from .data import (
    FileIndexRecord,
    NameDecisionRule,
    PerformanceIndexRecord,
    PersonIndexRecord
)
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

class CRUDAction(Enum):
    CREATE = auto()
    READ = auto()
    UPDATE = auto()
    DELETE = auto()
    NOOP = auto()

T = TypeVar("T")

@dataclass
class CRUDActionResult(Generic[T]):
    action: CRUDAction
    record: T

class ErdemScreen(Screen):
    BINDINGS = [("backspace", "app.pop_screen", "Back")]

    @property
    def erdem_app(self) -> "ErdemApp":
        return cast("ErdemApp", self.app)

def _make_options_performers(performers: Iterable[PersonIndexRecord]) -> tuple[Option, ...]:
        performer_options = []
        for p in performers:
            if p.id is None:
                raise InvalidDataClassState(f"id is None for {p}")

            performer_options.append(Option(str(p), id=str(p.id)))

        return tuple(performer_options)

class ErdemHomeScreen(ErdemScreen):
    TITLE = "Erdem"
    SUB_TITLE = "Media Notes"

    BINDINGS=[
        ("shift+tab", "switch_tab", "Switch tabs"),
        # Prevent popping screen when in the home screen.
        ("backspace", "")
    ]
    CSS_PATH = "tcss/erdem.tcss"

    NO_RESULTS_FOUND = Option("No results found.", disabled=True)

    def __init__(self):
        try:
            super().__init__()
            self.TITLES = self.app.index.fetch_files()
            self.title_count = Dynamic()
            self.__reset_title_list()
            self.PERFORMERS = self.app.index.fetch_persons(False)
            self.performer_count = Dynamic()
            self.__reset_performer_list()
            self.list_tabs = TabbedContent(initial="media-tab", id="list-tabs")
            self.records_loaded = True
        except OperationalError as oe:
            self.records_loaded = False
            self.app.log(error_string(oe))

    def __reset_title_list(self):
        """
        Assumes that the following fields are set:

        - TITLES
        - title_count
        """
        self.shown_titles = OptionList(
            *self.__make_options_titles(self.TITLES), id="media-list"
        )
        self.title_count.text = self.__make_count_label("title", len(self.TITLES))

    def __reset_performer_list(self):
        """
        Assumes that the following fields are set:

        - PERFORMERS
        - performer_count
        """
        self.shown_performers = OptionList(
            *_make_options_performers(self.PERFORMERS), id="performers-list"
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

    def compose(self) -> ComposeResult:
        yield Header()

        if self.records_loaded:
            yield GoodInput(placeholder="Search by title, tag, or performer", id="search-box")
            with self.list_tabs:
                with TabPane("Media", id="media-tab"):
                    yield self.title_count
                    yield self.shown_titles
                with TabPane("Performers", id="performers-tab"):
                    yield self.performer_count
                    yield self.shown_performers
        else:
            self.app.notify(
                "Unable to load records. Please check index integrity.",
                severity="error",
                title="Index Corrupted"
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

    @on(GoodInput.Changed, "#search-box")
    async def search(self, event: GoodInput.Changed) -> None:
        self.search_worker(event.input.value)

    @on(TabbedContent.TabActivated, "#list-tabs")
    async def tab_switched(self, event: GoodInput.Changed) -> None:
        search_input: GoodInput = cast(GoodInput, self.query_one("#search-box"))
        self.search_worker(search_input.value)

    def action_switch_tab(self) -> None:
        if self.list_tabs.active == "media-tab":
            self.list_tabs.active = "performers-tab"
        elif self.list_tabs.active == "performers-tab":
            self.list_tabs.active = "media-tab"

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
                    self.shown_performers.add_options(_make_options_performers(search_results))
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
                self.shown_performers.add_options(_make_options_performers(self.PERFORMERS))
                self.performer_count.text = self.__make_count_label("performer", len(self.PERFORMERS))

class MediaView(ErdemScreen):

    CSS_PATH = "tcss/record-view.tcss"

    def __init__(self, id: int):
        super().__init__()
        self.record = FileIndexRecord.fetch(self.erdem_app.index.conn.cursor(), id)
        self.error_str = ""
        if self.record is not None:
            performers_result = PerformanceIndexRecord.fetch(
                self.erdem_app.index.conn.cursor(),
                self.record
            )
            temp_performers = cast(tuple[Optional[PersonIndexRecord], ...], performers_result.performers if performers_result is not None else tuple())
            self.performers: list[PersonIndexRecord] = [
                tp for tp in temp_performers if tp is not None
            ]
            self.shown_performers = OptionList(
                *tuple(Option(str(performer), id=str(performer.id)) for performer in self.performers if performer is not None),
                id="performers-list",
                classes="span3"
            )
        else:
            self.error_str = f"Can't find performer with id {id}"

    def __update_record_model(self):
        self.record.rating = int(self.query_one("#rating-input").value)
        self.record.review = self.query_one("#review").source

    def compose(self) -> ComposeResult:
        yield Header()
        if self.record:
            ##############
            yield Label(self.record.filename if self.record is not None else "Unknown", id="record-title", classes="span2")
            yield HorizontalGroup(
                Button("Save", id="save-record", flat=True),
                Button("Delete", id="delete-record", flat=True),
                classes="span1"
            )
            ##############
            yield Label("Fullpath:", classes="span1")
            yield Label(self.record.fullpath, classes="span2")
            ##############
            yield Label("Rating:", classes="span1")
            yield GoodInput(
                classes="span2",
                type="integer",
                value=str(self.record.rating),
                id="rating-input"
            )
            ##############
            yield HorizontalGroup(
                Label("Performers:", classes="actionable-title"),
                Button("+", id="add-performer", flat=True),
                Button("x", variant="warning", id="remove-performer", flat=True),
                classes="span3"
            )
            yield self.shown_performers
            ##############
            yield HorizontalGroup(
                Label("Review:", classes="actionable-title"),
                Button("Edit", id="edit-review", flat=True),
                classes="span3"
            )
            yield Markdown(self.record.review, classes="span3", id="review")
        else:
            error = Static(f"Error: {self.error_str}")
            error.styles.background = "red"
            error.styles.color = "white"
            error.styles.padding = (1, 2)
            yield error

        yield Footer()

    def on_mount(self) -> None:
        self.title = "Erdem"
        self.sub_title = f"Media Notes - {self.title}"

    @on(OptionList.OptionSelected, "#performers-list")
    async def show_performer_modal(self, event: OptionList.OptionSelected) -> None:
        if event.option.id is not None:
            self.erdem_app.push_screen(
                PerformerModal(int(event.option.id)),
                callback=self.__update_performer_list
            )
        else:
            self.erdem_app.notify("No ID for given performer. Please check index", severity="warning")

    def __update_review(self, review: Optional[str]):
        if self.record and review:
            self.record.review = review
            cast(Markdown, self.query_one("#review")).update(review)

    def __update_performer_list(self, action_result: Optional[CRUDActionResult[PersonIndexRecord]]) -> None:
        if action_result and action_result.action == CRUDAction.UPDATE:
            # First find the index of the updated record
            idx = 0
            for performer in self.performers:
                if performer.id == action_result.record.id:
                    break
                idx += 1
            self.performers[idx] = action_result.record
            self.shown_performers.clear_options()
            self.shown_performers.add_options(_make_options_performers(self.performers))

    @on(Button.Pressed, "#edit-review")
    async def show_edit_review_modal(self, event: Button.Pressed) -> None:
        self.erdem_app.push_screen(
            EditMarkdownModal(
                "Review",
                self.record.review if self.record and self.record.review else ""
            ),
            callback=self.__update_review
        )

    @on(Button.Pressed, "#save-record")
    async def save_record(self, event: Button.Pressed) -> None:
        self.__update_record_model()
        if self.record and self.record.save(self.erdem_app.index.conn.cursor()):
            self.erdem_app.save_record_success()
        else:
            self.erdem_app.save_record_failed()
        self.erdem_app.index.conn.commit()

def performer_record_form(record: PersonIndexRecord, cursor, is_modal: bool) -> ComposeResult:
    yield HorizontalGroup(
        Label(str(record), classes="performer-label"),
        Button("Save", id="save-record", flat=True, classes="top-level-action"),
        Button("Delete", id="delete-record", flat=True, classes="top-level-action"),
        classes="span3"
    )
    ###############################################
    yield Label("First name:", classes="span1")
    yield GoodInput(classes="span2", value=f"{record.firstname}", id="performer-firstname")
    yield Label("Last name:", classes="span1")
    yield GoodInput(classes="span2", value=f"{record.lastname if record.lastname else ""}", id="performer-lastname")
    ###############################################
    if not is_modal:
        yield HorizontalGroup(
            Label("Performances:", classes="actionable-title"),
            Button("+", id="add-performance", flat=True, classes="list-action"),
            Button("x", variant="warning", id="remove-performance", flat=True, classes="list-action"),
            classes="span3 list-action"
        )
    else:
        yield Label("Performances:", classes="span3")
    performances = record.load_performances(cursor)
    if performances:
        yield OptionList(
            *tuple(Option(str(_file)) for _file in performances),
            id="performances-list",
            classes="span3"
        )

class PerformerView(ErdemScreen):
    CSS_PATH = "tcss/record-view.tcss"

    def __init__(self, performer_id: int, is_modal_view: bool = False):
        super().__init__()
        self.performer = PersonIndexRecord.fetch(
            self.erdem_app.index.conn.cursor(), performer_id
        )
        self.is_modal_view = is_modal_view
        self.error_str: Optional[str] = None

        if self.performer is not None:
            try:
                self.performances = self.performer.load_performances(self.erdem_app.cursor)
            except OperationalError as e:
                self.error_str = error_string(e)
        else:
            self.error_str = "Performer not found"

    def compose(self) -> ComposeResult:
        if not self.is_modal_view:
            yield Header()

        if self.error_str is None:
            if self.performer:
                yield from performer_record_form(
                    self.performer,
                    self.erdem_app.cursor,
                    self.is_modal_view
                )
        else:
            error = Static(f"Error: {self.error_str}")
            error.styles.background = "red"
            error.styles.color = "white"
            error.styles.padding = (1, 2)
            yield error
        if not self.is_modal_view:
            yield Footer()

    def on_mount(self) -> None:
        self.title = "Erdem"
        self.sub_title = f"Performer Notes - {self.performer}"

    def __update_record_model(self) -> None:
        if self.performer:
            self.performer.firstname = cast(GoodInput, self.query_one("#performer-firstname")).value
            self.performer.lastname = cast(GoodInput, self.query_one("#performer-lastname")).value

class PerformerModal(ModalScreen[CRUDActionResult[PersonIndexRecord]]):
    """
    Should be basically the same as the full PerformerView but here the user can
    only edit the performer's name.
    """
    CSS_PATH = "tcss/record-view.tcss"
    BINDINGS = [
        ("backspace", "close", "Close")
    ]

    def __init__(self, performer_id: int):
        super().__init__()
        self.parent_screen = PerformerView(performer_id, True)
        if self.parent_screen.performer:
            self.original_name = (
                self.parent_screen.performer.firstname,
                self.parent_screen.performer.lastname
            )

    def compose(self) -> ComposeResult:
        with CenterMiddle(id="modal-container"):
            if self.parent_screen.performer:
                yield from performer_record_form(
                    self.parent_screen.performer,
                    self.parent_screen.erdem_app.cursor,
                    True
                )

    @on(Button.Pressed, "#save-record")
    def action_save(self):
        self.parent_screen.performer.firstname = self.query_one("#performer-firstname").value
        self.parent_screen.performer.lastname = self.query_one("#performer-lastname").value
        if self.original_name != (
            self.parent_screen.performer.firstname,
            self.parent_screen.performer.lastname
        ):
            self.parent_screen.performer.extraction_rule = NameDecisionRule.MANUAL_INPUT
            try:
                self.parent_screen.performer.save(self.parent_screen.erdem_app.cursor)
                self.parent_screen.erdem_app.index.conn.commit()
                action_result = CRUDActionResult(
                    CRUDAction.UPDATE,
                    self.parent_screen.performer
                )
                self.parent_screen.erdem_app.save_record_success()
                self.dismiss(action_result)
            except Exception:
                self.parent_screen.erdem_app.save_record_failed()
        else:
            action_result = CRUDActionResult(
                CRUDAction.NOOP,
                self.parent_screen.performer
            )
            self.dismiss(action_result)

    def action_close(self):
        self.app.pop_screen()

class EditMarkdownModal(ModalScreen[str]):
    BINDINGS = [
        ("backspace", "close", "Close")
    ]

    def __init__(self, markdown_component_name, initial_value: str):
        super().__init__()
        self.markdown_component_name = markdown_component_name
        self.initial_value = initial_value

    def compose(self) -> ComposeResult:
        with CenterMiddle(id="modal-container"):
            yield Label(f"Editing {self.markdown_component_name}", classes="span3")
            # TODO make this highlight as markdown
            yield TextArea(self.initial_value, id="markdown-text")
            yield HorizontalGroup(
                Button("Save", id="save", variant="primary"),
                Button("Cancel", id="cancel"),
                classes="span3"
            )

    @on(Button.Pressed, "#save")
    def action_close(self):
        self.dismiss(self.query_one(TextArea).text)

    @on(Button.Pressed, "#cancel")
    def action_cancel(self):
        self.dismiss(self.initial_value)

class ErdemApp(App):

    SCREENS = {
        "home": ErdemHomeScreen
    }

    DEFAULT_CSS = """
    * {
        border: solid green;
    }
    """ if bool(os.environ.get("ERDEM_CSS_DEBUG")) else ""

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

    @property
    def cursor(self):
        return self.index.conn.cursor()

    def on_mount(self) -> None:
        self.app.push_screen("home")

    def save_record_failed(self) -> None:
        self.notify("Failed to save record", severity="error")

    def save_record_success(self) -> None:
        self.notify("Record saved")

app = ErdemApp()
if __name__ == "__main__":
    app.run()
