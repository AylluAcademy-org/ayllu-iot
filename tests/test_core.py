"""
Suite of tests for 'core' sub-module.
"""

# General imports
import logging
# Package imports
from aylluiot.core import Processor

def test_processor_getter() -> None:
    """
    Test classmethod to get processor.
    """
    private_executor = Processor._executor_processor
    private_relayer = Processor._relayer_processor

    assert private_executor == Processor.device_processor(1)
    assert private_relayer == Processor.device_processor(2)

    try:
        Processor.device_processor(3)
    except TypeError:
        logging.info('Expected Error checked!\n')
