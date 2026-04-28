from textual.reactive import reactive
from textual.widget import Widget
from textual.widgets import Input

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

class GoodInput(Input):
    """
    Input that allows escape to unfocus.

    In honor of TomJGooding, who had the good taste the Textual devs so far
    still don't have.

    https://github.com/Textualize/textual/discussions/2290#discussioncomment-12373572
    """
    BINDINGS = [
        ("escape", "blur")
    ]

    def action_blur(self) -> None:
        self.blur()
