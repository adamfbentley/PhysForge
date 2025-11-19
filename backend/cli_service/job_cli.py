import typer
import httpx
import json
from rich.console import Console
from rich.table import Table
from rich.syntax import Syntax
from pathlib import Path
from typing_extensions import Annotated, Optional
from .config import settings
from .utils import get_authenticated_client, handle_response_errors

app = typer.Typer(help="Manage computational jobs (PINN training, PDE discovery, etc.).")
console = Console()

@app.command(name="list")
def list_jobs(
    status: Annotated[Optional[str], typer.Option("--status", "-s", help="Filter jobs by status (e.g., PENDING, RUNNING, COMPLETED, FAILED).")] = None
):
    """List all jobs owned by the current user."""
    console.print("[bold green]Fetching jobs...[/bold green]")
    try:
        client = get_authenticated_client()
        params = {"status": status} if status else {}
        response = client.get(f"{settings.JOB_ORCHESTRATION_SERVICE_URL}/jobs/", params=params)
        handle_response_errors(response)
        jobs = response.json()

        if not jobs:
            console.print("No jobs found.")
            return

        table = Table(title="Your Jobs")
        table.add_column("ID", style="cyan", no_wrap=True)
        table.add_column("Type", style="magenta")
        table.add_column("Status", style="green")
        table.add_column("Progress", style="blue")
        table.add_column("Created At", style="dim")
        table.add_column("Completed At", style="dim")
        table.add_column("Error", style="red")

        for job in jobs:
            status_style = "green" if job['status'] == 'COMPLETED' else "yellow" if job['status'] == 'RUNNING' else "red" if job['status'] == 'FAILED' else "blue"
            table.add_row(
                str(job['id']),
                job['job_type'],
                f"[{status_style}]{job['status']}[/{status_style}]",
                f"{job['progress']}%",
                job['created_at'].split('T')[0],
                job['completed_at'].split('T')[0] if job['completed_at'] else "N/A",
                job['error_message'] or ""
            )
        console.print(table)

    except httpx.HTTPStatusError as e:
        console.print(f"[bold red]Failed to list jobs: {e.response.json().get('detail', str(e))}[/bold red]")
    except Exception as e:
        console.print(f"[bold red]An unexpected error occurred: {e}[/bold red]")

@app.command()
def status(
    job_id: Annotated[int, typer.Argument(help="The ID of the job to retrieve status for.")]
):
    """Get the status and details of a specific job."""
    console.print(f"[bold green]Fetching status for job ID: {job_id}...[/bold green]")
    try:
        client = get_authenticated_client()
        response = client.get(f"{settings.JOB_ORCHESTRATION_SERVICE_URL}/jobs/{job_id}")
        handle_response_errors(response)
        job_data = response.json()

        console.print(f"[bold green]Job Details (ID: {job_data['id']}):[/bold green]")
        console.print(f"  [cyan]Type:[/cyan] {job_data['job_type']}")
        console.print(f"  [cyan]Status:[/cyan] {job_data['status']}")
        console.print(f"  [cyan]Progress:[/cyan] {job_data['progress']}%")
        console.print(f"  [cyan]Created At:[/cyan] {job_data['created_at']}")
        console.print(f"  [cyan]Started At:[/cyan] {job_data['started_at'] or 'N/A'}")
        console.print(f"  [cyan]Completed At:[/cyan] {job_data['completed_at'] or 'N/A'}")
        console.print(f"  [cyan]Error Message:[/cyan] {job_data['error_message'] or 'None'}")
        console.print(f"  [cyan]Results Path:[/cyan] {job_data['results_path'] or 'None'}")
        console.print(f"  [cyan]Logs Path:[/cyan] {job_data['logs_path'] or 'None'}")
        if job_data.get('feature_library_path'):
            console.print(f"  [cyan]Feature Library Path:[/cyan] {job_data['feature_library_path']}")
        if job_data.get('canonical_equation'):
            console.print(f"  [cyan]Canonical Equation:[/cyan] {job_data['canonical_equation']}")
        if job_data.get('model_ranking_score') is not None:
            console.print(f"  [cyan]Model Ranking Score:[/cyan] {job_data['model_ranking_score']}")
        if job_data.get('equation_metrics'):
            console.print("[cyan]  Equation Metrics:[/cyan]")
            console.print(Syntax(json.dumps(job_data['equation_metrics'], indent=2), "json", theme="monokai", line_numbers=False))
        if job_data.get('uncertainty_metrics'):
            console.print("[cyan]  Uncertainty Metrics:[/cyan]")
            console.print(Syntax(json.dumps(job_data['uncertainty_metrics'], indent=2), "json", theme="monokai", line_numbers=False))
        if job_data.get('sensitivity_analysis_results_path'):
            console.print(f"  [cyan]Sensitivity Analysis Results Path:[/cyan] {job_data['sensitivity_analysis_results_path']}")

        console.print("[bold yellow]Status Logs:[/bold yellow]")
        if job_data['status_logs']:
            for log in job_data['status_logs']:
                console.print(f"  - {log['timestamp']}: {log['status']} - {log['message'] or ''}")
        else:
            console.print("  No status logs available.")

    except httpx.HTTPStatusError as e:
        console.print(f"[bold red]Failed to get job status: {e.response.json().get('detail', str(e))}[/bold red]")
    except Exception as e:
        console.print(f"[bold red]An unexpected error occurred: {e}[/bold red]")

