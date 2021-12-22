# Copyright (C) 2020-2021 Greenbone Networks GmbH
#
# SPDX-License-Identifier: AGPL-3.0-or-later
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as
# published by the Free Software Foundation, either version 3 of the
# License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program. If not, see <http://www.gnu.org/licenses/>.

import argparse
import logging

from pathlib import Path
from typing import Any, Dict

from ..config import Config
from ..__version__ import __version__

ParserType = argparse.ArgumentParser
Arguments = argparse.Namespace

logger = logging.getLogger(__name__)

DEFAULT_CONFIG_FILE = "/etc/gvm/notus-scanner.toml"
DEFAULT_USER_CONFIG_FILE = "~/.config/notus-scanner.toml"


def log_level(string: str) -> str:
    """Check if provided string is a valid log level."""

    if not hasattr(logging, string.upper()):
        raise argparse.ArgumentTypeError(
            "log level must be one of {debug,info,warning,error,critical}"
        )
    return string.upper()


def _to_defaults(values: Dict[str, Any]) -> Dict[str, Any]:
    defaults = {}

    for key, value in values.items():
        defaults[key.replace("-", "_")] = value

    return defaults


class CliParser:
    def __init__(self) -> None:
        """Create a command-line arguments parser for Notus Scanner."""
        parser = argparse.ArgumentParser(
            description="Notus Scanner", add_help=False
        )

        parser.add_argument(
            "--version",
            help="Print version then exit.",
            action="version",
            version=f"%(prog)s {__version__}",
        )
        parser.add_argument(
            "-h",
            "--help",
            help="Show this help message and exit.",
            action="store_true",
        )

        parser.add_argument(
            "-c",
            "--config",
            nargs="?",
            help="Configuration file path. If not set %(prog)s "
            f"tries to load {DEFAULT_USER_CONFIG_FILE} and "
            f"{DEFAULT_CONFIG_FILE}.",
        )
        parser.add_argument(
            "--pid-file",
            help="Location of the file for the process ID "
            "(default: %(default)s)",
        )
        parser.add_argument(
            "-l",
            "--log-file",
            nargs="?",
            default=None,
            help="Log file path (default: syslog)",
        )
        parser.add_argument(
            "-L",
            "--log-level",
            type=log_level,
            help="Wished level of logging (default: %(default)s)",
        )
        parser.add_argument(
            "-f",
            "--foreground",
            action="store_true",
            help="Run in foreground and logs all messages to console.",
        )
        parser.add_argument(
            "-a",
            "--advisories-directory",
            type=Path,
            help=(
                "Choose a custom directory that contains advisory files "
                "generated by the Notus Generator. (default: %(default)s)"
            ),
        )
        parser.add_argument(
            "-b",
            "--mqtt-broker-address",
            type=str,
            help="Hostname or IP address of the MQTT broker. "
            "(default: %(default)s)",
        )
        parser.add_argument(
            "-p",
            "--mqtt-broker-port",
            type=int,
            help="Port of the MQTT broker. (default: %(default)s)",
        )

        self.parser = parser

    def _set_defaults(self, configfilename=None) -> None:
        config_data = self._load_config(configfilename)
        self.parser.set_defaults(**_to_defaults(config_data))

    def _load_config(self, configfile: str) -> Dict[str, Any]:
        config = Config()

        use_default = configfile is None
        configpath = None

        if use_default:
            for file in [DEFAULT_USER_CONFIG_FILE, DEFAULT_CONFIG_FILE]:
                path = Path(file).expanduser().resolve()
                if path.exists():
                    configpath = path
                    break
                else:
                    logger.debug(
                        "Ignoring non existing config file %s", configfile
                    )

            if not configpath:
                return config.values()
        else:
            configpath = Path(configfile).expanduser().resolve()
            if not configpath.exists():
                logger.warning(
                    "Ignoring non existing config file %s", configfile
                )
                return config.values()

        config.load(configpath)
        logger.debug("Loaded config %s", configfile)

        return config.values()

    def parse_arguments(self, args=None) -> Arguments:
        # Parse args to get the config file path passed as option
        known_args, _ = self.parser.parse_known_args(args)

        # Load the defaults from the config file if it exists.
        # This also override what was passed as cmd option.
        self._set_defaults(known_args.config)

        if known_args.help:
            self.parser.print_help()
            self.parser.exit(0)

        return self.parser.parse_args(args)
