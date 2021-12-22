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

""" Test module for command line arguments.
"""

import unittest
import tempfile

from pathlib import Path
from typing import List

from notus.scanner.cli.parser import (
    CliParser,
    Arguments,
)
from notus.scanner.config import (
    DEFAULT_ADVISORIES_DIRECTORY,
    DEFAULT_LOG_LEVEL,
    DEFAULT_MQTT_BROKER_ADDRESS,
    DEFAULT_MQTT_BROKER_PORT,
    DEFAULT_PID_FILE,
)


class CliParserTestCase(unittest.TestCase):
    def setUp(self):
        self.parser = CliParser()

    def parse_args(self, args: List[str]) -> Arguments:
        return self.parser.parse_arguments(args)

    def test_mqtt_broker(self):
        args = self.parse_args(["--mqtt-broker-address=localhost"])
        self.assertEqual("localhost", args.mqtt_broker_address)

        args = self.parse_args(["-b", "localhost"])
        self.assertEqual("localhost", args.mqtt_broker_address)

    def test_mqtt_broker_port(self):
        args = self.parse_args(["--mqtt-broker-port=12345"])
        self.assertEqual(args.mqtt_broker_port, 12345)

        args = self.parse_args(["-p", "12345"])
        self.assertEqual(args.mqtt_broker_port, 12345)

    def test_correct_upper_case_log_level(self):
        args = self.parse_args(["--log-level=ERROR"])
        self.assertEqual("ERROR", args.log_level)

    def test_correct_lower_case_log_level(self):
        args = self.parse_args(["-L", "info"])
        self.assertEqual("INFO", args.log_level)

    def test_advisories_directory(self):
        args = self.parse_args(["--advisories-directory=/tmp"])
        self.assertEqual(Path("/tmp"), args.advisories_directory)

        args = self.parse_args(["-a", "/tmp"])
        self.assertEqual(Path("/tmp"), args.advisories_directory)

    def test_pid_file(self):
        args = self.parse_args(["--pid-file=/foo/bar"])
        self.assertEqual(args.pid_file, "/foo/bar")

    def test_log_file(self):
        args = self.parse_args(["--log-file=/foo/bar"])
        self.assertEqual(args.log_file, "/foo/bar")

        args = self.parse_args(["-l", "/foo/bar"])
        self.assertEqual(args.log_file, "/foo/bar")

    def test_foreground(self):
        args = self.parse_args(["--foreground"])
        self.assertTrue(args.foreground)

        args = self.parse_args(["-f"])
        self.assertTrue(args.foreground)

    def test_defaults(self):
        args = self.parse_args([])

        self.assertEqual(
            args.advisories_directory, Path(DEFAULT_ADVISORIES_DIRECTORY)
        )
        self.assertIsNone(args.config)
        self.assertIsNone(args.log_file)
        self.assertEqual(args.log_level, DEFAULT_LOG_LEVEL)
        self.assertEqual(args.mqtt_broker_port, DEFAULT_MQTT_BROKER_PORT)
        self.assertEqual(args.mqtt_broker_address, DEFAULT_MQTT_BROKER_ADDRESS)
        self.assertEqual(args.pid_file, DEFAULT_PID_FILE)
        self.assertFalse(args.foreground)

    def test_config_file_provide_mqtt_broker_address(self):
        with tempfile.NamedTemporaryFile() as fp:
            fp.write(b"[notus-scanner]\nmqtt-broker-address='1.2.3.4'")
            fp.flush()

            args = self.parse_args(["-c", fp.name])
            self.assertEqual(args.mqtt_broker_address, "1.2.3.4")

    def test_config_file(self):
        with tempfile.NamedTemporaryFile() as fp:
            fp.write(
                b"""[notus-scanner]
                mqtt-broker-address="1.2.3.4"
                mqtt-broker-port="123"
                advisories-directory="/tmp"
                pid-file="foo.bar"
                log-file="foo.log"
                log-level="DEBUG"
                """
            )
            fp.flush()

            args = self.parse_args(["-c", fp.name])

            self.assertEqual(args.mqtt_broker_address, "1.2.3.4")
            self.assertEqual(args.mqtt_broker_port, 123)
            self.assertEqual(args.advisories_directory, Path("/tmp"))
            self.assertEqual(args.pid_file, "foo.bar")
            self.assertEqual(args.log_file, "foo.log")
            self.assertEqual(args.log_level, "DEBUG")
