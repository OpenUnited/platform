from django.urls import path
from .views import MarketingPageView

app_name = 'marketing'

urlpatterns = [
    path('', MarketingPageView.as_view(path='index'), name='index'),
    path('<path:path>', MarketingPageView.as_view(), name='marketing_page'),
]
