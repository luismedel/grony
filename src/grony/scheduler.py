import os
import time
import logging
import subprocess

from datetime import datetime, timedelta
from threading import Thread
from collections import namedtuple

from grony.dotfile import Dotfile, load_dotfile

from crontab import CronTab  # type: ignore

from typing import Any, Dict, List, Optional, cast


RunInfo = namedtuple('RunInfo', ['datetime', 'action', 'repo_data'])


class SchedulerThread(Thread):
    def __init__(self, dotfile_path: str,
                 reload_delay_seconds: int) -> None:
        super().__init__()
        self.dotfile_path = dotfile_path
        self.reload_delay = reload_delay_seconds
        self._running = False

    def _schedule_next(self, dotfile: Dotfile,
                       since: datetime) -> List[RunInfo]:
        """Returns one RunInfo entry for each action in all repos.
        """
        since = since.replace(second=0, microsecond=0)

        result: List[RunInfo] = []

        for repo in dotfile.get_repos().values():
            repo_name = repo['name']

            logging.debug(f"Checking actions for '{repo_name}'...")
            for key in ('pull-on', 'commit-on', 'push-on'):
                cron_expr: Optional[str] = repo.get(key, None)
                if not cron_expr:
                    continue

                pending_seconds = CronTab(cron_expr).next(since,
                                                          default_utc=False)
                next_run = since + timedelta(seconds=pending_seconds)

                info = RunInfo(next_run, key.replace('-on', ''), repo)
                result.append(info)
                logging.debug(
                    f'  - Scheduled {info.action} on {info.datetime}')

        return result

    def _perform_run(self, rinfo: RunInfo) -> bool:
        repo: Dict[str, Any] = cast(Dict[str, Any], rinfo.repo_data)
        repo_name: str = repo['name']

        logging.info(f"Running '{rinfo.action}' for '{repo_name}'...")

        path: Optional[str] = repo.get('path', None)
        if not path:
            logging.warning("  - Missing 'path' key!")
            return False

        path = os.path.abspath(os.path.expandvars(path))

        command: Optional[str] = None
        if rinfo.action == 'pull':
            remote = repo.get('pull-remote', '')
            command = f'git pull {remote}'
        elif rinfo.action == 'commit':
            message = datetime.now().strftime(
                repo.get('commit-message', 'Auto commit at %Y%m%d %H:%M:%S'))
            command = f'git add -A && git commit -m "{message}"'
        elif rinfo.action == 'push':
            remote = repo.get('push-remote', '')
            command = f'git push {remote}'
        else:
            logging.warning(f"  - Invalid action '{rinfo.action}'!")
            return False

        try:
            subprocess.run(command, shell=True, check=True, cwd=path)
            logging.info("Finished")
            return True
        except Exception as ex:
            logging.exception(ex)
            return False

    def start(self) -> None:
        self._running = True
        super().start()

    def run(self) -> None:
        dotfile = load_dotfile(self.dotfile_path)
        next_reload = datetime.min
        next_runs: Optional[List[RunInfo]] = None

        while self._running:

            # This is the main cron-like loop. It consistes of 3 steps:
            # 1) Load repo metadata.
            # 2) Run pending scheduled operations.
            # 3) Re-schedule next operations.
            #
            # We choose to reload all files every `reload_delay` seconds
            # because:
            # - It's a lightweight operation.
            # - It's simpler thant maintaining an up-to-date memory cache
            #   of all files and watch for changes during runtime.

            #  Reload metadata if needed
            if next_reload < datetime.now():
                logging.debug('Reloading metadata...')
                dotfile = load_dotfile(self.dotfile_path)
                next_reload = datetime.now() + \
                    timedelta(seconds=self.reload_delay)
                next_runs = None
                logging.debug(f'  - Next reload on {next_reload}')

            if not next_runs:
                next_runs = self._schedule_next(dotfile, datetime.now())

            now = datetime.now()

            # Run all pending operations
            pending_count = 0
            success_runs = 0
            for run in next_runs:
                if run.datetime > now:
                    continue

                pending_count += 1
                if self._perform_run(run):
                    success_runs += 1

            if pending_count:
                logging.info(f'Executed {pending_count} pending runs.')
                if success_runs != pending_count:
                    logging.warning(
                        f'  - {pending_count - success_runs} errors.')

                #  Schedule next runs.
                #
                # Schedule since the cached `now` instead of `datetime.now()`
                # to not leave any time gap without a check
                next_runs = self._schedule_next(dotfile, now)

            # Sleep for 1 second (we want to be responsive when closing)
            time.sleep(1)

    def stop(self) -> None:
        self._running = False
