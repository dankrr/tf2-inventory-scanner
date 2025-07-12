import importlib
from pathlib import Path
import subprocess

import pytest
from flask import render_template
from bs4 import BeautifulSoup


@pytest.fixture
def app(monkeypatch):
    monkeypatch.setenv("STEAM_API_KEY", "x")
    monkeypatch.setenv("BPTF_API_KEY", "x")
    monkeypatch.setattr("utils.local_data.load_files", lambda *a, **k: ({}, {}))
    monkeypatch.setattr(
        "utils.price_loader.ensure_prices_cached",
        lambda refresh=False: Path("prices.json"),
    )
    monkeypatch.setattr(
        "utils.price_loader.ensure_currencies_cached",
        lambda refresh=False: Path("currencies.json"),
    )
    monkeypatch.setattr("utils.price_loader.build_price_map", lambda path: {})
    monkeypatch.setattr("utils.price_loader.PRICE_MAP_FILE", Path("price_map.json"))
    monkeypatch.setattr(
        "utils.price_loader.dump_price_map",
        lambda mapping, path=Path("price_map.json"): path,
    )
    mod = importlib.import_module("app")
    importlib.reload(mod)
    return mod.app


def test_killstreak_badge_color(app):
    item = {"killstreak_name": "Professional Killstreak", "sheen_color": "#8847ff"}
    with app.app_context():
        html = render_template("_modal.html", item=item)
    soup = BeautifulSoup(html, "html.parser")
    badge = soup.find("span", class_="killstreak-badge")
    assert badge is not None
    assert badge.text.strip() == "Professional Killstreak"
    assert "#8847ff" in badge.get("style", "")


def test_craftable_text_shown(app):
    item = {"craftable": True}
    with app.app_context():
        html = render_template("_modal.html", item=item)
    soup = BeautifulSoup(html, "html.parser")
    assert "Craftable" in soup.text


def test_uncraftable_text_shown(app):
    item = {"craftable": False}
    with app.app_context():
        html = render_template("_modal.html", item=item)
    soup = BeautifulSoup(html, "html.parser")
    assert "Uncraftable" in soup.text


def test_modal_title_fallback_chain(tmp_path):
    script = tmp_path / "test.js"
    script.write_text(
        """
const fs = require('fs');
const vm = require('vm');
const code = fs.readFileSync('static/modal.js', 'utf8');
const elements = {};
const document = { getElementById: id => (elements[id] ||= { textContent: '' }) };
const window = { document };
vm.runInNewContext(code, { window, document });
const modal = window.modal;
function check(data, expected) {
  elements['modal-title'] = { textContent: '' };
  elements['modal-custom-name'] = { textContent: '' };
  elements['modal-effect'] = { textContent: '' };
  modal.updateHeader(data);
  if (elements['modal-title'].textContent !== expected) {
    throw new Error('Expected ' + expected + ' got ' + elements['modal-title'].textContent);
  }
}
check({ composite_name: 'Comp' }, 'Comp');
check({ display_base: 'Base' }, 'Base');
check({ resolved_name: 'Resolved' }, 'Resolved');
check({ base_name: 'BN' }, 'BN');
check({ display_name: 'DN' }, 'DN');
check({ name: 'Name' }, 'Name');
console.log('ok');
"""
    )

    result = subprocess.run(
        ["node", str(script)], capture_output=True, text=True, check=True
    )
    assert "ok" in result.stdout
