"""
Command-line interface for the BP Health Coach.
"""
import typer
from rich.console import Console
from rich.panel import Panel
from rich.markdown import Markdown
from typing import Optional

from src.features.query_answering import QueryEngine
from src.features.daily_briefing import DailyBriefingGenerator
from src.features.scenario_testing import ScenarioEngine
from src.data.database import init_database

# Initialize
app = typer.Typer(help="BP Health Coach - AI-powered health coaching")
console = Console()


@app.command()
def chat(session_id: Optional[str] = None):
    """
    Start an interactive chat session with the health coach.
    """
    init_database()
    engine = QueryEngine(session_id)

    console.print(Panel(
        "[bold blue]BP Health Coach[/bold blue]\n"
        "Ask me about your blood pressure, sleep, activity, and more.\n"
        "Type 'quit' or 'exit' to end the session.",
        title="Welcome"
    ))
    console.print(f"[dim]Session ID: {engine.get_session_id()}[/dim]\n")

    while True:
        try:
            query = console.input("[bold green]You:[/bold green] ")

            if query.lower() in ('quit', 'exit', 'q'):
                console.print("\n[yellow]Goodbye! Take care of your health.[/yellow]")
                break

            if not query.strip():
                continue

            # Show thinking indicator
            with console.status("[bold blue]Thinking...[/bold blue]"):
                result = engine.ask_with_metadata(query)

            # Display response
            console.print(f"\n[bold blue]Coach:[/bold blue] {result['response']}\n")
            console.print(f"[dim]({result['intent']} | {result.get('model_used', 'unknown')} | {result.get('tokens', 0)} tokens)[/dim]\n")

        except KeyboardInterrupt:
            console.print("\n[yellow]Session interrupted. Goodbye![/yellow]")
            break
        except Exception as e:
            console.print(f"[red]Error: {e}[/red]")


@app.command()
def briefing():
    """
    Generate and display today's health briefing.
    """
    init_database()
    generator = DailyBriefingGenerator()

    with console.status("[bold blue]Generating briefing...[/bold blue]"):
        content = generator.generate_briefing()

    console.print(Panel(content, title="Daily Briefing", border_style="blue"))


@app.command()
def scenario(
    vo2: Optional[float] = typer.Option(None, help="Target VO2 Max"),
    sleep: Optional[float] = typer.Option(None, help="Target sleep hours"),
    steps: Optional[int] = typer.Option(None, help="Target daily steps")
):
    """
    Test a what-if scenario.

    Example: bp-coach scenario --vo2 42 --sleep 8
    """
    init_database()
    engine = ScenarioEngine()

    # Build changes dict
    changes = {}
    if vo2 is not None:
        changes['vo2_max'] = vo2
    if sleep is not None:
        changes['sleep_hours'] = sleep
    if steps is not None:
        changes['steps'] = steps

    if not changes:
        console.print("[red]Please specify at least one change (--vo2, --sleep, or --steps)[/red]")
        raise typer.Exit(1)

    with console.status("[bold blue]Analyzing scenario...[/bold blue]"):
        result = engine.test_scenario(changes)

    # Format and display
    output = f"""
**Scenario Analysis**

**Changes:** {changes}

**Predicted Impact:**
- Current BP: {result.current_bp:.0f} mmHg
- Predicted BP: {result.predicted_bp:.0f} mmHg
- Change: {result.bp_change:+.1f} mmHg
- 95% CI: {result.confidence_interval[0]:.0f} to {result.confidence_interval[1]:.0f} mmHg

**Timeline:** {result.timeline_weeks} weeks
**Feasibility:** {result.feasibility}

**Recommendations:**
"""
    for rec in result.recommendations:
        output += f"- {rec}\n"

    console.print(Panel(Markdown(output), title="Scenario Results", border_style="green"))


@app.command()
def ask(query: str):
    """
    Ask a single question (non-interactive).

    Example: bp-coach ask "What was my BP yesterday?"
    """
    init_database()
    engine = QueryEngine()

    with console.status("[bold blue]Thinking...[/bold blue]"):
        response = engine.ask(query)

    console.print(Panel(response, title="Health Coach", border_style="blue"))


def main():
    """Entry point for the CLI."""
    app()


if __name__ == "__main__":
    main()
