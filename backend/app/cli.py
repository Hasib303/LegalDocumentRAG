from __future__ import annotations

import typer
from rich.console import Console

from app import __version__

app = typer.Typer(
    name="nerdfarm",
    help="Agentic legal-document AI workflow.",
    no_args_is_help=True,
    add_completion=False,
)
console = Console()


@app.command()
def version() -> None:
    console.print(__version__)


@app.command()
def demo() -> None:
    console.print("[yellow]Demo entry point reserved. Implementation lands "
                  "in the orchestrator + agents commits.[/yellow]")


if __name__ == "__main__":
    app()
