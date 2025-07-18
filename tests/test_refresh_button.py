from quart import render_template
from bs4 import BeautifulSoup

import pytest


@pytest.mark.asyncio
async def test_refresh_button_has_button_type(app):
    async with app.test_request_context("/"):
        html = await render_template(
            "index.html", steamids="", users=[], ids=[], failed_ids=[]
        )
    soup = BeautifulSoup(html, "html.parser")
    refresh_btn = soup.find("button", id="refresh-failed-btn")
    assert refresh_btn is not None
    assert refresh_btn.get("type") == "button"
