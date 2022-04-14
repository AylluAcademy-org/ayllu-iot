"""
Utils submodule related with path and files on system
"""

# General imports
import sys
import os
import logging
from pathlib import Path
from typing import Union


def get_root_path() -> str:
    """
    Set working directory for project root independently of runner device

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


def set_working_path(target_paths: Union[str, list] = None) -> None:
    """
    Add to path the target routes passed down which are also included inside
    the repository folder

    Parameters
    ----------
    target_paths: Union[str, list], default=None
        Folder(s) and/or file(s) to be included in path.
        When default, still appends root directory to path. 
    """
    working_dir = get_root_path()
    if isinstance(list, target_paths):
        for t_path in target_paths:
            n_dir = f'{working_dir}/{t_path}'
            sys.path.insert(0, n_dir)
    elif isinstance(str, target_paths):
        n_dir = f'{working_dir}/{target_paths}'
        sys.path.insert(0, n_dir)
    else:
        sys.path.insert(0, working_dir)


def create_folder(target_path: Union[str, list]) -> None:
    """
    Creates a folder in the indicated path(s)

    Parameters
    ----------
    target_path: Union[str, list]
        Individual or list of path to folders to be created
    """
    if isinstance(target_path, list):
        for t_path in target_path:
            if not os.path.exists(t_path):
                os.makedirs(t_path)
                logging.info("Folder created at `%s`", t_path)
            else:
                logging.info("Folder `%s` already exists", t_path)
    else:
        if not os.path.exists(target_path):
            os.makedirs(target_path)
            logging.info("Folder created at `%s`", target_path)
        else:
            logging.info("Folder `%s` already exists", target_path)


def remove_folder(target_path: Union[str, list]) -> None:
    """
    Deletes folder at system level

    Parameters
    ---------
    target_path: Union[str, list]
        Individual or list of path to folders to be deleted
    """
    if isinstance(target_path, list):
        for t_path in target_path:
            if os.path.exists(t_path):
                os.remove(t_path)
                logging.info("Folder removed at %s", t_path)
            else:
                logging.info("Folder %s did not exists", t_path)
    else:
        if os.path.exists(target_path):
            os.remove(target_path)
            logging.info("Folder removed at %s", target_path)
        else:
            logging.info("Folder %s did not exists", target_path)
