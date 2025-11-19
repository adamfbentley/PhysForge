import typer
import httpx
from rich.console import Console
from rich.prompt import Prompt
from .config import settings, save_token, delete_token, load_token # Added load_token here
from .utils import handle_response_errors

app = typer.Typer(help="Authentication and user management commands.")
console = Console()

@app.command()
def register(
    email: str = typer.Option(..., "--email", "-e", help="User email"),
    password: str = typer.Option(..., "--password", "-p", help="User password", hide_input=True, confirmation_prompt=True)
):
    """Register a new user."""
    console.print(f"[bold green]Registering user: {email}[/bold green]")
    try:
        response = httpx.post(
            f"{settings.AUTH_SERVICE_URL}/auth/register",
            json={"email": email, "password": password}
        )
        handle_response_errors(response)
        user_data = response.json()
        console.print(f"[bold green]User '{user_data['email']}' registered successfully with ID: {user_data['id']}[/bold green]")
    except httpx.HTTPStatusError as e:
        console.print(f"[bold red]Registration failed: {e.response.json().get('detail', str(e))}[/bold red]")
    except Exception as e:
        console.print(f"[bold red]An unexpected error occurred during registration: {e}[/bold red]")

@app.command()
def login(
    email: str = typer.Option(..., "--email", "-e", help="User email"),
    password: str = typer.Option(..., "--password", "-p", help="User password", hide_input=True)
):
    """Login a user and save the JWT token."""
    console.print(f"[bold green]Logging in user: {email}[/bold green]")
    try:
        response = httpx.post(
            f"{settings.AUTH_SERVICE_URL}/auth/login",
            data={"username": email, "password": password}
        )
        handle_response_errors(response)
        token_data = response.json()
        save_token(token_data["access_token"])
        console.print("[bold green]Login successful. Token saved.[/bold green]")
    except httpx.HTTPStatusError as e:
        console.print(f"[bold red]Login failed: {e.response.json().get('detail', str(e))}[/bold red]")
    except Exception as e:
        console.print(f"[bold red]An unexpected error occurred during login: {e}[/bold red]")

@app.command()
def logout():
    """Clear the saved JWT token."""
    delete_token()
    console.print("[bold green]Logged out. Token cleared.[/bold green]")

@app.command()
def whoami():
    """Show current authenticated user info."""
    console.print("[bold green]Fetching current user info...[/bold green]")
    try:
        # Corrected: Call load_token() from config module directly
        token = load_token()
        if not token:
            console.print("[bold red]Error: Not logged in. Please run 'pinn-cli auth login' first.[/bold red]")
            raise typer.Exit(code=1)

        response = httpx.get(
            f"{settings.AUTH_SERVICE_URL}/auth/me",
            headers={"Authorization": f"Bearer {token}"}
        )
        handle_response_errors(response)
        user_data = response.json()
        console.print("[bold green]You are logged in as:[/bold green]")
        console.print(f"  [cyan]ID:[/cyan] {user_data['id']}")
        console.print(f"  [cyan]Email:[/cyan] {user_data['email']}")
        console.print(f"  [cyan]Active:[/cyan] {user_data['is_active']}")
        console.print(f"  [cyan]Roles:[/cyan] {', '.join([role['name'] for role in user_data['roles']]) if user_data['roles'] else 'None'}")
    except httpx.HTTPStatusError as e:
        console.print(f"[bold red]Failed to retrieve user info: {e.response.json().get('detail', str(e))}[/bold red]")
    except Exception as e:
        console.print(f"[bold red]An unexpected error occurred: {e}[/bold red]")
