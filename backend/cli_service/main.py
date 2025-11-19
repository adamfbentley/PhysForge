import typer
from . import auth_cli, dataset_cli, job_cli

app = typer.Typer(
    name="pinn-cli",
    help="Physics-Informed Scientific Discovery Platform CLI",
    rich_markup_nocolor=True
)

app.add_typer(auth_cli.app, name="auth", help="Authentication and user management commands.")
app.add_typer(dataset_cli.app, name="datasets", help="Manage scientific datasets.")
app.add_typer(job_cli.app, name="jobs", help="Manage computational jobs (PINN training, PDE discovery, etc.).")

@app.callback()
def main(ctx: typer.Context):
    """Physics-Informed Scientific Discovery Platform CLI."""
    pass

if __name__ == "__main__":
    app()
