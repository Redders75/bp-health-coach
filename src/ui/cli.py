"""
Command-line interface for the BP Health Coach.
"""
import typer
from rich.console import Console
from rich.panel import Panel
from rich.markdown import Markdown
from rich.table import Table
from typing import Optional
from datetime import date, timedelta

from src.features.query_answering import QueryEngine
from src.features.daily_briefing import DailyBriefingGenerator
from src.features.scenario_testing import ScenarioEngine
from src.features.weekly_report import WeeklyReportGenerator
from src.features.alerts import AlertEngine
from src.features.goal_tracking import GoalTracker
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
def weekly(
    weeks_ago: int = typer.Option(0, help="Number of weeks ago (0 = last week)")
):
    """
    Generate a weekly health report.

    Example: bp-coach weekly --weeks-ago 1
    """
    init_database()
    generator = WeeklyReportGenerator()

    # Calculate week end date
    today = date.today()
    week_end = today - timedelta(days=today.weekday() + 1)  # Last Sunday
    week_end = week_end - timedelta(weeks=weeks_ago)

    with console.status("[bold blue]Generating weekly report...[/bold blue]"):
        content = generator.generate_report(week_end)

    console.print(Panel(content, title="Weekly Report", border_style="green"))


@app.command()
def goals():
    """
    Display the goal tracking dashboard.
    """
    init_database()
    tracker = GoalTracker()

    with console.status("[bold blue]Loading goals...[/bold blue]"):
        output = tracker.format_dashboard_text()

    console.print(output)


@app.command()
def alerts(
    check: bool = typer.Option(False, "--check", "-c", help="Run alert checks now"),
    days: int = typer.Option(7, help="Show alerts from last N days")
):
    """
    View and manage health alerts.

    Example: bp-coach alerts --check
    """
    init_database()
    engine = AlertEngine()

    if check:
        with console.status("[bold blue]Checking for alerts...[/bold blue]"):
            new_alerts = engine.check_all()

        if new_alerts:
            console.print(f"[green]Generated {len(new_alerts)} new alert(s)[/green]\n")
            for alert in new_alerts:
                priority_colors = {
                    'critical': 'red',
                    'warning': 'yellow',
                    'info': 'blue',
                    'celebration': 'green'
                }
                color = priority_colors.get(alert.priority.value, 'white')
                console.print(Panel(
                    alert.message,
                    title=f"[{color}]{alert.title}[/{color}]",
                    border_style=color
                ))
        else:
            console.print("[green]No new alerts[/green]")
        return

    # Show existing alerts
    recent_alerts = engine.get_recent_alerts(days=days)

    if not recent_alerts:
        console.print(f"[dim]No alerts in the last {days} days[/dim]")
        return

    table = Table(title=f"Alerts (Last {days} Days)")
    table.add_column("Priority", style="bold")
    table.add_column("Title")
    table.add_column("Message")
    table.add_column("Date")
    table.add_column("Status")

    priority_icons = {
        'critical': '[red]🔴[/red]',
        'warning': '[yellow]🟠[/yellow]',
        'info': '[blue]🔵[/blue]',
        'celebration': '[green]🎉[/green]'
    }

    for alert in recent_alerts:
        icon = priority_icons.get(alert['priority'], '📢')
        status = "✓ Seen" if alert['acknowledged'] else "[bold]NEW[/bold]"
        created = alert['created_at'][:10] if alert['created_at'] else 'N/A'

        table.add_row(
            icon,
            alert['title'],
            alert['message'][:50] + "..." if len(alert['message']) > 50 else alert['message'],
            created,
            status
        )

    console.print(table)


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
- Current BP: {result.current_systolic:.0f}/{result.current_diastolic:.0f} mmHg
- Predicted BP: {result.predicted_systolic:.0f}/{result.predicted_diastolic:.0f} mmHg
- Change: {result.bp_change:+.1f}/{result.diastolic_change:+.1f} mmHg
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


@app.command()
def scheduler(
    run: Optional[str] = typer.Option(None, help="Run a specific job: daily_briefing, weekly_report, alert_check"),
    start: bool = typer.Option(False, "--start", "-s", help="Start the scheduler daemon")
):
    """
    Manage scheduled jobs.

    Example: bp-coach scheduler --run daily_briefing
    Example: bp-coach scheduler --start
    """
    init_database()

    if run:
        from src.scheduler.jobs import run_job_once
        console.print(f"[blue]Running job: {run}[/blue]")
        try:
            result = run_job_once(run)
            console.print(f"[green]Job completed successfully[/green]")
            console.print(f"Result: {result}")
        except Exception as e:
            console.print(f"[red]Job failed: {e}[/red]")
        return

    if start:
        from src.scheduler.jobs import run_scheduler
        console.print("[blue]Starting scheduler...[/blue]")
        console.print("[dim]Press Ctrl+C to stop[/dim]")
        try:
            run_scheduler()
        except KeyboardInterrupt:
            console.print("\n[yellow]Scheduler stopped[/yellow]")
        return

    # Show scheduler status
    console.print(Panel(
        "[bold]Available Jobs:[/bold]\n"
        "• daily_briefing - Morning health briefing (8 AM)\n"
        "• weekly_report - Weekly summary (Monday 7 AM)\n"
        "• alert_check - Check for health alerts (every 4 hours)\n\n"
        "[bold]Usage:[/bold]\n"
        "• Run a job now: [cyan]bp-coach scheduler --run daily_briefing[/cyan]\n"
        "• Start daemon: [cyan]bp-coach scheduler --start[/cyan]",
        title="Scheduler",
        border_style="blue"
    ))


def main():
    """Entry point for the CLI."""
    app()


if __name__ == "__main__":
    main()
