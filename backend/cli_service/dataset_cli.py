import typer
import httpx
from rich.console import Console
from rich.table import Table
from pathlib import Path
from typing_extensions import Annotated
from .config import settings
from .utils import get_authenticated_client, handle_response_errors

app = typer.Typer(help="Manage scientific datasets.")
console = Console()

@app.command(name="list")
def list_datasets():
    """List all datasets owned by the current user."""
    console.print("[bold green]Fetching datasets...[/bold green]")
    try:
        client = get_authenticated_client()
        response = client.get(f"{settings.DATA_MANAGEMENT_SERVICE_URL}/datasets/")
        handle_response_errors(response)
        datasets = response.json()

        if not datasets:
            console.print("No datasets found.")
            return

        table = Table(title="Your Datasets")
        table.add_column("ID", style="cyan", no_wrap=True)
        table.add_column("Name", style="magenta")
        table.add_column("Description", style="green")
        table.add_column("Owner ID", style="blue")
        table.add_column("Latest Version", style="yellow")
        table.add_column("Uploaded At", style="dim")

        for ds in datasets:
            latest_version = ds.get('latest_version')
            version_info = f"V{latest_version['version_number']} (ID: {latest_version['id']})" if latest_version else "N/A"
            uploaded_at = latest_version['uploaded_at'].split('T')[0] if latest_version else "N/A"
            table.add_row(
                str(ds['id']),
                ds['name'],
                ds['description'] or "",
                str(ds['owner_id']),
                version_info,
                uploaded_at
            )
        console.print(table)

    except httpx.HTTPStatusError as e:
        console.print(f"[bold red]Failed to list datasets: {e.response.json().get('detail', str(e))}[/bold red]")
    except Exception as e:
        console.print(f"[bold red]An unexpected error occurred: {e}[/bold red]")

@app.command()
def upload(
    file_path: Annotated[Path, typer.Argument(exists=True, file_okay=True, dir_okay=False, writable=False, readable=True, resolve_path=True, help="Path to the dataset file to upload.")],
    name: Annotated[str, typer.Option("--name", "-n", help="A unique name for the dataset.")],
    description: Annotated[str, typer.Option("--description", "-d", help="Optional description for the dataset.")] = None
):
    """Upload a new dataset."""
    console.print(f"[bold green]Uploading dataset '{name}' from '{file_path}'...[/bold green]")
    try:
        client = get_authenticated_client()
        
        with open(file_path, "rb") as f:
            files = {"file": (file_path.name, f, "application/octet-stream")}
            data = {"name": name}
            if description: data["description"] = description

            response = client.post(
                f"{settings.DATA_MANAGEMENT_SERVICE_URL}/datasets/",
                files=files,
                data=data,
                timeout=300.0 # Increased timeout for large file uploads
            )
        
        handle_response_errors(response)
        dataset_data = response.json()
        console.print(f"[bold green]Dataset '{dataset_data['name']}' (ID: {dataset_data['id']}) uploaded successfully![/bold green]")
        console.print(f"Latest Version ID: {dataset_data['latest_version']['id']}")
        console.print(f"Storage Path: {dataset_data['latest_version']['storage_path']}")

    except httpx.HTTPStatusError as e:
        console.print(f"[bold red]Failed to upload dataset: {e.response.json().get('detail', str(e))}[/bold red]")
    except Exception as e:
        console.print(f"[bold red]An unexpected error occurred during upload: {e}[/bold red]")

@app.command()
def download(
    dataset_id: Annotated[int, typer.Argument(help="The ID of the dataset to download.")],
    output_path: Annotated[Path, typer.Option("--output", "-o", help="Path to save the downloaded file.")]
):
    """Download the latest version of a dataset."""
    console.print(f"[bold green]Generating download link for dataset ID: {dataset_id}...[/bold green]")
    try:
        client = get_authenticated_client()
        response = client.get(f"{settings.DATA_MANAGEMENT_SERVICE_URL}/datasets/{dataset_id}/download_link")
        handle_response_errors(response)
        download_info = response.json()
        presigned_url = download_info["download_url"]
        
        console.print(f"[bold green]Downloading file from presigned URL...[/bold green]")
        file_response = httpx.get(presigned_url, follow_redirects=True, timeout=300.0)
        file_response.raise_for_status()

        with open(output_path, "wb") as f:
            f.write(file_response.content)
        console.print(f"[bold green]Dataset ID {dataset_id} downloaded successfully to '{output_path}'![/bold green]")

    except httpx.HTTPStatusError as e:
        console.print(f"[bold red]Failed to download dataset: {e.response.json().get('detail', str(e))}[/bold red]")
    except Exception as e:
        console.print(f"[bold red]An unexpected error occurred during download: {e}[/bold red]")

