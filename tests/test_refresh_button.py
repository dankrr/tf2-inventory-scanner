from flask import render_template
from bs4 import BeautifulSoup


def test_refresh_button_has_button_type(app):
    with app.test_request_context():
        html = render_template("index.html", steamids="", users=[], ids=[])
    soup = BeautifulSoup(html, "html.parser")
    refresh_btn = soup.find("button", id="refresh-failed-btn")
    assert refresh_btn is not None
    assert refresh_btn.get("type") == "button"
