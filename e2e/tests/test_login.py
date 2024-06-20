from e2e.helpers import login_user
from e2e.pages.login_page import LoginPage


def test_login(live_server, page_context, create_user):
    _, username, password, _ = create_user
    login_user(page_context, live_server.url, username, password)
    # assert page_context.is_visible("#navbar-menu-button")
