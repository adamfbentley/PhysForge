import httpx
import typer
from rich.console import Console
from .config import load_token

console = Console()

def get_authenticated_client() -> httpx.Client:
    token = load_token()
    if not token:
        console.print("[bold red]Error: Not logged in. Please run 'pinn-cli auth login' first.[/bold red]")
        raise typer.Exit(code=1)
    
    return httpx.Client(headers={"Authorization": f"Bearer {token}"})

def handle_response_errors(response: httpx.Response):
    if response.is_error:
        response.raise_for_status()
