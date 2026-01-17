import os
from textual.app import App, ComposeResult
from textual.containers import Container, Horizontal, Vertical, VerticalScroll
from textual.widgets import (
    Header, Footer, DirectoryTree, TextArea, RichLog,
    Button, Label, Switch, Select, TabbedContent, TabPane, Static
)
from textual import on, work
from textual.theme import Theme


class ControlPanel(Horizontal):
    """
    The command bar above the code editor.
    Contains main actions: Run, Live Mode, Visualization, Export.
    """

    def compose(self) -> ComposeResult:
        # Left side: Execution controls
        with Horizontal(id="exec-controls"):
            yield Button("▶ Run", id="btn-run", variant="primary")
            yield Label("Live Mode", classes="label-switch")
            yield Switch(value=False, id="sw-live")

        # Center: Visualization tools
        with Horizontal(id="vis-controls"):
            yield Button("🕸 View Network", id="btn-net", variant="warning")
            yield Button("📊 Plot Stats", id="btn-plot", variant="default")

        # Right side: Export/File operations
        with Horizontal(id="export-controls"):
            yield Select(
                options=[("Python (.py)", "py"), ("Gephi (.gexf)", "gexf"), ("JSON (.json)", "json")],
                prompt="Export As...",
                id="sel-export"
            )
            yield Button("💾 Save", id="btn-save", variant="success")


class OutputPanel(Vertical):
    """
    The bottom area for logs, errors, and graph statistics.
    Uses tabs to keep different types of output organized.
    """

    def compose(self) -> ComposeResult:
        with TabbedContent(initial="tab-console"):
            with TabPane("Console Output", id="tab-console"):
                yield RichLog(highlight=True, markup=True, id="console-log")

            with TabPane("Network Metrics", id="tab-metrics"):
                yield RichLog(id="metrics-log")

            with TabPane("Debug/Trace", id="tab-debug"):
                yield RichLog(id="debug-log")


class FlowIDE(App):
    """
    The main FlowLang IDE application shell.
    """
    CSS = """
    /* --- Main Layout --- */
    Screen {
        layout: horizontal;
        background: #1e1e1e;
    }

    /* --- Left Sidebar (Directory) --- */
    #sidebar {
        width: 25%;
        height: 100%;
        dock: left;
        background: #252526;
        border-right: heavy $background;
    }

    DirectoryTree {
        background: #252526;
        padding: 0 1;
    }

    /* --- Right Column (Main Content) --- */
    #main-content {
        width: 75%;
        height: 100%;
        layout: vertical;
    }

    /* --- Control Panel (Top Bar) --- */
    ControlPanel {
        height: 3;
        background: #333333;
        align: center top;
        padding: 0 1;
        border-bottom: solid black;
    }

    #exec-controls, #vis-controls, #export-controls {
        width: auto;
        height: auto;
        align: center middle;
    }

    /* Spacing for controls */
    Button { margin-right: 1; min-width: 8; }
    .label-switch { padding: 1; color: #cccccc; }
    Select { width: 16; }

    /* --- Code Editor Area --- */
    #editor-container {
        height: 60%;
        border-bottom: heavy $background;
        background: #1e1e1e;
    }

    TextArea {
        background: #1e1e1e;
        border: none; 
    }

    /* --- Bottom Output Area --- */
    OutputPanel {
        height: 40%;
        background: #1e1e1e;
    }

    RichLog {
        background: #1e1e1e;
        color: #d4d4d4;
        border: none;
    }
    """

    BINDINGS = [
        ("f5", "run_code", "Run Code"),
        ("ctrl+s", "save_file", "Save File"),
        ("ctrl+q", "quit", "Quit"),
        ("ctrl+b", "toggle_sidebar", "Toggle Sidebar"),
    ]

    def compose(self) -> ComposeResult:
        """Create the child widgets for the app."""
        yield Header(show_clock=True)

        # Left Sidebar
        with Vertical(id="sidebar"):
            yield Label("📁 Project Explorer", classes="panel-title")
            yield DirectoryTree("./", id="file-tree")

        # Right Main Content
        with Vertical(id="main-content"):
            yield ControlPanel()

            # Code Editor
            with Container(id="editor-container"):
                yield TextArea.code_editor(
                    text="// Select a file to begin editing...",
                    language="python",  # Python highlighting is close enough for custom DSLs usually
                    id="code-editor"
                )

            # Bottom Output Tabs
            yield OutputPanel()

        yield Footer()

    # --- ACTION HANDLERS (The "Shell" Logic) ---

    def on_mount(self):
        """Called when the app starts."""
        log = self.query_one("#console-log", RichLog)
        log.write("[bold green]Welcome to RuleFlow IDE v0.1[/]")
        log.write("Ready to evolve systems.")

    @on(DirectoryTree.FileSelected)
    def handle_file_selected(self, event: DirectoryTree.FileSelected):
        """
        Triggered when a user clicks a file in the directory tree.
        TODO: Implement file reading logic.
        1. Check if file is valid text/flow file.
        2. Read content.
        3. self.query_one("#code-editor").load_text(content)
        """
        self.notify(f"File selected: {event.path}")

    @on(Button.Pressed, "#btn-run")
    def action_run_code(self):
        """
        Triggered by the 'Run' button or F5.
        TODO: Implement execution logic.
        1. Get text from #code-editor.
        2. Pass to Interpreter.
        3. Write results to #console-log.
        """
        log = self.query_one("#console-log", RichLog)
        log.write("[bold yellow]Running simulation...[/]")
        self.notify("Execution started...")

    @on(Switch.Changed, "#sw-live")
    def toggle_live_mode(self, event: Switch.Changed):
        """
        Triggered when the Live Mode switch is toggled.
        TODO: Implement live listener.
        1. If True: Attach 'Changed' event listener to TextArea.
        2. If False: Detach listener to save resources.
        """
        state = "ENABLED" if event.value else "DISABLED"
        color = "green" if event.value else "red"
        self.query_one("#console-log", RichLog).write(f"Live Mode [{color}]{state}[/]")

    @on(Button.Pressed, "#btn-net")
    def view_network(self):
        """
        Triggered by 'View Network'.
        TODO: Implement GraphViz/Gephi bridge.
        1. Export current state to DOT/GEXF.
        2. Launch external viewer or internal subprocess.
        """
        self.notify("Opening Network Visualizer...", severity="information")

    @on(Button.Pressed, "#btn-save")
    def save_current_work(self):
        """
        Triggered by 'Save' button.
        TODO: Write content of #code-editor to currently selected file path.
        """
        self.notify("File saved successfully.")

    @on(Select.Changed, "#sel-export")
    def handle_export(self, event: Select.Changed):
        """
        Triggered when an export format is selected.
        TODO: Implement export logic.
        1. Convert internal Trie/Graph structure to selected format.
        2. Write to disk.
        """
        if event.value != Select.BLANK:
            self.notify(f"Exporting as {event.value}...")

    def action_toggle_sidebar(self):
        """Built-in action to hide/show sidebar."""
        sidebar = self.query_one("#sidebar")
        sidebar.display = not sidebar.display


if __name__ == "__main__":
    app = FlowIDE()
    app.run()