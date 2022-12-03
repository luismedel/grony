import os
import configparser

from pathlib import Path

from grony.dotfile import Dotfile, save_dotfile

from typing import Any, Callable, Dict, Optional, Tuple


CommandResult = Tuple[bool, str]
CallableCommand = Callable[[Dotfile, Dict[str, Any]], CommandResult]


class Commands:

    ALLOWED_METHODS: Tuple[str, ...] = ('init', 'add', 'remove',)

    @classmethod
    def get_command(cls, name: str) -> Optional[CallableCommand]:
        """Returns a command method by name.

        We use this to avoid accessing other member via hijacked requests.
        """
        if name not in cls.ALLOWED_METHODS:
            return None
        return getattr(cls, name, None)

    @staticmethod
    def init(dotfile: Dotfile, args: Dict[str, Any]) -> CommandResult:
        path: Optional[str] = args.get('path', None)
        if not path:
            return (False, "Missing parameter 'path'")

        path = os.path.abspath(os.path.expandvars(path))

        file: Path = Path(os.path.join(path, '.grony'))
        if file.exists():
            return (False, f".grony file already exists in {path}")
        conf = configparser.RawConfigParser()
        conf.add_section('repo')

        defaults = {
            'override-settings': 'false',
            'pull-on': '@hourly',
            'commit-message': r'Auto commit at %Y%m%d %H:%M:%S',
            'commit-on': '@hourly',
            'push-to-remote': 'origin',
            'push-on': '@hourly'
        }

        for k, v in defaults.items():
            conf.set('repo', k, v)

        with file.open('w') as f:
            conf.write(f)

        if not Path(os.path.join(path, '.git')).is_dir():
            return (True, f"Default .grony created in {path}")
        else:
            return (True, f"Default .grony created in {path} but"
                    " it doesn't look like a git repo")

    @staticmethod
    def add(dotfile: Dotfile, args: Dict[str, Any]) -> CommandResult:
        path: Optional[str] = args.get('path', None)
        if not path:
            return (False, "Missing parameter 'path'")

        name: Optional[str] = args.get('name', None)
        if not name:
            return (False, "Missing parameter 'name'")

        if dotfile.has_repo(name):
            return (False, f'Repository {name} already'
                    ' exists in {dotfile.path}.')

        section = dotfile.add_repo_section(name)
        section['path'] = os.path.abspath(os.path.expandvars(path))
        save_dotfile(dotfile)
        return (True, f'Successfully added {name}')

    @staticmethod
    def remove(dotfile: Dotfile, args: Dict[str, Any]) -> CommandResult:
        name: Optional[str] = args.get('name', None)
        if not name:
            return (False, "Missing parameter 'name'")

        if not dotfile.has_repo(name):
            return (False, f"Unknown repo '{name}'")
        elif not dotfile.remove_repo(name):
            return (False, f"Can't remove repo '{name}'")
        else:
            return (True, f"Repository removed from {dotfile.path}")
