from textual.app import App, ComposeResult
from textual.containers import Container, Center, Horizontal, Vertical, VerticalScroll
from textual.screen import Screen, ModalScreen
from textual.widgets import ( Log,
    DirectoryTree, TextArea, RichLog, Button, Label,
    Switch, Select, TabbedContent, TabPane, OptionList,
    Input, Collapsible, Checkbox, Header, Footer, ContentSwitcher, Static
)
from textual import on


LOGO: str = r"""______      _     ______ _                    _____ _             _ _       
| ___ \    | |    |  ___| |                  /  ___| |           | (_)      
| |_/ /   _| | ___| |_  | | _____      __    \ `--.| |_ _   _  __| |_  ___  
|    / | | | |/ _ \  _| | |/ _ \ \ /\ / /     `--. \ __| | | |/ _` | |/ _ \ 
| |\ \ |_| | |  __/ |   | | (_) \ V  V /     /\__/ / |_| |_| | (_| | | (_) |
\_| \_\__,_|_|\___\_|   |_|\___/ \_/\_/      \____/ \__|\__,_|\__,_|_|\___/"""


class InputModal(ModalScreen[str]):
    """
    A generic modal that overlays the screen, dims the background,
    and captures text input.
    """

    def __init__(self, prompt: str, placeholder: str = ""):
        super().__init__()
        self.prompt_text = prompt
        self.placeholder_text = placeholder

    def compose(self) -> ComposeResult:
        # The 'modal-dialog' ID is crucial for the CSS centering to work
        with Vertical(id="modal-dialog"):
            yield Label(self.prompt_text, id="modal-label")
            yield Input(placeholder=self.placeholder_text, id="modal-input")

            with Horizontal(id="modal-buttons"):
                yield Button("Cancel", variant="default", id="cancel")
                yield Button("Submit", variant="primary", id="submit")

    @on(Button.Pressed, "#submit")
    @on(Input.Submitted, "#modal-input")
    def action_submit(self):
        # Return the value to the callback
        value = self.query_one("#modal-input", Input).value
        self.dismiss(value)

    @on(Button.Pressed, "#cancel")
    def action_cancel(self):
        # Return None to indicate cancellation
        self.dismiss(None)


class WelcomeScreen(Screen):
    """
    The landing screen matching Image 1.
    """
    CSS_PATH = "styles.tcss"

    # noinspection PyRedundantParentheses
    def compose(self) -> ComposeResult:
        with Container(id="welcome-container") as wc:
            wc.border_subtitle = 'v0.1.0'

            with Center():  # to center it *relative* to the other widgets
                yield Label(LOGO, id="welcome-title")

            yield (_:=OptionList(
                    *(f'Project Example {i}' for i in range(12)),
                    id="recents-list"
            ))
            _.border_title = 'Recent Projects'
            with Horizontal(id="welcome-buttons"):
                yield Button("📂 Open", id="btn-open-project", variant="primary")
                yield Button("➕ New", id="btn-new-project", variant="default")
                yield (_:=Static())
                _.styles.width = '1fr'
                yield Button("🗑  Remove", id="btn-clear-recents", variant="default")

    @on(Button.Pressed, "#btn-new-project")
    def action_new_project_path(self):
        """Calls the reusable InputModal to get a new project path."""

        def handle_path(path: str | None):
            if path:
                self.notify(f"Creating project at: {path}")
                # You can now add this to your list or switch screens
                self.query_one("#recents-list").add_option(path)
            elif path == "":
                self.notify("Path cannot be empty", severity="error")

        self.app.push_screen(
            InputModal("Enter New Project Path:", "/Users/Projects/etc..."),
            callback=handle_path
        )

    @on(Button.Pressed, "#btn-open-project")
    def on_open(self):
        self.app.push_screen("editor")

    @on(Button.Pressed, "#btn-clear-recents")
    def on_clear(self):
        _ = self.query_one("#recents-list")
        if (i:=_.highlighted) != None:
            _.remove_option_at_index(i)
        else:
            self.notify('There is no selection to remove!', severity='warning')


