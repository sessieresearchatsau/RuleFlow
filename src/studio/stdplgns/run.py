# Textual Imports
from textual.widgets import Collapsible, TabPane, Input, Label, Switch
from textual.widget import Widget
from textual.containers import ScrollableContainer
from textual.app import App

# Standard Imports
from typing import Optional, Iterator
from studio.model import Plugin, Model
from studio.stdplgns.lib.widgets import Button


class P(Plugin):
    def __init__(self) -> None:
        self.name: str = "run"
        self.model: Optional[Model] = None
        self.app: Optional[App] = None

    def panel(self) -> TabPane | None:
        return TabPane(
            self.name.title(),
            ScrollableContainer(
                Collapsible(Collapsible(expanded_symbol="-", collapsed_symbol="+")),
                Collapsible(), Collapsible())
        )

    def controls(self) -> Iterator[Widget]:
        i = Input(type='number', compact=False, valid_empty=True)
        i.border_title = 'Timeout (ms)'
        b = Button("Test")
        b.connect_pressed_callback(lambda: self.app.notify("TEST"))
        with Collapsible(title='Hot Reload', collapsed=False):
            yield Switch()
            yield i
            yield Label('Reload after changes:')
            yield Input(type='integer', compact=True, valid_empty=True)
            yield b
plugin = P()
