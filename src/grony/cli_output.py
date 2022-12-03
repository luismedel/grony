
import click


def info(message: str) -> None:
    print(message)


def success(message: str) -> None:
    click.secho(message, fg='cyan')


def err(message: str) -> None:
    click.secho(f'Error: {message}', fg='red')


def warn(message: str) -> None:
    click.secho(f'Warning: {message}', fg='yellow')


def fatal(message: str, exit_code: int = 1) -> None:
    click.secho(f'Fatal: {message}', fg='red')
    exit(exit_code)
