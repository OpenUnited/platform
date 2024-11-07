from django.views.generic import TemplateView
from django.conf import settings
import os

class MarketingPageView(TemplateView):
    path = None  # Declare the path attribute at class level
    template_name = None  # Optional: declare template_name if you want to use it

    def get_template_names(self):
        # Get the path from URL kwargs or use 'index' as default
        path = self.kwargs.get('path', 'index')
        
        # If no .html extension, add it
        if not path.endswith('.html'):
            path = f"{path}.html"
            
        # Return the full template path
        return [f"landing-pages/{path}"]
