from textual.app import App, ComposeResult
from textual.widgets import Input

class ErdemHomeApp(App):

    def compose(self) -> ComposeResult:
        yield Input(placeholder="Enter a title, tag, or performer", id="search-box")

if __name__ == "__main__":
    app = ErdemHomeApp()
    app.run()
