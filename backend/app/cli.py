from __future__ import annotations

from pathlib import Path

import typer
from rich.console import Console
from rich.table import Table

from app import __version__
from app.config import get_settings
from app.orchestrator import Orchestrator

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
def demo(
    edits_path: Path = typer.Option(  # noqa: B008
        Path("samples/edits/matter_delaware_health.md"),
        help="Markdown file with operator edits applied to the training matter draft.",
    ),
) -> None:
    settings = get_settings()
    orch = Orchestrator(settings)
    orch.reset_style_memory()

    plans = orch.load_matters()
    if not plans:
        console.print("[red]No matters found in data/matters.yaml[/red]")
        raise typer.Exit(code=1)

    training = next((p for p in plans if not p.matter.held_out), None)
    held_out = next((p for p in plans if p.matter.held_out), None)
    if training is None or held_out is None:
        console.print("[red]Demo requires one non-held-out matter and one held-out matter.[/red]")
        raise typer.Exit(code=1)

    console.rule("[bold]1. Ingest + process + index")
    for plan in (training, held_out):
        orch.ingest_and_process(plan)
        orch.index(plan.matter)
        console.print(f"  {plan.matter.matter_id}: {len(plan.matter.document_ids)} docs ready")

    console.rule("[bold]2. Draft training matter (style memory v0)")
    style_v0 = orch.current_style_memory()
    training_bundle = orch.draft(training.matter, style_v0)
    console.print(f"  draft {training_bundle.draft.draft_id} written")

    console.rule("[bold]3. Apply operator edits → style memory v1")
    edited_markdown = edits_path.read_text(encoding="utf-8")
    style_v1 = orch.apply_edit(
        training_bundle,
        edited_markdown,
        matter_type=training.matter.matter_type,
        matter_id=training.matter.matter_id,
    )
    console.print(
        f"  learned: {len(style_v1.terminology_map)} terminology entries, "
        f"{len(style_v1.section_rules)} section rules, "
        f"{len(style_v1.exemplar_store)} exemplars"
    )

    console.rule("[bold]4. Draft held-out matter — baseline vs learned")
    baseline_bundle = orch.draft(held_out.matter, style_v0)
    learned_bundle = orch.draft(held_out.matter, style_v1)

    console.rule("[bold]5. A/B comparison on held-out matter")
    comparison = orch.evaluate(
        matter=held_out.matter,
        baseline=baseline_bundle,
        learned=learned_bundle,
        reference_markdown=edited_markdown,
        style_memory=style_v1,
    )

    table = Table(title=f"Held-out comparison ({held_out.matter.matter_id})")
    table.add_column("Metric")
    table.add_column("Value", justify="right")
    table.add_row("Edit-distance reduction", f"{comparison.edit_distance_reduction:.2%}")
    table.add_row("Terminology adherence", f"{comparison.terminology_adherence:.2%}")
    table.add_row("Section-rule compliance", f"{comparison.section_rule_compliance:.2%}")
    table.add_row("Baseline draft", comparison.baseline_draft_id)
    table.add_row("Learned draft", comparison.learned_draft_id)
    console.print(table)


if __name__ == "__main__":
    app()
