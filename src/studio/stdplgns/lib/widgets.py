"""This is where some widgets are located that are uniquely useful to Plugin.controls() UI constructions.\

The main reason for doing this is to provide easy access to events (through callbacks) of widgets for non-textual code.
Of course, other useful widgets may be created here as needed for the standard plugin library.

Best Development Policy:
- Quickly provide widgets that work... no need to be perfectionistic.
- Only after having working controls, then "prettify" them into well-styled/ordered widgets.
    - Abstract those into specialized widgets here if deemed elegant.
"""

# Textual Imports
from textual.widgets import Button as _Button

# Standard Imports
from typing import Callable


class Button(_Button):
    """A normal Textual Button but extended with pressed callbacks."""

    def connect_pressed_callback(self, c: Callable):
        self._pressed_callback: Callable = c

    def on_button_pressed(self):
        self._pressed_callback()
