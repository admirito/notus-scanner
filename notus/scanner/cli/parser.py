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

from ..config import Config

DEFAULT_CONFIG_PATH = "/etc/gvm/notus.conf"
DEFAULT_PID_PATH = "/run/gvm/notus.pid"

ParserType = argparse.ArgumentParser
Arguments = argparse.Namespace

logger = logging.getLogger(__name__)


def _dir_path(directory: str) -> Path:
    """Check if a given string is a valid path to a directory,
    relative or absolute.

    Arguments:
        directory: A string to check if it is an existing directory.

    Returns:
        If directory points to an existing directory a Path to the directory is
        returned otherwise an ArgumentTypeError is raised
    """
    path = Path(directory)
    if not path.is_dir():
        raise argparse.ArgumentTypeError(
            f"{directory.absolute()} does not exist."
        )

    return path


class CliParser:
    def __init__(self, description: str) -> None:
        """Create a command-line arguments parser for Notus Scanner."""
        self._name = description
        parser = argparse.ArgumentParser(description=description)

        parser.add_argument(
            '--version', action='store_true', help='Print version then exit.'
        )

        parser.add_argument(
            '-c',
            '--config',
            nargs='?',
            default=DEFAULT_CONFIG_PATH,
            help='Configuration file path (default: %(default)s)',
        )
        parser.add_argument(
            '--pid-file',
            default=DEFAULT_PID_PATH,
            help='Location of the file for the process ID '
            '(default: %(default)s)',
        )
        parser.add_argument(
            '-l',
            '--log-file',
            nargs='?',
            default=None,
            help='Log file path (default: syslog)',
        )
        parser.add_argument(
            '-L',
            '--log-level',
            default='INFO',
            type=self.log_level,
            help='Wished level of logging (default: %(default)s)',
        )
        parser.add_argument(
            '-f',
            '--foreground',
            action='store_true',
            help='Run in foreground and logs all messages to console.',
        )
        parser.add_argument(
            "-a",
            "--advisories-directory",
            type=_dir_path,
            help=(
                "Choose a custom directory that contains advisory files,"
                "generated by the Notus Generator."
            ),
        )
        parser.add_argument(
            "-b",
            "--mqtt-broker-address",
            type=str,
            required=True,
            help="Hostname or IP address of the MQTT broker.",
        )
        parser.add_argument(
            "-p",
            "--mqtt-broker-port",
            type=int,
            default=1883,
            help="Port of the MQTT broker. (default: %(default)s)",
        )

        self.parser = parser

    def log_level(self, string: str) -> str:
        """Check if provided string is a valid log level."""

        if not hasattr(logging, string.upper()):
            raise argparse.ArgumentTypeError(
                'log level must be one of {debug,info,warning,error,critical}'
            )
        return string.upper()

    def _set_defaults(self, configfilename=None) -> None:
        self._config = self._load_config(configfilename)
        self.parser.set_defaults(**self._config.defaults())

    def _load_config(self, configfile: str) -> Config:
        config = Config()

        if not configfile:
            return config

        configpath = Path(configfile)

        if not configpath.expanduser().resolve().exists():
            logger.debug('Ignoring non existing config file %s', configfile)
            return config

        try:
            config.load(configpath, def_section=self._name)
            logger.debug('Loaded config %s', configfile)
        except Exception as e:  # pylint: disable=broad-except
            raise RuntimeError(
                'Error while parsing config file {config}. Error was '
                '{message}'.format(config=configfile, message=e)
            ) from None

        return config

    def parse_arguments(self, args=None):
        # Parse args to get the config file path passed as option
        _args, _ = self.parser.parse_known_args(args)

        # Load the defaults from the config file if it exists.
        # This also override what was passed as cmd option.
        self._set_defaults(_args.config)
        args = self.parser.parse_args(args)

        return args


def create_parser(description: str) -> CliParser:
    return CliParser(description)
