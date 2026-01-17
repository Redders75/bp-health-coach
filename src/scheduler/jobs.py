"""
Scheduled jobs for the BP Health Coach.

Handles automated tasks like:
- Daily briefing generation (8 AM)
- Weekly report generation (Monday mornings)
- Alert checks (every few hours)
- Data sync reminders
"""
import schedule
import time
import logging
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Optional, Callable
import threading

from src.features.daily_briefing import DailyBriefingGenerator
from src.features.weekly_report import WeeklyReportGenerator
from src.features.alerts import AlertEngine
from src.data.database import get_connection

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class Scheduler:
    """Manages scheduled health coach jobs."""

    def __init__(self, output_dir: Optional[Path] = None):
        """
        Initialize the scheduler.

        Args:
            output_dir: Directory to save generated reports
        """
        self.output_dir = output_dir or Path.home() / '.bp-health-coach' / 'reports'
        self.output_dir.mkdir(parents=True, exist_ok=True)

        self.briefing_generator = DailyBriefingGenerator()
        self.report_generator = WeeklyReportGenerator()
        self.alert_engine = AlertEngine()

        self._init_schedule_table()
        self._running = False
        self._thread: Optional[threading.Thread] = None

    def _init_schedule_table(self):
        """Initialize table to track scheduled job runs."""
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS scheduled_jobs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    job_name TEXT NOT NULL,
                    run_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    status TEXT NOT NULL,
                    output_file TEXT,
                    error_message TEXT
                )
            """)
            conn.commit()

    def setup_default_schedule(self):
        """Set up the default job schedule."""
        # Clear any existing schedule
        schedule.clear()

        # Daily briefing at 8 AM
        schedule.every().day.at("08:00").do(self.run_daily_briefing)

        # Weekly report on Monday at 7 AM
        schedule.every().monday.at("07:00").do(self.run_weekly_report)

        # Alert checks every 4 hours
        schedule.every(4).hours.do(self.run_alert_check)

        logger.info("Default schedule configured:")
        logger.info("  - Daily briefing: 8:00 AM")
        logger.info("  - Weekly report: Monday 7:00 AM")
        logger.info("  - Alert checks: Every 4 hours")

    def run_daily_briefing(self) -> str:
        """
        Generate and save the daily briefing.

        Returns:
            Path to the saved briefing file
        """
        logger.info("Running daily briefing job...")

        try:
            briefing = self.briefing_generator.generate_briefing()

            # Save to file
            today = date.today()
            filename = f"briefing_{today.isoformat()}.txt"
            filepath = self.output_dir / filename

            with open(filepath, 'w') as f:
                f.write(briefing)

            # Log success
            self._log_job_run('daily_briefing', 'success', str(filepath))

            logger.info(f"Daily briefing saved to {filepath}")

            # Also run alert check after briefing
            self.run_alert_check()

            return str(filepath)

        except Exception as e:
            logger.error(f"Daily briefing failed: {e}")
            self._log_job_run('daily_briefing', 'error', error=str(e))
            raise

    def run_weekly_report(self) -> str:
        """
        Generate and save the weekly report.

        Returns:
            Path to the saved report file
        """
        logger.info("Running weekly report job...")

        try:
            report = self.report_generator.generate_report()

            # Save to file
            today = date.today()
            week_start = today - timedelta(days=today.weekday())
            filename = f"weekly_report_{week_start.isoformat()}.txt"
            filepath = self.output_dir / filename

            with open(filepath, 'w') as f:
                f.write(report)

            # Log success
            self._log_job_run('weekly_report', 'success', str(filepath))

            logger.info(f"Weekly report saved to {filepath}")
            return str(filepath)

        except Exception as e:
            logger.error(f"Weekly report failed: {e}")
            self._log_job_run('weekly_report', 'error', error=str(e))
            raise

    def run_alert_check(self) -> int:
        """
        Run alert checks and return number of new alerts.

        Returns:
            Number of alerts generated
        """
        logger.info("Running alert check...")

        try:
            alerts = self.alert_engine.check_all()

            alert_count = len(alerts)
            self._log_job_run('alert_check', 'success')

            if alert_count > 0:
                logger.info(f"Generated {alert_count} new alerts")
                for alert in alerts:
                    logger.info(f"  - [{alert.priority.value}] {alert.title}")
            else:
                logger.info("No new alerts")

            return alert_count

        except Exception as e:
            logger.error(f"Alert check failed: {e}")
            self._log_job_run('alert_check', 'error', error=str(e))
            raise

    def _log_job_run(
        self,
        job_name: str,
        status: str,
        output_file: str = None,
        error: str = None
    ):
        """Log a job run to the database."""
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """INSERT INTO scheduled_jobs
                   (job_name, status, output_file, error_message)
                   VALUES (?, ?, ?, ?)""",
                (job_name, status, output_file, error)
            )
            conn.commit()

    def get_job_history(self, job_name: str = None, limit: int = 10) -> list:
        """Get history of scheduled job runs."""
        with get_connection() as conn:
            cursor = conn.cursor()

            if job_name:
                cursor.execute(
                    """SELECT * FROM scheduled_jobs
                       WHERE job_name = ?
                       ORDER BY run_time DESC
                       LIMIT ?""",
                    (job_name, limit)
                )
            else:
                cursor.execute(
                    """SELECT * FROM scheduled_jobs
                       ORDER BY run_time DESC
                       LIMIT ?""",
                    (limit,)
                )

            return [dict(row) for row in cursor.fetchall()]

    def start(self, blocking: bool = True):
        """
        Start the scheduler.

        Args:
            blocking: If True, blocks the main thread. If False, runs in background.
        """
        self.setup_default_schedule()
        self._running = True

        if blocking:
            logger.info("Starting scheduler (blocking mode)...")
            self._run_loop()
        else:
            logger.info("Starting scheduler (background mode)...")
            self._thread = threading.Thread(target=self._run_loop, daemon=True)
            self._thread.start()

    def stop(self):
        """Stop the scheduler."""
        self._running = False
        if self._thread:
            self._thread.join(timeout=5)
        logger.info("Scheduler stopped")

    def _run_loop(self):
        """Main scheduler loop."""
        while self._running:
            schedule.run_pending()
            time.sleep(60)  # Check every minute

    def run_now(self, job_name: str) -> str:
        """
        Run a specific job immediately.

        Args:
            job_name: One of 'daily_briefing', 'weekly_report', 'alert_check'

        Returns:
            Result of the job
        """
        jobs = {
            'daily_briefing': self.run_daily_briefing,
            'weekly_report': self.run_weekly_report,
            'alert_check': self.run_alert_check
        }

        if job_name not in jobs:
            raise ValueError(f"Unknown job: {job_name}. Available: {list(jobs.keys())}")

        return jobs[job_name]()

    def get_next_run_times(self) -> dict:
        """Get the next scheduled run time for each job."""
        jobs = schedule.get_jobs()
        next_runs = {}

        for job in jobs:
            # Extract job name from the function
            if hasattr(job.job_func, '__name__'):
                name = job.job_func.__name__
            else:
                name = str(job.job_func)

            next_runs[name] = job.next_run

        return next_runs


def run_scheduler():
    """Entry point to run the scheduler."""
    scheduler = Scheduler()

    # Run initial checks
    logger.info("Running initial alert check...")
    scheduler.run_alert_check()

    # Start the scheduler
    scheduler.start(blocking=True)


def run_job_once(job_name: str):
    """Run a specific job once and exit."""
    scheduler = Scheduler()
    result = scheduler.run_now(job_name)
    print(f"Job '{job_name}' completed. Result: {result}")
    return result


if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1:
        # Run specific job
        job = sys.argv[1]
        run_job_once(job)
    else:
        # Run scheduler
        run_scheduler()
