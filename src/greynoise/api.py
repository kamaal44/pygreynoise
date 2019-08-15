"""GreyNoise API client."""

import datetime
import logging

import requests

from greynoise.exceptions import RequestFailure
from greynoise.util import load_config, validate_ip


LOGGER = logging.getLogger(__name__)


class GreyNoise(object):

    """GreyNoise API client.

    :param api_key: Key use to access the API.
    :type api_key: str
    :param timeout: API requests timeout in seconds.
    :type timeout: int

    """

    NAME = "GreyNoise"
    BASE_URL = "https://enterprise.api.greynoise.io"
    CLIENT_VERSION = 1
    API_VERSION = "v2"
    DATE_FORMAT = "%Y-%m-%d"
    EP_NOISE_BULK = "noise/bulk"
    EP_NOISE_BULK_DATE = "noise/bulk/{date}"
    EP_NOISE_QUICK = "noise/quick/{ip_address}"
    EP_NOISE_MULTI = "noise/multi/quick"
    EP_NOISE_CONTEXT = "noise/context/{ip_address}"
    EP_RESEARCH_ACTORS = "research/actors"
    UNKNOWN_CODE_MESSAGE = "Code message unknown: {}"
    CODE_MESSAGES = {
        "0x00": "IP has never been observed scanning the Internet",
        "0x01": "IP has been observed by the GreyNoise sensor network",
        "0x02": (
            "IP has been observed scanning the GreyNoise sensor network, "
            "but has not completed a full connection, meaning this can be spoofed"
        ),
        "0x03": (
            "IP is adjacent to another host that has been directly observed "
            "by the GreyNoise sensor network"
        ),
        "0x04": "RESERVED",
        "0x05": "IP is commonly spoofed in Internet-scan activity",
        "0x06": (
            "IP has been observed as noise, but this host belongs to a cloud provider "
            "where IPs can be cycled frequently"
        ),
        "0x07": "IP is invalid",
        "0x08": (
            "IP was classified as noise, but has not been observed "
            "engaging in Internet-wide scans or attacks in over 60 days"
        ),
    }

    def __init__(self, api_key=None, timeout=7):
        if api_key is None:
            api_key = load_config()["api_key"]
        self.api_key = api_key
        self.timeout = timeout
        self.session = requests.Session()

    def _request(self, endpoint, params=None, json=None):
        """Handle the requesting of information from the API.

        :param endpoint: Endpoint to send the request to.
        :type endpoint: str
        :param params: Request parameters.
        :type param: dict
        :param json: Request's JSON payload.
        :type json: dict
        :returns: Response's JSON payload
        :rtype: dict
        :raises RequestFailure: when HTTP status code is not 2xx

        """
        if params is None:
            params = {}
        headers = {
            "X-Request-Client": "pyGreyNoise v{}".format(self.CLIENT_VERSION),
            "key": self.api_key,
        }
        url = "/".join([self.BASE_URL, self.API_VERSION, endpoint])
        response = self.session.get(
            url, headers=headers, timeout=self.timeout, params=params, json=json
        )
        if response.status_code not in range(200, 299):
            raise RequestFailure(response.status_code, response.content)

        return response.json()

    def get_noise(self, date=None):
        """Get a complete dump of noisy IPs associated with Internet scans.

        Get all noise IPs generated by Internet scanners, search engines, and
        worms.

        Users will get all values or can specify a date filter for just
        a single day.

        :param date: Optional date to use as a filter.
        :type date: datetime.date | None
        :return: List of IP addresses associated with scans.
        :rtype: list
        :raises ValueError: when date argument is invalid

        """
        LOGGER.debug("Getting noise (date: %s)...", date)
        if date is None:
            endpoint = self.EP_NOISE_BULK
        else:
            if not isinstance(date, datetime.date):
                raise ValueError("date argument must be an instance of datetime.date")
            endpoint = self.EP_NOISE_BULK_DATE.format(
                date=date.strftime(self.DATE_FORMAT)
            )

        response = self._request(endpoint)
        noise_ips = response.get("noise_ips", [])
        offset = response.get("offset", -1)
        complete = response["complete"]
        while not complete:
            response = self._request(endpoint, params={"offset": offset})
            noise_ips.extend(response.get("noise_ips", []))
            offset = response.get("offset", -1)
            complete = response["complete"]

        LOGGER.debug("Noisy IP addresses found: %d", len(noise_ips))
        return noise_ips

    def get_noise_status(self, ip_address):
        """Get activity associated with an IP address.

        :param ip_address: IP address to use in the look-up.
        :type recurse: str
        :return: Activity metadata for the IP address.
        :rtype: dict

        """
        LOGGER.debug("Getting noise status for %s...", ip_address)
        validate_ip(ip_address)
        endpoint = self.EP_NOISE_QUICK.format(ip_address=ip_address)
        result = self._request(endpoint)
        code = result["code"]
        result["code_message"] = self.CODE_MESSAGES.get(
            code, self.UNKNOWN_CODE_MESSAGE.format(code)
        )
        return result

    def get_noise_status_bulk(self, ip_addresses):
        """Get activity associated with multiple IP addresses.

        :param ip_addresses: IP addresses to use in the look-up.
        :type ip_addresses: list
        :return: Bulk status information for IP addresses.
        :rtype: dict

        """
        LOGGER.debug("Getting noise status for %s...", ip_addresses)
        if not isinstance(ip_addresses, list):
            raise ValueError("`ip_addresses` must be a list")

        ip_addresses = [
            ip_address
            for ip_address in ip_addresses
            if validate_ip(ip_address, strict=False)
        ]
        results = self._request(self.EP_NOISE_MULTI, json={"ips": ip_addresses})
        for result in results:
            code = result["code"]
            result["code_message"] = self.CODE_MESSAGES.get(
                code, self.UNKNOWN_CODE_MESSAGE.format(code)
            )
        return results

    def get_context(self, ip_address):
        """Get context associated with an IP address.

        :param ip_address: IP address to use in the look-up.
        :type recurse: str
        :return: Context for the IP address.
        :rtype: dict

        """
        LOGGER.debug("Getting context for %s...", ip_address)
        validate_ip(ip_address)
        endpoint = self.EP_NOISE_CONTEXT.format(ip_address=ip_address)
        response = self._request(endpoint)
        return response

    def get_actors(self):
        """Get the names and IP addresses of actors scanning the Internet.

        :returns: Most labeled actors scanning the intenet.
        :rtype: list

        """
        LOGGER.debug("Getting actors...")
        response = self._request(self.EP_RESEARCH_ACTORS)
        return response
