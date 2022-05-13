"""
Utils submodule related with path and files on system
"""

# General imports
import sys
import os
import shutil
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


def join_paths(left_side: str, right_side: str):
    """
    Join to parts of a path
    """
    n_left = '/'.join(left_side.split('/')[:-1]) \
        if left_side.split('/')[-1] == '' else left_side
    n_right = '/'.join(right_side.split('/')[1:]) \
        if right_side.split('/')[0] == '.' else right_side
    return f"{n_left}/{n_right}"


def validate_path(input_path: str, use_parent: bool = False) -> str:
    """
    Turn a relative path into an absolute one or returns one path that could
    be left joined with a parent path
    """
    if use_parent:
        if input_path.split('/')[0] == '.':
            root_path = str(Path(__file__))
            return f"{root_path}/{input_path}"
        elif input_path.split('/')[0] == '..':
            root_path = str(Path(__file__).parent)
            return f"{root_path}/{input_path}"
    else:
        if input_path.split('/')[0] == '.' \
                or input_path.split('/')[0] == '..':
            return '/'.join(input_path.split('/')[1:])


def only_folder_path(input_str: str) -> str:
    """
    Validate if an inputed path is a folder. If it is a file
    it cuts it down to its parent
    """
    return input_str if len(input_str.split('/')[-1].split('.')) == 1\
        else '/'.join(input_str.split('/')[:-1])


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
            only_folder = only_folder_path(t_path)
            if not os.path.exists(only_folder):
                os.makedirs(only_folder)
                logging.info("Folder created at `%s`", only_folder)
            else:
                logging.info("Folder `%s` already exists", only_folder)
    else:
        only_folder = only_folder_path(target_path)
        if not os.path.exists(only_folder):
            os.makedirs(only_folder)
            logging.info("Folder created at `%s`", only_folder)
        else:
            logging.info("Folder `%s` already exists", only_folder)


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
            only_folder = only_folder_path(t_path)
            if os.path.exists(only_folder):
                shutil.rmtree(only_folder)
                logging.info("Folder removed at %s", only_folder)
            else:
                logging.info("Folder %s did not exists", only_folder)
    else:
        only_folder = only_folder_path(target_path)
        if os.path.exists(only_folder):
            shutil.rmtree(only_folder)
            logging.info("Folder removed at %s", only_folder)
        else:
            logging.info("Folder %s did not exists", only_folder)


def file_exists(target_path: Union[str, list]) -> Union[bool, list]:
    """
    Verify wether a file exists or not
    """
    if isinstance(target_path, str):
        return os.path.exists(target_path)
    else:
        return [os.path.exists(p) for p in target_path]
