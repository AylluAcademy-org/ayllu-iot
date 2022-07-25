"""
Suite of tests for library 'data' utilities submodule.
"""
# General imports
from pathlib import Path
# Package imports
from aylluiot.utils.path_utils import set_working_path, get_root_path


def test_root_path() -> None:
    """
    Testing for both functions related with working path.
    """
    try:
        _ = get_root_path('ayllu-iot')
    except KeyError:
        pass  # We haven't add the path yet.
    _current_path = str(Path(__file__).parent.parent)
    set_working_path(_current_path)
    output = get_root_path('ayllu-iot')
    assert output == _current_path
