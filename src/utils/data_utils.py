def check_nested_dicts(vals: dict):
    if any(isinstance(v, dict) for v in vals.values()):
        return True
    else:
        return False

def flatten_dict(d, parent_key='', sep=''):
    """
    Credits to:
    stackoverflow.com/questions/6027558/flatten-nested-dictionaries-compressing-keys#6027615
    """
    items = []
    for k, v in d.items():
        nk = parent_key + sep + str(k) if parent_key else k
        try:
            items.extend(flatten_dict(v, nk, sep=sep).items())
        except AttributeError:
            items.append((nk, v))
    return dict(items)