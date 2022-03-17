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
    for d in str(Path(__file__)).split('/'):
        if d != root_dir_name:
            root_path += d + '/'
        else:
            break
    return root_path + root_dir_name

def set_working_path() -> None:
    working_dir = get_root_path()
    sys.path.insert(0, working_dir)
    return None