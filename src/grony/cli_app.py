import os
import click
import signal
import logging

from pathlib import Path
from urllib.error import URLError

from grony.client import Client
from grony.server import ServerThread
from grony.dotfile import load_dotfile
from grony.scheduler import SchedulerThread
from grony.cli_output import info, success, err, warn, fatal

from tabulate import tabulate

from typing import Any, Dict, List, Optional


HOME_DIR = Path.home()
DEFAULT_CONF = Path.joinpath(HOME_DIR, '.grony.conf')


def _is_success(result: Dict[str, Any]) -> bool:
    messages: Optional[List[Dict[str, str]]] = result.get('messages', None)
    if not messages:
        return False

    for m in messages:
        severity: str = m.get('severity', 'info')
        if severity.startswith('err'):
            return False

    return True


def _display_result(result: Dict[str, Any]) -> None:
    messages: List[Dict[str, str]] = result.get('messages', [])
    if not messages:
        fatal(f'Unknown error received from server: {str(result)}')
        return

    for msg in messages:
        severity: str = msg.get('severity', 'info')
        message = msg.get('message', '<Missing message>')

        fn = info if severity.startswith('info') \
            else success if severity.startswith('succ') \
            else warn if severity.startswith('warn') \
            else err

        fn(message)


@click.group
def cli() -> None:
    pass


@cli.command
@click.option('--reload-delay', type=int, default=5, show_default=True,
              help='Delay between config reloads.')
@click.option('--log-level',
              type=click.Choice(['DEBUG', 'INFO', 'WARN', 'ERROR'],
                                case_sensitive=False),
              default='INFO', show_default=True, help='Log level.')
@click.option('--log-file', type=click.Path(file_okay=True),
              help='Logs to a file instead to stdout.')
@click.option('--dotfile', 'dotfile_path',
              type=click.Path(file_okay=True),
              default=DEFAULT_CONF,
              show_default=True, help='.grony.conf location.')
def start(dotfile_path: str, reload_delay: int, log_level: str,
          log_file: Optional[str] = None) -> None:
    """Starts the main process.
    """

    logging.basicConfig(format='%(asctime)-5s %(levelname)-8s %(message)s',
                        filename=log_file,
                        level=getattr(logging, log_level.upper()))

    logging.info('===== Starting grony =====')

    scheduler_thread = SchedulerThread(dotfile_path, reload_delay)
    server_thread = ServerThread(dotfile_path)

    def handle_signal(sig: int, frame: Any) -> None:
        name = signal.Signals(sig).name
        logging.info(f'{name} received.')

        if scheduler_thread.is_alive():
            logging.info('Stopping scheduler process...')
            scheduler_thread.stop()

        if server_thread.is_alive():
            logging.info('Stopping server process...')
            server_thread.stop()

    signal.signal(signal.SIGINT, handle_signal)
    signal.signal(signal.SIGTERM, handle_signal)

    logging.info('Press Ctrl+C to stop...')

    scheduler_thread.start()
    server_thread.start()

    scheduler_thread.join()
    server_thread.join()


@cli.command()
@click.argument('path', type=click.Path(exists=True, dir_okay=True),
                nargs=1)
@click.option('--name', help='Repository friendly name.')
@click.option('--dotfile', 'dotfile_path',
              type=click.Path(file_okay=True),
              default=DEFAULT_CONF,
              show_default=True, help='.grony.conf location.')
def add(path: str, name: Optional[str], dotfile_path: str):
    """Adds a repository to the .grony.conf file.
    """

    dotfile = load_dotfile(dotfile_path)

    if not name:
        _, dirname = os.path.split(os.path.abspath(path))
        default: Optional[str] = None
        if dirname:
            default = dirname
        while not name or not name.strip():
            name = click.prompt("Repository friendly name", default=default)

    client = Client(dotfile)
    try:
        result = client.make_request('add', path=path, name=name)
        _display_result(result)
    except URLError as e:
        fatal(str(e.reason))


@cli.command()
@click.option('--dotfile', 'dotfile_path',
              type=click.Path(file_okay=True),
              default=DEFAULT_CONF,
              show_default=True, help='.grony.conf location.')
@click.argument('name')
def remove(dotfile_path: str, name: str):
    """Removes a repository from the .grony.conf file.
    """

    dotfile = load_dotfile(dotfile_path)
    client = Client(dotfile)
    try:
        result = client.make_request('remove', name=name)
        _display_result(result)
    except URLError as e:
        fatal(str(e.reason))


@cli.command
@click.option('--add', 'autoadd', is_flag=True, default=False,
              help="Also, add the repository to the default .grony.conf.")
@click.option('--dotfile', 'dotfile_path',
              type=click.Path(file_okay=True),
              default=DEFAULT_CONF,
              show_default=True, help='.grony.conf location.')
@click.argument('path', type=click.Path(exists=True, dir_okay=True),
                default='.')
def init(autoadd: bool, dotfile_path: str, path: str):
    """Initializes a .grony file in the specified path.
    """

    dotfile = load_dotfile(dotfile_path)
    client = Client(dotfile)
    try:
        result = client.make_request('init', path=path)
        _display_result(result)
    except URLError as e:
        fatal(str(e.reason))

    if _is_success(result) and autoadd:
        add(path, None, dotfile_path)


@cli.command
@click.option('--dotfile', 'dotfile_path',
              type=click.Path(file_okay=True),
              default=DEFAULT_CONF,
              show_default=True, help='.grony.conf location.')
def list(dotfile_path: str):
    """List all configured repositories.
    """

    dotfile = load_dotfile(dotfile_path)
    items = tuple((name, repo.get('path'))
                  for (name, repo) in dotfile.get_repos().items())
    print(tabulate(items, headers=('Name', 'Path'), tablefmt='simple'))


@cli.command
@click.option('--ini', 'ini_format', is_flag=True, default=False,
              help='Uses an output format suitable for config files')
@click.option('--dotfile', 'dotfile_path',
              type=click.Path(file_okay=True),
              default=DEFAULT_CONF,
              show_default=True, help='.grony.conf location.')
@click.option('--all', 'show_all', is_flag=True,
              default=False,
              help='Display all repositories')
@click.argument('name', type=str, required=False)
def show(ini_format, dotfile_path: str, show_all: bool, name: str):
    """Show the effective settings for a repository.
    """

    dotfile = load_dotfile(dotfile_path)

    items = dotfile.get_repo(name).items()
    if ini_format:
        for k, v in items:
            print(f'{k} = {v}')
    else:
        print(tabulate(items, headers=('Key', 'Value'), tablefmt='simple'))
