from .models import PersonSkill


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
        "children": [
            serialize_expertise(child) for child in node.get_children
        ],
    }