@app.command()
def logs(
    job_id: Annotated[int, typer.Argument(help="The ID of the job to retrieve logs for.")]
):
    """Retrieve the logs for a specific job."""
    console.print(f"[bold green]Fetching logs for job ID: {job_id}...[/bold green]")
    try:
        client = get_authenticated_client()
        response = client.get(f"{settings.JOB_ORCHESTRATION_SERVICE_URL}/jobs/{job_id}/logs")
        handle_response_errors(response)
        log_data = response.json()

        if log_data['logs']:
            console.print("[bold yellow]Job Logs:[/bold yellow]")
            for line in log_data['logs']:
                console.print(line)
        else:
            console.print(f"[bold yellow]{log_data.get('message', 'No logs available.')}[/bold yellow]")

    except httpx.HTTPStatusError as e:
        console.print(f"[bold red]Failed to get job logs: {e.response.json().get('detail', str(e))}[/bold red]")
    except Exception as e:
        console.print(f"[bold red]An unexpected error occurred: {e}[/bold red]")

@app.command(name="submit-pinn-training")
def submit_pinn_training_job(
    config_file: Annotated[Path, typer.Argument(exists=True, file_okay=True, dir_okay=False, readable=True, resolve_path=True, help="Path to a JSON file containing the PINN training configuration.")]
):
    """Submit a new PINN training job."""
    console.print(f"[bold green]Submitting PINN training job from '{config_file}'...[/bold green]")
    try:
        client = get_authenticated_client()
        with open(config_file, 'r') as f:
            config = json.load(f)
        
        job_payload = {"job_type": "pinn_training", "config": config}
        response = client.post(
            f"{settings.JOB_ORCHESTRATION_SERVICE_URL}/jobs/pinn-training",
            json=job_payload
        )
        handle_response_errors(response)
        job_data = response.json()
        console.print(f"[bold green]PINN Training Job submitted successfully! Job ID: {job_data['id']}[/bold green]")
        console.print(f"Current Status: {job_data['status']}")

    except httpx.HTTPStatusError as e:
        console.print(f"[bold red]Failed to submit PINN training job: {e.response.json().get('detail', str(e))}[/bold red]")
    except json.JSONDecodeError:
        console.print(f"[bold red]Error: Invalid JSON in config file '{config_file}'.[/bold red]")
    except Exception as e:
        console.print(f"[bold red]An unexpected error occurred: {e}[/bold red]")

