"""
Suite of tests for library 'utilities' module.
"""

# Package imports
from aylluiot.utils.data_utils import parse_inputs


def test_parse_inputs() -> None:
    """
    Suite of tests for parsing_inputs.
    """
    test_keywords = ['var_1', 'var_2']

    test_kwargs = {'var_1': 'abc', 'var_2': 123}
    test_args_one = ('abc', 123)
    test_args_two = (test_kwargs, )

    output_1_a, output_1_b = parse_inputs(keywords=test_keywords,
                                          _args=test_args_one)
    output_2_a, output_2_b = parse_inputs(keywords=test_keywords, 
                                            _args=test_args_two)

    output_1_c, output_1_d = parse_inputs(keywords=test_keywords,
                                          _kwargs=test_kwargs)

    assert output_1_a == output_2_a
    assert output_1_a == output_1_c
    assert output_1_b == output_2_b
    assert output_1_b == output_1_d
