"""
Utils submodule related with path and files on system
"""

# General imports
import sys
import os
import os.path
import shutil
import logging
from pathlib import Path
from typing import Union


def get_root_path() -> str:
    """
    Set working directory for project root independently of user.

    Returns
    ------
    working_dir: str
        Full path to working directory
    """
    root_dir_name = 'ayllu-iot'
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
    if isinstance(target_paths, list):
        for t_path in target_paths:
            n_dir = f'{working_dir}/{t_path}'
            sys.path.insert(0, n_dir)
    elif isinstance(target_paths, str):
        n_dir = f'{working_dir}/{target_paths}'
        sys.path.insert(0, n_dir)
    else:
        sys.path.insert(0, working_dir)


def join_paths(left_side: str, right_side: str) -> str:
    """
    Join two parts of a path

    Parameters
    ----------
    left_side: str
        Root component of path. Which will be the left side of concatenation.
    right_side: str
        Relative path to component. Is able to be fitted as complement of
        left side.

    Returns
    str
        New full path with given components concatenation.
    """
    n_left = '/'.join(left_side.split('/')[:-1]) \
        if left_side.split('/')[-1] == '' else left_side
    n_right = '/'.join(right_side.split('/')[1:]) \
        if right_side.split('/')[0] == '.' else right_side
    return os.path.join(n_left, n_right)


def validate_path(input_path: str, use_root: bool = False,
                  exists: bool = False) -> str:
    """
    Turn a relative path into an absolute one or returns one path that could
    be left joined with a parent path

    Parameters
    ----------
    input_path: str
        The given relative path to be processed.
    use_root: bool, default = False
        If the repository should be use as root for the `input_path` or not.
    exists: bool, default = False
        If the path is exists on the system or not.

    Returns
    ------
    str
        Valid path attending to the given conditions provide.
    """
    if input_path.split('/')[0] == '.' or input_path.split('/')[0] == '..':
        if use_root and exists:
            return _find_path(get_root_path(),
                              '/'.join(input_path.split('/')[1:]))
        elif use_root and not exists:
            return join_paths(get_root_path(),
                              '/'.join(input_path.split('/')[1:]))
        else:
            return '/'.join(input_path.split('/')[1:])
    else:
        if use_root and exists:
            return _find_path(get_root_path(), input_path)
        elif use_root and not exists:
            return join_paths(get_root_path(), input_path)
        else:
            return input_path


def _find_path(starting_path: str, target_path: str) -> str:
    """
    Helper function to determine if an object exists or not in the system given
    an absolute starting point an a relative target name.

    Parameters
    ---------
    starting_path: str
        Root path to be use as starting point.
    target_path: str
        Relative target directory or file to be found.

    Returns
    -------
    return_path: str
        The full path where to find the target object.
    """
    # To-do: It needs to verify if the starting_path is not already contain
    # in the target path before going trough os.listdir()
    return_path: str
    try:
        if target_path.split('/')[0] in os.listdir(starting_path):
            return_path = f"{starting_path}/{target_path}"
        else:
            new_start = f"{starting_path}/{target_path.split('/')[0]}"
            _find_path(new_start, '/'.join(target_path.split('/')[1:]))
    except IndexError:
        raise KeyError("The provided path was not found in the Library folder")
    return return_path


def only_folder_path(input_str: str) -> str:
    """
    Validate if an inputed path is a folder. If it is a file
    it cuts it down to its parent.

    Parameters
    ----------
    input_str: str
        The path to be evaluated.

    Returns
    -------
    str
        Valid path until the last avilable folder given the tree directory.
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


def file_exists(target_path: Union[str, list[str]],
                is_absolute: bool = False) -> Union[bool, list[bool]]:
    """
    Verify wether a file exists or not.

    Parameters
    ----------
    target_path: Union[str, list]
        Single or list of target paths to check.

    Returns
    -------
    Union[bool, list[bool]]
        Single or list of boolean values indicated wether the inputed files
        exists or not.
    """
    if isinstance(target_path, str):
        if is_absolute:
            return os.path.exists(target_path)
        else:
            return os.path.exists(validate_path(target_path, True))
    else:
        if is_absolute:
            return [os.path.exists(p) for p in target_path]
        else:
            return [os.path.exists(validate_path(p, True))
                    for p in target_path]


def save_file(content: Union[str, dict],
              target_path: str = '../default.txt') -> None:
    """
    Saves strings to a file specified by inputed path.

    Parameters
    ----------
    content: Union[str, dict]
        The string to be saved as a file.
    target_path: str
        Location to save the resulting file, including its name and extension.
    """
    create_folder(target_path)
    with open(target_path, 'w') as file:
        file.write(str(content))
    logging.info(f'File created at {target_path}')


def remove_file(input_path: str) -> None:
    """
    Deletes a file from syste.

    Parameters
    ---------
    input_path: str
        Path of file to delete.
    """
    if os.path.exists(input_path):
        os.remove(input_path)