@app.command(name="submit-derivatives")
def submit_derivative_job(
    config_file: Annotated[Path, typer.Argument(exists=True, file_okay=True, dir_okay=False, readable=True, resolve_path=True, help="Path to a JSON file containing the derivative computation configuration.")]
):
    """Submit a new derivative computation job."""
    console.print(f"[bold green]Submitting derivative computation job from '{config_file}'...[/bold green]")
    try:
        client = get_authenticated_client()
        with open(config_file, 'r') as f:
            config = json.load(f)
        
        job_payload = {"job_type": "derivative_computation", "config": config}
        response = client.post(
            f"{settings.JOB_ORCHESTRATION_SERVICE_URL}/jobs/derivatives",
            json=job_payload
        )
        handle_response_errors(response)
        job_data = response.json()
        console.print(f"[bold green]Derivative Computation Job submitted successfully! Job ID: {job_data['id']}[/bold green]")
        console.print(f"Current Status: {job_data['status']}")

    except httpx.HTTPStatusError as e:
        console.print(f"[bold red]Failed to submit derivative job: {e.response.json().get('detail', str(e))}[/bold red]")
    except json.JSONDecodeError:
        console.print(f"[bold red]Error: Invalid JSON in config file '{config_file}'.[/bold red]")
    except Exception as e:
        console.print(f"[bold red]An unexpected error occurred: {e}[/bold red]")

@app.command(name="submit-pde-discovery")
def submit_pde_discovery_job(
    config_file: Annotated[Path, typer.Argument(exists=True, file_okay=True, dir_okay=False, readable=True, resolve_path=True, help="Path to a JSON file containing the PDE discovery configuration.")]
):
    """Submit a new PDE discovery job."""
    console.print(f"[bold green]Submitting PDE discovery job from '{config_file}'...[/bold green]")
    try:
        client = get_authenticated_client()
        with open(config_file, 'r') as f:
            config = json.load(f)
        
        job_payload = {"job_type": "pde_discovery", "config": config}
        response = client.post(
            f"{settings.JOB_ORCHESTRATION_SERVICE_URL}/jobs/pde-discovery",
            json=job_payload
        )
        handle_response_errors(response)
        job_data = response.json()
        console.print(f"[bold green]PDE Discovery Job submitted successfully! Job ID: {job_data['id']}[/bold green]")
        console.print(f"Current Status: {job_data['status']}")

    except httpx.HTTPStatusError as e:
        console.print(f"[bold red]Failed to submit PDE discovery job: {e.response.json().get('detail', str(e))}[/bold red]")
    except json.JSONDecodeError:
        console.print(f"[bold red]Error: Invalid JSON in config file '{config_file}'.[/bold red]")
    except Exception as e:
        console.print(f"[bold red]An unexpected error occurred: {e}[/bold red]")

@app.command(name="cancel")
def cancel_job(
    job_id: Annotated[int, typer.Argument(help="The ID of the job to cancel.")]
):
    """Cancel a running job."""
    console.print(f"[bold yellow]Cancelling job ID: {job_id}...[/bold yellow]")
    try:
        client = get_authenticated_client()
        response = client.post(f"{settings.JOB_ORCHESTRATION_SERVICE_URL}/jobs/{job_id}/cancel")
        handle_response_errors(response)
        console.print(f"[bold green]Job {job_id} cancelled successfully![/bold green]")

    except httpx.HTTPStatusError as e:
        console.print(f"[bold red]Failed to cancel job: {e.response.json().get('detail', str(e))}[/bold red]")
    except Exception as e:
        console.print(f"[bold red]An unexpected error occurred: {e}[/bold red]")

