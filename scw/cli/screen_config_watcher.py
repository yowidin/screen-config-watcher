#!/usr/bin/env python3
import sys
from typing import List, Optional

from scw.options import Options
from scw.watcher_app import ScreenConfigWatcherApp


def main(cmd_args: Optional[List[str]] = None):
    opts, _ = Options.parse('screen-config-watcher', cmd_args=cmd_args)
    app = ScreenConfigWatcherApp(opts)
    app.run()


def run(cmd_args: Optional[List[str]] = None):
    try:
        main(cmd_args)
        sys.exit(0)
    except RuntimeError as e:
        print(e, file=sys.stderr)

    sys.exit(-1)


if __name__ == '__main__':
    run()