class EditorScreen(Screen):
    """
    The main IDE interface matching Image 2 with dynamic sidebar logic.
    """
    CSS_PATH = "styles.tcss"

    # UPDATED BINDINGS:
    # ctrl+b: Left Sidebar
    # ctrl+u: Right Sidebar (changed from ctrl+m to avoid Enter conflict)
    # ctrl+j: Bottom Panel (standard toggle key)
    BINDINGS = [
        ("ctrl+b", "toggle_left_sidebar", "Toggle Project View"),
        ("ctrl+u", "toggle_right_sidebar", "Toggle Context Menu"),
        ("ctrl+j", "toggle_bottom_panel", "Toggle Output Panel"),
    ]

    def compose(self) -> ComposeResult:
        # 2. Main 3-Column Layout
        with Horizontal(id="main-layout"):
            # --- LEFT COLUMN: Project Files ---
            with Vertical(id="sidebar"):
                yield Label("Project Files", classes="pane-header")
                yield DirectoryTree("./", id="file-tree")

                with Vertical(classes="sidebar-note"):
                    yield Button("↻  Refresh Directory", classes="dim-text")
                    yield Button("↩  Project Manager", classes="dim-text")

            # --- MIDDLE COLUMN: Workspace ---
            with Vertical(id="workspace"):
                # Top Toolbar
                with Horizontal(id="workspace-toolbar"):
                    yield Button("Docs", id="btn-docs")
                    with Horizontal(id="toolbar-actions"):
                        yield Button("Run", id="btn-run", classes="action-btn success")
                        yield Label("|", classes="separator")
                        yield Button("Debug", id="btn-debug", classes="action-btn warning")
                        yield Label("|", classes="separator")
                        yield Button("Clear", id="btn-clear", classes="action-btn error")

                # Code Editor
                with Container(id="editor-area"):
                    yield TextArea.code_editor(
                        text="# Select a .flow file to begin...",
                        language="python",
                        id="code-editor"
                    )

                # Bottom Panel (Output vs Analysis)
                with Container(id="bottom-panel"):
                    with TabbedContent(initial="tab-output", id="bottom-tabs"):
                        # ID is applied to the TabPane content
                        with TabPane("Output", id="tab-output"):
                            yield Log(id="log-output")

                        with TabPane("Analysis", id="tab-analysis"):
                            yield Label("Graph/Network Visualization Placeholder", classes="placeholder-text")
                            yield RichLog(id="log-analysis")

            # --- RIGHT COLUMN: Context Menu ---
            with Vertical(id="right-menu") as _:
                # Dynamic Header
                yield Label("Run Settings", classes="pane-header", id="sidebar-header")

                # Dynamic Settings Container
                with ContentSwitcher(initial="menu-output", id="sidebar-switcher"):
                    # -- A. SETTINGS FOR "OUTPUT" TAB --
                    with Vertical(id="menu-output"):
                        # Section: Output
                        with Collapsible(title="Output Controls", collapsed=False):
                            yield Label("Run Steps / Stop Condition")
                            yield Input(placeholder="e.g. 1000", id="inp-steps")

                        # Section: Live Mode
                        with Collapsible(title="Live Mode", collapsed=False):
                            yield Checkbox("Enable Live Mode", id="chk-live")
                            yield Label("Timeout Setting (ms)")
                            yield Input(placeholder="500", id="inp-timeout")
                            yield Checkbox("Timed/Wait Mode")
                            yield Checkbox("Show Active Rule(s)")
                            yield Checkbox("Multiway path selection")

                        # Section: Debugger
                        with Collapsible(title="Debugger", collapsed=True):
                            yield Label("Break Conditions")
                            yield Input(placeholder="Line no. or Condition")
                            yield Label("Jump/Step Length")
                            yield Select([("1 Step", 1), ("10 Steps", 10), ("100 Steps", 100)], value=1)
                            yield Checkbox("Show Mem + Compute Time")
                            yield Button("Export as SVG", classes="full-width-btn")

                        # Section: Ruleset View Options
                        with Collapsible(title="Ruleset View Options", collapsed=True):
                            yield Checkbox("Letters (or source)")
                            yield Checkbox("Colors (with letters)")
                            yield Label("Rendering Mode")
                            yield Select([("Linear", "lin"), ("Vertical", "vert")], value="lin")

                    # -- B. SETTINGS FOR "ANALYSIS" TAB --
                    with Vertical(id="menu-analysis"):
                        # Section: Analysis Controls
                        with Collapsible(title="Analysis Settings", collapsed=False):
                            yield Checkbox("Streaming mode (Gephi)")
                            yield Checkbox("Enable different stats/metrics")
                            yield Label("Conversion Mode")
                            yield Select([("Graphs to Stats", "g2s"), ("Raw Data", "raw")], value="g2s")

                        # Section: AI & Permissions
                        with Collapsible(title="AI & Backend", collapsed=False):
                            yield Label("AI Model Configuration")
                            yield Select([("Local (Llama)", "local"), ("Cloud (GPT-4)", "cloud")], value="local")
                            yield Button("Manage Permissions", classes="full-width-btn")
                            yield Button("Run AI Analysis", variant="primary", classes="full-width-btn")

        # 3. Footer
        yield Footer()

    # --- ACTION HANDLERS ---

    @on(TabbedContent.TabActivated)
    def on_tab_switch(self, event: TabbedContent.TabActivated):
        """
        Dynamically switches the Right Sidebar content AND Title.
        """
        switcher = self.query_one("#sidebar-switcher", ContentSwitcher)
        header = self.query_one("#sidebar-header", Label)

        if event.pane.id == "tab-output":
            switcher.current = "menu-output"
            header.update("Run Settings")
        elif event.pane.id == "tab-analysis":
            switcher.current = "menu-analysis"
            header.update("Analysis Settings")

    def action_toggle_left_sidebar(self):
        """Ctrl+B: Toggle left sidebar."""
        sidebar = self.query_one("#sidebar")
        sidebar.display = not sidebar.display

    def action_toggle_right_sidebar(self):
        """Ctrl+U: Toggle right context menu."""
        menu = self.query_one("#right-menu")
        menu.display = not menu.display

    def action_toggle_bottom_panel(self):
        """Ctrl+J: Toggle bottom output panel."""
        panel = self.query_one("#bottom-panel")
        panel.display = not panel.display

    @on(Button.Pressed, "#btn-run")
    def action_run(self):
        log = self.query_one("#log-output", Log)
        from rich.text import Text
        s = "HELLO"
        t = Text()
        colors = ["red", "green", "yellow", "blue", "magenta"]
        for ch, color in zip(s, colors):
            t.append(ch, style=f"black on {color}")
        import textual
        textual.widgets.RichLog

    @on(Button.Pressed, "#btn-clear")
    def action_clear(self):
        self.query_one("#log-output", RichLog).clear()
        self.query_one("#log-analysis", RichLog).clear()
        self.notify("Logs cleared.")


class Main(App):
    CSS_PATH = "styles.tcss"
    BINDINGS = [
        ("ctrl+q", "quit", "Quit"),
        ("f5", "run_sim", "Run Simulation"),
        ("ctrl+s", "save_file", "Save File")
    ]

    def on_mount(self):
        self.install_screen(WelcomeScreen(), name="welcome")
        self.install_screen(EditorScreen(), name="editor")
        self.push_screen("welcome")

    def action_run_sim(self):
        if isinstance(self.screen, EditorScreen):
            self.screen.action_run()

    def action_save_file(self):
        self.notify("File saved successfully.")


if __name__ == "__main__":
    app = Main()
    app.run()
