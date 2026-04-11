# Textual Imports
from textual.widgets import Collapsible, TabPane, Label

# Standard Imports
from typing import Iterator
from studio.model import Plugin


class P(Plugin):
    def on_initialized(self) -> None:
        self.name = 'Enum'

    def panel(self) -> TabPane | None:
        return TabPane(self.name.title(), Label('Content would go here when this plugin is developed.'))

    def controls(self) -> Iterator[Collapsible]:
        return iter([])


plugin = P()
