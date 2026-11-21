import re
from datetime import datetime
from pathlib import Path
from urllib.parse import urlsplit

import httpx
import pytest


@pytest.mark.asyncio
async def test_footer_links_have_working_public_destinations(ui_app):
    from everwealth.auth import auth_user
    from everwealth.db import get_connection

    async def unexpected_dependency():
        pytest.fail("Public marketing pages must not need authentication or a database")

    ui_app.dependency_overrides[auth_user] = unexpected_dependency
    ui_app.dependency_overrides[get_connection] = unexpected_dependency
    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=ui_app), base_url="http://test") as client:
        home = await client.get("/")
        assert home.status_code == 200
        footer = home.text.split('<footer class="site-footer wrap">')[1].split("</footer>")[0]
        for heading in ("Product", "Resources", "Your account"):
            assert heading in footer
        assert f"{datetime.now().year} Jaxon" in footer
        for path in ("/privacy", "/terms", "/cookies"):
            assert f'href="{path}"' in footer
        pages = {"/": home.text}
        for href in re.findall(r'href="([^"]+)"', footer):
            assert href != "#"
            url = urlsplit(href)
            path = url.path or "/"
            if path.startswith("/static/"):
                assert Path("everwealth", path.lstrip("/")).is_file()
                continue
            if path not in pages:
                response = await client.get(path)
                assert response.status_code == 200, path
                pages[path] = response.text
            if url.fragment:
                assert f'id="{url.fragment}"' in pages[path]
        for path in ("/about", "/help", "/privacy", "/terms", "/cookies"):
            assert pages[path].count("<footer ") == 1
            assert pages[path].count("<h1") == 1
            assert "<title>" in pages[path]
        assert "<details>" in pages["/help"]


@pytest.mark.asyncio
@pytest.mark.parametrize("path, heading", [
    ("/privacy", "Privacy policy"),
    ("/terms", "Terms of use"),
    ("/cookies", "Cookies &amp; storage"),
])
async def test_legal_pages_are_identified_as_drafts(ui_app, path, heading):
    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=ui_app), base_url="http://test") as client:
        response = await client.get(path)
    assert response.status_code == 200
    assert f"<h1>{heading}</h1>" in response.text
    assert '<meta name="robots" content="noindex">' in response.text
    assert "Draft for review" in response.text
    assert "Not yet effective" in response.text
    assert "legal operator, contact details" in response.text


@pytest.mark.asyncio
@pytest.mark.parametrize("path", ["/login", "/register"])
async def test_policy_links_are_available_at_sign_in_and_registration(ui_app, path):
    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=ui_app), base_url="http://test") as client:
        response = await client.get(path)
    assert response.status_code == 200
    assert 'aria-label="Legal information"' in response.text
    for legal_path in ("/privacy", "/terms", "/cookies"):
        assert f'href="{legal_path}"' in response.text
    assert "By creating an account, you agree" not in response.text
