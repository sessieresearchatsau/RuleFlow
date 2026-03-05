# Textual Imports
from textual.widgets import Collapsible, TabPane, Input, Checkbox, Button
from textual.widget import Widget
from textual.containers import ScrollableContainer

# Standard Imports
from typing import Iterator
from studio.model import Plugin


class P(Plugin):
    def on_initialized(self) -> None:
        self.name = 'run'
        self.view.sig_button_pressed.connect(self._handle_b)

    def panel(self) -> TabPane | None:
        # TODO: connect up the controls and the Flow backend......
        return TabPane(
            self.name.title(),
            ScrollableContainer(
                Collapsible(Collapsible(expanded_symbol='-', collapsed_symbol='+')),
                Collapsible(), Collapsible()
            )
        )

    def _handle_b(self, e: Button.Pressed):
        if e.control.id == 'test':
            self.view.notify('Test Pressed')

    def controls(self) -> Iterator[Widget]:
        # NOTE: there aren't that many settings for the run tab due to most controls being available through the DSL.
        self.test = Button('Test', id='test')

        yield self.test

        with Collapsible(title='Hot Reload', collapsed=False):
            self.hot_mode = Checkbox('Enable Hot Reload Mode')
            yield self.hot_mode
            self.hot_n_changes = Input(type='integer', value='1')
            self.hot_n_changes.border_title = 'Re-run after N changes'
            yield self.hot_n_changes
            self.hot_timeout = Input(type='number', value='500')
            self.hot_timeout.border_title = 'Timeout (ms)'
            yield self.hot_timeout

        with Collapsible(title='Profiler', collapsed=False):
            self.enable_progress_bar = Checkbox('Progress bar')
            yield self.enable_progress_bar
            self.enable_program_stats = Checkbox('Resource usage stats')
            yield self.enable_program_stats
plugin = P()
