"""Top-level CLI for the NerdFarm backend."""

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
    """Print the installed version."""
    console.print(__version__)


@app.command()
def demo() -> None:
    """Run the end-to-end demo on the bundled corpus.

    The full pipeline (ingest → process → index → retrieve → draft → audit →
    edit-loop → eval) is wired up in subsequent commits. This stub keeps the
    entry point reachable from the moment the package is installable.
    """
    console.print("[yellow]Demo entry point reserved. Implementation lands "
                  "in the orchestrator + agents commits.[/yellow]")


if __name__ == "__main__":
    app()
