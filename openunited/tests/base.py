def clean_up(
    d: dict, extra: list = None, custom: list = None, exclude: list = None
) -> None:
    """
    Removes specified key-value pairs from a dictionary.
    Args:
        d (dict): The dictionary to clean up.
        extra (list, optional): Additional keys to remove. Defaults to None.
        custom (list, optional): Custom list of keys to remove. Overrides `extra` if provided. Defaults to None.
        exclude (list, optional): Keys to exclude from removal. Defaults to None.
    Returns:
        None
    """
    keys_to_remove = ["view", "object", "paginator", "page_obj", "object_list"]
    if custom:
        keys_to_remove = custom
    else:
        if extra:
            keys_to_remove.extend(extra)

    if exclude:
        for item in exclude:
            keys_to_remove.remove(item)

    keys = list(d.keys())
    for key in keys:
        if key in keys_to_remove:
            d.pop(key, None)
