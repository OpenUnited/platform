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
