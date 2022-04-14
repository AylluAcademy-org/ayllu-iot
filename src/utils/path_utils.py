import sys
from pathlib import Path


def get_root_path() -> str:
    """
    Set working directory for project
    root independently of runner device

    Returns
    ------
    working_dir: str
        Full path to working directory
    """
    root_dir_name = 'CardanoPython'
    root_path = ''
    path_list = str(Path(__file__)).split('/')
    index = 0
    for d in path_list:
        if d != root_dir_name:
            root_path += d + '/'
            index += 1
        else:
            if (path_list[index + 1] == root_dir_name):
                root_path += d + '/'
                break
            else:
                break
    return root_path + root_dir_name


def set_working_path(target: list = []) -> None:
    """
    """
    working_dir = get_root_path()
    if target:
        for t in target:
            n_dir = f'{working_dir}/{t}'
            sys.path.insert(0, n_dir)
    else:
        sys.path.insert(0, working_dir)
    return None
