"""CLI subcommands test cases."""

import textwrap
from datetime import datetime

import pytest
from click.testing import CliRunner
from mock import Mock, patch

from greynoise.cli.subcommand import (
    actors,
    context,
    multi_quick_check,
    noise,
    quick_check,
    setup,
)
from greynoise.util import CONFIG_FILE


class TestSetup(object):
    """Setup subcommand test cases."""

    @pytest.mark.parametrize("key_option", ["-k", "--api-key"])
    def test_save_config(self, key_option):
        """Save configuration file."""
        runner = CliRunner()
        api_key = "<api_key>"
        expected_config = {"api_key": api_key}
        expected_output = "Configuration saved to {!r}\n".format(CONFIG_FILE)

        with patch("greynoise.cli.subcommand.save_config") as save_config:
            result = runner.invoke(setup, [key_option, api_key])
        assert result.exit_code == 0
        assert result.output == expected_output
        save_config.assert_called_with(expected_config)

    def test_missing_api_key(self):
        """Setup fails when api_key is not passed."""
        runner = CliRunner()
        expected_error = 'Error: Missing option "-k" / "--api-key"'

        result = runner.invoke(setup, [])
        assert result.exit_code == 2
        assert expected_error in result.output


class TestNoise(object):
    """Noise subcommand test cases."""

    def test_without_date(self):
        """Noise subcommand without date."""
        runner = CliRunner()

        api_client = Mock()
        api_client.get_noise.return_value = []
        obj = {"api_client": api_client, "output_format": "json"}
        result = runner.invoke(noise, [], obj=obj)
        assert result.exit_code == 0
        assert result.output == "[]\n"
        api_client.get_noise.assert_called_with(date=None)

    @pytest.mark.parametrize("date_option", ["-d", "--date"])
    def test_with_date(self, date_option):
        """Noise subcommand with date."""
        runner = CliRunner()

        api_client = Mock()
        api_client.get_noise.return_value = []
        obj = {"api_client": api_client, "output_format": "json"}
        result = runner.invoke(noise, [date_option, "2019-01-01"], obj=obj)
        assert result.exit_code == 0
        assert result.output == "[]\n"
        api_client.get_noise.assert_called_with(date=datetime(2019, 1, 1))

    @pytest.mark.parametrize("date_option", ["-d", "--date"])
    def test_invalid_date(self, date_option):
        """Noise subcommand with date."""
        runner = CliRunner()

        api_client = Mock()
        api_client.get_noise.return_value = []
        obj = {"api_client": api_client, "output_format": "json"}
        expected = 'Error: Invalid value for "-d" / "--date"'

        result = runner.invoke(noise, [date_option, "not-a-date"], obj=obj)
        assert result.exit_code == 2
        assert expected in result.output
        api_client.get_noise.assert_not_called()


class TestContext(object):
    """Context subcommand tests."""

    def test_context(self):
        """Get IP address context."""
        runner = CliRunner()

        api_client = Mock()
        api_client.get_context.return_value = {}
        obj = {"api_client": api_client, "output_format": "json"}

        result = runner.invoke(context, ["0.0.0.0"], obj=obj)
        assert result.exit_code == 0
        assert result.output == "{}\n"
        api_client.get_context.assert_called_with(ip_address="0.0.0.0")

    def test_missing_ip_address(self):
        """Context fails when ip_address is missing."""
        runner = CliRunner()

        api_client = Mock()
        api_client.get_context.return_value = {}
        obj = {"api_client": api_client, "output_format": "json"}
        expected = 'Error: Missing argument "IP_ADDRESS".'

        result = runner.invoke(context, [], obj=obj)
        assert result.exit_code == 2
        assert expected in result.output
        api_client.get_context.assert_not_called()

    def test_invalid_ip_address(self):
        """Context fails when ip_address is invalid."""
        runner = CliRunner()

        api_client = Mock()
        api_client.get_context.return_value = {}
        obj = {"api_client": api_client, "output_format": "json"}
        expected = 'Error: Invalid value for "IP_ADDRESS": not-an-ip\n'

        result = runner.invoke(context, ["not-an-ip"], obj=obj)
        assert result.exit_code == 2
        assert expected in result.output
        api_client.get_context.assert_not_called()