@app.command(name="batch-submit")
def batch_submit_jobs(
    config_file: Annotated[Path, typer.Argument(exists=True, file_okay=True, dir_okay=False, readable=True, resolve_path=True, help="Path to a JSON file containing batch job configurations.")]
):
    """Submit multiple jobs from a batch configuration file."""
    console.print(f"[bold green]Submitting batch jobs from '{config_file}'...[/bold green]")
    try:
        with open(config_file, 'r') as f:
            batch_config = json.load(f)

        if not isinstance(batch_config, list):
            console.print("[bold red]Error: Batch config must be a JSON array of job configurations.[/bold red]")
            return

        client = get_authenticated_client()
        submitted_jobs = []

        for i, job_config in enumerate(batch_config, 1):
            console.print(f"[bold blue]Submitting job {i}/{len(batch_config)}...[/bold blue]")

            if 'job_type' not in job_config:
                console.print(f"[bold red]Error: Job {i} missing 'job_type' field. Skipping.[/bold red]")
                continue

            job_type = job_config['job_type']
            endpoint_map = {
                'pinn_training': 'pinn-training',
                'derivatives': 'derivatives',
                'pde_discovery': 'pde-discovery',
                'active_experiment': 'active-experiment'
            }

            if job_type not in endpoint_map:
                console.print(f"[bold red]Error: Unknown job type '{job_type}' for job {i}. Skipping.[/bold red]")
                continue

            try:
                response = client.post(
                    f"{settings.JOB_ORCHESTRATION_SERVICE_URL}/jobs/{endpoint_map[job_type]}",
                    json=job_config
                )
                handle_response_errors(response)
                job_data = response.json()
                submitted_jobs.append(job_data)
                console.print(f"[bold green]Job {i} submitted successfully! Job ID: {job_data['id']}[/bold green]")

            except Exception as e:
                console.print(f"[bold red]Failed to submit job {i}: {e}[/bold red]")

        console.print(f"\n[bold green]Batch submission complete! {len(submitted_jobs)}/{len(batch_config)} jobs submitted.[/bold green]")
        if submitted_jobs:
            console.print("Submitted job IDs:", [job['id'] for job in submitted_jobs])

    except json.JSONDecodeError:
        console.print(f"[bold red]Error: Invalid JSON in batch config file '{config_file}'.[/bold red]")
    except Exception as e:
        console.print(f"[bold red]An unexpected error occurred: {e}[/bold red]")

@app.command(name="watch")
def watch_job(
    job_id: Annotated[int, typer.Argument(help="The ID of the job to watch.")],
    interval: Annotated[int, typer.Option("--interval", "-i", help="Polling interval in seconds.")] = 5
):
    """Watch a job's progress in real-time."""
    import time

    console.print(f"[bold green]Watching job ID: {job_id} (polling every {interval}s)...[/bold green]")
    console.print("Press Ctrl+C to stop watching.\n")

    try:
        client = get_authenticated_client()
        last_status = None

        while True:
            try:
                response = client.get(f"{settings.JOB_ORCHESTRATION_SERVICE_URL}/jobs/{job_id}")
                handle_response_errors(response)
                job_data = response.json()

                current_status = job_data['status']
                progress = job_data['progress']

                if current_status != last_status:
                    status_style = "green" if current_status == 'COMPLETED' else "yellow" if current_status == 'RUNNING' else "red" if current_status == 'FAILED' else "blue"
                    console.print(f"[{status_style}]Status changed: {current_status}[/{status_style}]")
                    last_status = current_status

                if current_status in ['COMPLETED', 'FAILED']:
                    console.print(f"[bold green]Job finished with status: {current_status}[/bold green]")
                    if job_data.get('error_message'):
                        console.print(f"[bold red]Error: {job_data['error_message']}[/bold red]")
                    break

                # Show progress bar
                bar_width = 40
                filled = int(bar_width * progress / 100)
                bar = "█" * filled + "░" * (bar_width - filled)
                console.print(f"\rProgress: [{bar}] {progress}%", end="", flush=True)

                time.sleep(interval)

            except KeyboardInterrupt:
                console.print(f"\n[bold yellow]Stopped watching job {job_id}[/bold yellow]")
                break
            except Exception as e:
                console.print(f"\n[bold red]Error polling job status: {e}[/bold red]")
                time.sleep(interval)

    except Exception as e:
        console.print(f"[bold red]Failed to watch job: {e}[/bold red]")
