from e2e.pages.login_page import LoginPage

def login_user(page, live_server_url, username, password):
    login_page = LoginPage(page)
    login_page.navigate(f"{live_server_url}{login_page.url}")
    login_page.login(username, password)