class TestQuickCheck(object):
    """Quick check subcommand tests."""

    def test_quick_check(self):
        """Quickly check IP address."""
        runner = CliRunner()

        api_client = Mock()
        api_client.get_noise_status.return_value = {}
        obj = {"api_client": api_client, "output_format": "json"}

        result = runner.invoke(quick_check, ["0.0.0.0"], obj=obj)
        assert result.exit_code == 0
        assert result.output == "{}\n"
        api_client.get_noise_status.assert_called_with(ip_address="0.0.0.0")

    def test_missing_ip_address(self):
        """Quick check fails when ip_address is missing."""
        runner = CliRunner()

        api_client = Mock()
        api_client.get_noise_status.return_value = {}
        obj = {"api_client": api_client, "output_format": "json"}
        expected = 'Error: Missing argument "IP_ADDRESS".'

        result = runner.invoke(quick_check, [], obj=obj)
        assert result.exit_code == 2
        assert expected in result.output
        api_client.get_noise_status.assert_not_called()

    def test_invalid_ip_address(self):
        """Quick check fails when ip_address is invalid."""
        runner = CliRunner()

        api_client = Mock()
        api_client.get_noise_status.return_value = {}
        obj = {"api_client": api_client, "output_format": "json"}
        expected = 'Error: Invalid value for "IP_ADDRESS": not-an-ip\n'

        result = runner.invoke(quick_check, ["not-an-ip"], obj=obj)
        assert result.exit_code == 2
        assert expected in result.output
        api_client.get_noise_status.assert_not_called()


class TestMultiQuickCheck(object):
    """Multi quick check subcommand tests."""

    def test_quick_check(self):
        """Quickly check IP addresses."""
        runner = CliRunner()

        api_client = Mock()
        api_client.get_noise_status_bulk.return_value = []
        obj = {"api_client": api_client, "output_format": "json"}

        result = runner.invoke(multi_quick_check, ["0.0.0.0", "0.0.0.1"], obj=obj)
        assert result.exit_code == 0
        assert result.output == "[]\n"
        api_client.get_noise_status_bulk.assert_called_with(
            ip_addresses=["0.0.0.0", "0.0.0.1"]
        )

    def test_missing_ip_address(self):
        """Quick check calls API even when no addresses are passed."""
        runner = CliRunner()

        api_client = Mock()
        api_client.get_noise_status_bulk.return_value = {"error": "no results"}
        obj = {"api_client": api_client, "output_format": "json"}
        expected = textwrap.dedent(
            """\
            {
                "error": "no results"
            }
        """
        )

        result = runner.invoke(multi_quick_check, [], obj=obj)
        assert result.exit_code == 0
        assert result.output == expected
        api_client.get_noise_status_bulk.assert_called_with(ip_addresses=[])

    def test_invalid_ip_address(self):
        """Quick check fails when ip_address is invalid."""
        runner = CliRunner()

        api_client = Mock()
        api_client.get_noise_status_bulk.return_value = {}
        obj = {"api_client": api_client, "output_format": "json"}
        expected = 'Error: Invalid value for "[IP_ADDRESS]...": not-an-ip\n'

        result = runner.invoke(multi_quick_check, ["0.0.0.0", "not-an-ip"], obj=obj)
        assert result.exit_code == 2
        assert expected in result.output
        api_client.get_noise_status_bulk.assert_not_called()


class TestActors(object):
    """Actors subcommand tests."""

    def test_actors(self):
        """Get actors."""
        runner = CliRunner()

        api_client = Mock()
        api_client.get_actors.return_value = []
        obj = {"api_client": api_client, "output_format": "json"}
        expected = "[]\n"

        result = runner.invoke(actors, obj=obj)
        assert result.exit_code == 0
        assert result.output == expected
        api_client.get_actors.assert_called_with()