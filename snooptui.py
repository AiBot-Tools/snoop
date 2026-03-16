import asyncio
import os
import sys

from textual.app import App, ComposeResult
from textual.containers import Container, Horizontal
from textual.widgets import Header, Footer, Input, Button, RichLog, Label


class SnoopHUD(App):
    """A Textual App for the Snoop Heads-Up Display."""

    CSS = """
    Screen {
        background: #1a1b26;
    }
    #sidebar {
        dock: left;
        width: 30;
        height: 100%;
        border-right: solid #7aa2f7;
        padding: 1 2;
        background: #24283b;
    }
    #main-content {
        width: 1fr;
        height: 100%;
    }
    #search-box {
        height: 3;
        margin: 1 2;
    }
    #search-input {
        width: 1fr;
    }
    #search-button {
        width: 16;
        margin-left: 2;
        background: #7aa2f7;
        color: #1a1b26;
    }
    #log-view {
        width: 1fr;
        height: 1fr;
        margin: 0 2 1 2;
        border: solid #bb9af7;
        background: #16161e;
    }
    .title {
        text-style: bold;
        color: #bb9af7;
        margin-bottom: 1;
    }
    #target-title {
        margin-top: 2;
    }
    #include-input, #exclude-input {
        margin-bottom: 1;
    }
    """

    BINDINGS = [
        ("q", "quit", "Quit the HUD"),
    ]

    def compose(self) -> ComposeResult:
        yield Header()
        with Container(id="sidebar"):
            yield Label("Snoop Project", classes="title")
            yield Label("Enter a username in the search bar to scan across websites.")
            yield Label("Target Countries:", classes="title", id="target-title")
            yield Input(placeholder="Include (e.g. US RU)", id="include-input")
            yield Input(placeholder="Exclude (e.g. RU WR)", id="exclude-input")
            yield Label("", id="status-label")
            yield Label(
                "\nOptions enabled by default:\n- Color Output\n- Rich Formatting",
                id="options-label",
            )

        with Container(id="main-content"):
            with Horizontal(id="search-box"):
                yield Input(placeholder="Search nickname...", id="search-input")
                yield Button("Snoop!", id="search-button", variant="primary")
            yield RichLog(id="log-view", markup=True, highlight=True, auto_scroll=True)
        yield Footer()

    def on_mount(self) -> None:
        self.query_one("#search-input").focus()

        # Check if username was passed via CLI positional arguments to snoop.py
        # sys.argv could be: ['snoop.py', 'nickname'] or ['snooptui.py']
        if len(sys.argv) > 1 and sys.argv[1] not in ("--tui", "--cli"):
            inp = self.query_one("#search-input", Input)
            inp.value = sys.argv[1]

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "search-button":
            self.start_snoop()

    def on_input_submitted(self, event: Input.Submitted) -> None:
        if event.input.id == "search-input":
            self.start_snoop()

    def start_snoop(self) -> None:
        inp = self.query_one("#search-input", Input)
        username = inp.value.strip()
        if not username:
            return

        inc_inp = self.query_one("#include-input", Input)
        exc_inp = self.query_one("#exclude-input", Input)

        inc_val = inc_inp.value.strip().split()
        exc_val = exc_inp.value.strip().split()

        log = self.query_one("#log-view", RichLog)
        log.clear()

        btn = self.query_one("#search-button", Button)
        btn.disabled = True
        inp.disabled = True
        inc_inp.disabled = True
        exc_inp.disabled = True

        lbl = self.query_one("#status-label", Label)
        lbl.update(f"\n[bold green]Searching for: {username}[/]")

        self.run_worker(
            self.run_snoop_process(username, inc_val, exc_val), exclusive=True
        )

    async def run_snoop_process(
        self, username: str, includes: list, excludes: list
    ) -> None:
        log = self.query_one("#log-view", RichLog)

        env = os.environ.copy()
        env["PYTHONUNBUFFERED"] = "1"
        # Force color output
        env["FORCE_COLOR"] = "1"

        # Execute the snoop CLI from the same python binary
        cmd = [sys.executable, "snoop.py", username, "--cli"]
        for inc in includes:
            cmd.extend(["-i", inc.upper()])
        for exc in excludes:
            cmd.extend(["-e", exc.upper()])
            
        DIRPATH = os.path.dirname(os.path.abspath(__file__))

        try:
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.STDOUT,
                env=env,
            )

            if process.stdout is None:
                log.write("[red]Error: could not capture subprocess output.[/red]")
                return
            while True:
                line = await process.stdout.readline()
                if not line:
                    break
                # RichLog handles ansi natively
                decoded = line.decode("utf-8", errors="replace").rstrip("\r\n")
                if decoded:
                    log.write(decoded)

            await process.wait()
            log.write(
                f"\n[bold cyan]Process completed with exit code {process.returncode}[/]"
            )
            
            # Show the results in the TUI from the formatted txt file
            txt_file = os.path.join(DIRPATH, "results", "nicknames", "txt", f"{username}.txt")
            if os.path.exists(txt_file):
                log.write("\n[bold magenta]--- Final Formatted Results ---[/]")
                with open(txt_file, "r", encoding="utf-8") as f:
                    log.write(f.read())
                log.write("[bold magenta]-------------------------------[/]")
                log.write(f"[italic]Results also saved to {txt_file}[/italic]")
                
        except Exception as e:
            log.write(f"\n[bold red]Error running Snoop process: {e}[/]")
        finally:
            self.call_from_thread(self._re_enable_inputs)

    def _re_enable_inputs(self) -> None:
        self.query_one("#search-button", Button).disabled = False
        inp = self.query_one("#search-input", Input)
        inp.disabled = False
        self.query_one("#include-input", Input).disabled = False
        self.query_one("#exclude-input", Input).disabled = False
        inp.focus()
        lbl = self.query_one("#status-label", Label)
        lbl.update("\n[bold yellow]Ready for next search[/]")


def run_tui():
    app = SnoopHUD()
    app.run()


if __name__ == "__main__":
    run_tui()
