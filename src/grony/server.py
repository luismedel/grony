import re
import cgi
import json
import logging
import urllib.parse

from functools import partial
from threading import Thread
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.error import HTTPError

from grony.dotfile import Dotfile, load_dotfile
from grony.commands import CallableCommand, Commands

from typing import Any, Dict, List, Optional


class ServerThread(Thread):
    def __init__(self, dotfile_path: str) -> None:
        super().__init__()
        dotfile = load_dotfile(dotfile_path)
        port = dotfile.getint('config', 'ipc_port')
        endpoint = ('127.0.0.1', port)
        self.server = HTTPServer(endpoint, partial(Handler, dotfile))

    def run(self):
        self.server.serve_forever()

    def stop(self):
        self.server.shutdown()


class Handler(BaseHTTPRequestHandler):
    def __init__(self, dotfile: Dotfile, *args, **kwargs) -> None:
        self.dotfile = dotfile
        super().__init__(*args, *kwargs)

    def send(self, data: Any, response_code: int = 200):
        self.send_response(response_code)
        self.send_header('Content-type', 'application/json')
        self.end_headers()
        self.wfile.write(json.dumps(data).encode())

    def _get_data(self) -> Dict[str, Any]:
        ctype, pdict = cgi.parse_header(self.headers.get('content-type', ''))
        if ctype == 'multipart/form-data':
            return cgi.parse_multipart(self.rfile, pdict)  # type: ignore
        elif ctype == 'application/x-www-form-urlencoded':
            length = int(self.headers.get('content-length', -1))
            qs = self.rfile.read(length).decode()
            return urllib.parse.parse_qs(qs, keep_blank_values=True)
        else:
            return {}

    def reject_request(self, message: str) -> None:
        logging.warning(message)
        self.send('Go home', 500)
        return

    def get_command(self) -> Optional[CallableCommand]:
        secret = self.dotfile.get('config', 'secret')

        if self.client_address[0] != '127.0.0.1':
            self.reject_request(
                f'Invalid request (address = {self.client_address})')
            return None

        auth_headers = (k for k, v in self.headers.items()
                        if k == "Authorization"
                        and v == f"Bearer {secret}")
        auth = next(auth_headers, None)
        if not auth:
            self.reject_request('Invalid request (authentication failed)')
            return None

        m = re.match(r'^\/grony\/([^\/]+)/?', self.path)
        if not m:
            self.reject_request('Invalid request')
            return None

        command = m.group(1)
        return Commands.get_command(command)

    def do_POST(self) -> None:
        fn = self.get_command()
        if not fn:
            self.reject_request("Unrecognized command")
            return

        try:
            messages: List[Dict[str, str]] = []

            # Convert from Dict[str, List[str]] to Dict[str, str], as
            # we only have a value for each key
            args = dict((k, v[0]) for k, v in self._get_data().items())

            success, msg = fn(self.dotfile, args)
            severity = 'success' if success else 'error'
            messages.append({'severity': severity, 'message': msg})
        except HTTPError as ex:
            logging.exception(ex)
            messages.append({'severity': 'fatal', 'message': str(ex)})
        finally:
            self.send({'messages': messages})
