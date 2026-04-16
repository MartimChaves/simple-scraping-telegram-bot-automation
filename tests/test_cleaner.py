"""Tests for the cleaner module."""

import json

from cleaner import clean_data, export_data


class TestCleanData:
    def test_strips_whitespace(self):
        raw = [{"text": "  hello  "}, {"text": "world "}]
        result = clean_data(raw)
        assert result == [{"text": "hello"}, {"text": "world"}]

    def test_removes_duplicates(self):
        raw = [{"text": "same"}, {"text": "same"}, {"text": "different"}]
        result = clean_data(raw)
        assert len(result) == 2
        assert result[0] == {"text": "same"}
        assert result[1] == {"text": "different"}

    def test_removes_duplicates_after_trimming(self):
        raw = [{"text": "hello "}, {"text": " hello"}]
        result = clean_data(raw)
        assert len(result) == 1
        assert result[0] == {"text": "hello"}

    def test_empty_input(self):
        assert clean_data([]) == []


class TestExportData:
    def test_json_export(self):
        data = [{"text": "one"}, {"text": "two"}]
        result = export_data(data, "JSON")
        parsed = json.loads(result)
        assert parsed == data

    def test_csv_export(self):
        data = [{"text": "one"}, {"text": "two"}]
        result = export_data(data, "CSV")
        lines = result.strip().splitlines()
        assert lines[0] == "text"
        assert lines[1] == "one"
        assert lines[2] == "two"

    def test_csv_empty(self):
        assert export_data([], "CSV") == ""

    def test_case_insensitive_format(self):
        data = [{"text": "hello"}]
        result = json.loads(export_data(data, "json"))
        assert result == data
