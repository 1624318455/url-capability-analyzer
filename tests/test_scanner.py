import pytest
from pathlib import Path
from scripts.scanner import LocalScanner

def test_scanner_loads_paths():
    scanner = LocalScanner()
    assert "opencode" in scanner.agents
    assert "skills" in scanner.agents["opencode"]
    assert "mcps" in scanner.agents["opencode"]

def test_scanner_expands_home():
    scanner = LocalScanner()
    # The path should be expanded (not contain '~')
    assert "~" not in scanner.agents["opencode"]["skills"]