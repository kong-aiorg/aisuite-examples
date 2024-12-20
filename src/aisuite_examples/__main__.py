"""Command-line interface."""
import click


@click.command()
@click.version_option()
def main() -> None:
    """Aisuite Examples."""


if __name__ == "__main__":
    main(prog_name="aisuite-examples")  # pragma: no cover
