from django import template
from django.utils.safestring import mark_safe

register = template.Library()

@register.simple_tag
def generate_summary_structure(items, depth=0, displayed_items=None):
    if displayed_items is None:
        displayed_items = set()
        
    html = []
    for item in items:
        if item not in displayed_items:
            displayed_items.add(item)
            
            html.append(f'''
                <div class="nested-item flex flex-col {'pl-4 lg:pl-8' if depth > 1 else ''}">
                    <div class="nested-item__label flex items-start py-1.5 border-t border-solid border-gray-100">
                        <button type="button" 
                            class="{'opacity-0 pointer-events-none' if not item.descendants.exists() else ''} nested-item__label-icon h-[22px] w-4 mr-1 flex items-center justify-center shrink-0 rounded-full focus:outline-none focus:ring-0 p-0.5 appearance-none">
                            <!-- Button content -->
                        </button>
                        <span class="flex flex-col flex-1">
                            <span class="flex items-center">
                                <a href="{{% url 'capability-detail' product_slug item.id %}}" class="mr-2">{item.name}</a>
                            </span>
                            <span class="flex text-sm leading-6 text-gray-700 font-normal mt-0.5">
                                {item.description}
                            </span>
                        </span>
                    </div>
                    
                    {generate_summary_structure(item.descendants.all(), depth + 1, displayed_items) if item.descendants.exists() else ''}
                </div>
            ''')
    
    return mark_safe('\n'.join(html))

# You can register multiple tags in the same file
@register.simple_tag
def another_tag():
    return "Hello"

# You can also register filters
@register.filter
def my_filter(value):
    return value.lower()