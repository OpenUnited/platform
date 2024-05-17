from playwright.sync_api import Page

class BasePage:
    def __init__(self, page: Page):
        self.page = page

    def navigate(self, url):
        self.page.goto(url)
    
    # def go_to_page(self):
        # self.page.goto(self.url)

