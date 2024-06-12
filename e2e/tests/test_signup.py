from e2e.pages.signup_page import SignupPage


def test_signup(live_server, page_context):
    signup_page = SignupPage(page_context)
    signup_page.navigate(f"{live_server.url}{signup_page.url}")
    signup_page.signup("Pacey Witter", "pacey@gmail.com", "pacey", "pacey", "4@Password")
    # assert page_context.is_visible("#navbar-menu-button")
