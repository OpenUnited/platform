from urllib.parse import urlparse

def serialize_skills(node):
    """Serializer for the tree."""
    return {
        "id": node.pk,
        "name": node.name,
        "children": [serialize_skills(child) for child in node.get_children],
    }


def serialize_expertise(node):
    """Serializer for the tree."""
    return {
        "id": node.pk,
        "name": node.name,
        "skill": node.skill.pk,
        "children": [serialize_expertise(child) for child in node.get_children],
    }


def get_path_from_url(url: str, remove_trailing_slash: bool = False) -> str:
    """Extract path from URL, optionally removing trailing slash"""
    if not url:
        return ""
    
    parsed = urlparse(url)
    path = parsed.path or parsed.netloc or url
    
    if remove_trailing_slash and path.endswith('/'):
        path = path[:-1]
        
    return path


class MacrosFun:
    @staticmethod
    def skill_filter_tree(skills, skill_id, show_all=False):
        # Your skill filter tree implementation here
        options = []
        for skill in skills:
            selected = str(skill.id) == str(skill_id) if skill_id else False
            options.append(f'<option value="{skill.id}" {"selected" if selected else ""}>{skill.name}</option>')
        return '\n'.join(options)

macros_fun = MacrosFun()
