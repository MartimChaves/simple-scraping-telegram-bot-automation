"""Tests for the scraper module."""

from unittest.mock import patch, MagicMock

import pytest

from scraper import scrape_page, validate_url, URLValidationError


SAMPLE_HTML = """
<html><body>
  <div class="quote"><span class="text">Quote one</span></div>
  <div class="quote"><span class="text">Quote two</span></div>
  <div class="quote"><span class="text">Quote three</span></div>
</body></html>
"""


class TestValidateUrl:
    def test_valid_public_url(self):
        with patch("scraper.socket.gethostbyname", return_value="93.184.216.34"):
            assert validate_url("https://example.com") == "https://example.com"

    def test_rejects_ftp_scheme(self):
        with pytest.raises(URLValidationError, match="Only http/https"):
            validate_url("ftp://example.com")

    def test_rejects_no_scheme(self):
        with pytest.raises(URLValidationError, match="Only http/https"):
            validate_url("example.com")

    def test_rejects_localhost(self):
        with patch("scraper.socket.gethostbyname", return_value="127.0.0.1"):
            with pytest.raises(URLValidationError, match="private/internal"):
                validate_url("http://localhost")

    def test_rejects_private_ip_10(self):
        with patch("scraper.socket.gethostbyname", return_value="10.0.0.1"):
            with pytest.raises(URLValidationError, match="private/internal"):
                validate_url("http://internal-server.com")

    def test_rejects_private_ip_192(self):
        with patch("scraper.socket.gethostbyname", return_value="192.168.1.1"):
            with pytest.raises(URLValidationError, match="private/internal"):
                validate_url("http://my-router.local")

    def test_rejects_metadata_endpoint(self):
        with patch("scraper.socket.gethostbyname", return_value="169.254.169.254"):
            with pytest.raises(URLValidationError, match="private/internal"):
                validate_url("http://169.254.169.254/latest/meta-data/")

    def test_rejects_unresolvable_host(self):
        import socket as _socket
        with patch("scraper.socket.gethostbyname", side_effect=_socket.gaierror("no such host")):
            with pytest.raises(URLValidationError, match="Could not resolve"):
                validate_url("http://doesnotexist.invalid")


class TestScrapePage:
    @patch("scraper.requests.get")
    @patch("scraper.socket.gethostbyname", return_value="93.184.216.34")
    def test_extracts_elements(self, _mock_dns, mock_get):
        mock_resp = MagicMock()
        mock_resp.text = SAMPLE_HTML
        mock_resp.raise_for_status = MagicMock()
        mock_get.return_value = mock_resp

        result = scrape_page("http://example.com", ".quote .text")

        assert len(result) == 3
        assert result[0] == {"text": "Quote one"}
        assert result[1] == {"text": "Quote two"}
        assert result[2] == {"text": "Quote three"}

    @patch("scraper.requests.get")
    @patch("scraper.socket.gethostbyname", return_value="93.184.216.34")
    def test_no_matches_returns_empty(self, _mock_dns, mock_get):
        mock_resp = MagicMock()
        mock_resp.text = "<html><body><p>No quotes here</p></body></html>"
        mock_resp.raise_for_status = MagicMock()
        mock_get.return_value = mock_resp

        result = scrape_page("http://example.com", ".quote .text")
        assert result == []

    def test_rejects_blocked_url(self):
        with patch("scraper.socket.gethostbyname", return_value="127.0.0.1"):
            with pytest.raises(URLValidationError):
                scrape_page("http://localhost", ".quote")