@app.command(name="batch-upload")
def batch_upload_datasets(
    directory: Annotated[Path, typer.Argument(exists=True, file_okay=False, dir_okay=True, readable=True, resolve_path=True, help="Directory containing dataset files to upload.")],
    pattern: Annotated[str, typer.Option("--pattern", "-p", help="File pattern to match (e.g., '*.csv', '*.h5').")] = "*",
    name_template: Annotated[str, typer.Option("--name-template", "-n", help="Template for dataset names (use {filename} placeholder).")] = "{filename}",
    description: Annotated[str, typer.Option("--description", "-d", help="Description for all uploaded datasets.")] = None
):
    """Upload multiple datasets from a directory."""
    import glob

    console.print(f"[bold green]Batch uploading datasets from '{directory}'...[/bold green]")

    # Find files matching pattern
    search_pattern = str(directory / pattern)
    file_paths = glob.glob(search_pattern)

    if not file_paths:
        console.print(f"[bold yellow]No files found matching pattern '{pattern}' in '{directory}'.[/bold yellow]")
        return

    console.print(f"Found {len(file_paths)} files to upload.")

    client = get_authenticated_client()
    uploaded_datasets = []

    for file_path_str in file_paths:
        file_path = Path(file_path_str)
        filename = file_path.name

        # Generate dataset name from template
        dataset_name = name_template.format(filename=filename.rsplit('.', 1)[0])

        console.print(f"[bold blue]Uploading '{filename}' as '{dataset_name}'...[/bold blue]")

        try:
            with open(file_path, "rb") as f:
                files = {"file": (filename, f, "application/octet-stream")}
                data = {"name": dataset_name}
                if description:
                    data["description"] = description

                response = client.post(
                    f"{settings.DATA_MANAGEMENT_SERVICE_URL}/datasets/",
                    files=files,
                    data=data,
                    timeout=300.0
                )

            handle_response_errors(response)
            dataset_data = response.json()
            uploaded_datasets.append(dataset_data)
            console.print(f"[bold green]✓ Uploaded as dataset ID: {dataset_data['id']}[/bold green]")

        except Exception as e:
            console.print(f"[bold red]✗ Failed to upload '{filename}': {e}[/bold red]")

    console.print(f"\n[bold green]Batch upload complete! {len(uploaded_datasets)}/{len(file_paths)} datasets uploaded.[/bold green]")

@app.command(name="info")
def dataset_info(
    dataset_id: Annotated[int, typer.Argument(help="The ID of the dataset to get information about.")]
):
    """Get detailed information about a dataset."""
    console.print(f"[bold green]Fetching information for dataset ID: {dataset_id}...[/bold green]")
    try:
        client = get_authenticated_client()
        response = client.get(f"{settings.DATA_MANAGEMENT_SERVICE_URL}/datasets/{dataset_id}")
        handle_response_errors(response)
        dataset_data = response.json()

        console.print(f"[bold green]Dataset Information (ID: {dataset_data['id']}):[/bold green]")
        console.print(f"  [cyan]Name:[/cyan] {dataset_data['name']}")
        console.print(f"  [cyan]Description:[/cyan] {dataset_data['description'] or 'None'}")
        console.print(f"  [cyan]Owner ID:[/cyan] {dataset_data['owner_id']}")
        console.print(f"  [cyan]Created At:[/cyan] {dataset_data['created_at']}")

        if dataset_data.get('versions'):
            console.print(f"  [cyan]Total Versions:[/cyan] {len(dataset_data['versions'])}")
            console.print("  [cyan]Versions:[/cyan]")
            for version in dataset_data['versions']:
                console.print(f"    - v{version['version_number']} (ID: {version['id']}) - {version['file_size']} bytes - {version['uploaded_at']}")

        if dataset_data.get('latest_version'):
            lv = dataset_data['latest_version']
            console.print(f"  [cyan]Latest Version:[/cyan] v{lv['version_number']} ({lv['file_size']} bytes)")
            console.print(f"  [cyan]Storage Path:[/cyan] {lv['storage_path']}")
            console.print(f"  [cyan]Uploaded At:[/cyan] {lv['uploaded_at']}")

    except httpx.HTTPStatusError as e:
        console.print(f"[bold red]Failed to get dataset info: {e.response.json().get('detail', str(e))}[/bold red]")
    except Exception as e:
        console.print(f"[bold red]An unexpected error occurred: {e}[/bold red]")
