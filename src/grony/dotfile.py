import os
import re
import uuid
import logging
import configparser

from pathlib import Path

from typing import Any, Dict


class Dotfile(configparser.RawConfigParser):
    def __init__(self, path: str, *args, **kwargs) -> None:
        self.path = path
        super().__init__(*args, **kwargs)
        self.reload()

    def reload(self) -> None:
        self.clear()
        try:
            self.read(self.path)
        except Exception as ex:
            logging.warning(str(ex))

    def _get_repo_key(self, name: str) -> str:
        return f"repo '{name}'"

    def add_repo_section(self, name: str) -> configparser.SectionProxy:
        key = self._get_repo_key(name)
        self.add_section(key)
        return self[key]

    def get_repos(self) -> Dict[str, Dict[str, Any]]:
        return dict((match.group(1), self.get_repo(match.group(1)))
                    for match in (re.match(r"^\s*repo\s+'([^']+)'\s*$", s)
                                  for s in self.sections())
                    if match)

    def has_repo(self, name: str) -> bool:
        key = self._get_repo_key(name)
        return self.has_section(key)

    def get_repo(self, name: str) -> Dict[str, Any]:
        key = self._get_repo_key(name)
        if not self.has_section(key):
            return {}

        result = {'name': name}

        section = self[key]

        # Load .grony file, if any
        path = section.get('path', None)
        if path:
            conf_path = Path(os.path.join(path, '.grony'))
            if conf_path.exists() and conf_path.is_file():
                conf = configparser.RawConfigParser()
                conf.read(conf_path)
                if conf.has_section('repo'):
                    result.update(conf['repo'])

        # Settings in main conf override anything else
        result.update(section)

        return result

    def remove_repo(self, name: str) -> bool:
        key = self._get_repo_key(name)
        if not self.has_section(key):
            return False

        try:
            del self[key]
            save_dotfile(self)
            return True
        except Exception as ex:
            logging.warning(str(ex))
            return False


def _expand(path: str) -> str:
    return os.path.abspath(os.path.expandvars(path))


def _load_dotfile(path: str) -> Dotfile:
    return Dotfile(_expand(path))


def _set_default_value(dotfile: Dotfile, section: str,
                       key: str, value: str) -> bool:
    result = False
    if not dotfile.has_section(section):
        result = True
        dotfile.add_section(section)

    if not dotfile.has_option(section, key):
        result = True
        dotfile.set(section, key, value)

    return result


def add_defaults(dotfile: Dotfile) -> bool:
    """Adds the default config.
       Returns `True` if any defaul added. `False` otherwise.
    """

    defaults = {
        'ipc_port': '62830',
        'secret': str(uuid.uuid4()),
    }

    updated = False
    for k, v in defaults.items():
        updated = _set_default_value(dotfile, 'config', k, v) or updated

    if updated:
        logging.debug('Defaults added to dotfile.')

    return updated


def load_dotfile(path: str, with_defaults: bool = True) -> Dotfile:
    result = _load_dotfile(path)
    if with_defaults and add_defaults(result):
        save_dotfile(result)
        logging.info('Dotfile udpated with missing defaults.')
    return result


def save_dotfile(dotfile: Dotfile) -> None:
    logging.debug(f'Saving dotfile to {dotfile.path}...')
    with open(dotfile.path, "w+") as f:
        dotfile.write(f)
