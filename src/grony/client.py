import json
import urllib.request

from urllib.error import HTTPError

from grony.dotfile import Dotfile

from typing import Any, Dict


class Client:
    def __init__(self, dotfile: Dotfile) -> None:
        self.dotfile = dotfile

    def make_request(self, endpoint: str, **kwargs) -> Dict[str, Any]:
        port: int = self.dotfile.getint('config', 'ipc_port')
        secret: str = self.dotfile.get('config', 'secret')
        host: str = '127.0.0.1'
        data: bytes = urllib.parse.urlencode(kwargs).encode()

        req = urllib.request.Request(
            f'http://{host}:{port}/grony/{endpoint}',
            data=data, method='POST')
        req.add_header('Authorization', f"Bearer {secret}")

        try:
            response = urllib.request.urlopen(req)
            return json.loads(response.read().decode())
        except HTTPError as e:
            return json.loads(e.read())
