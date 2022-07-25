"""
This is a demonstration on how to create a basic AWS service with the
library
"""

from pathlib import Path

from aylluiot.aws import thing, service
from aylluiot.devices import DeviceExecutors
from aylluiot.utils.path_utils import set_working_path

class MockExecutor:
    def __init__(self)-> None:
        """
        Just for demo purposes. Feel free to add any functionatility to
        test it out from IoT Core.
        """
        pass

    def hello_world(self) -> str:
        """
        Demo function that returns string `Hello World`.
        """
        return 'Hello World'

def aws_service():
    current_path = Path(__file__).parent.parent # On production set it manually
    # As when you import the library, this path could not be set accordingly
    set_working_path(current_path)
    instace = DeviceExecutors('Demo', [MockExecutor])
    thing_instace = thing.IotCore(handler_object=instace, \
                        config_path=f"{current_path}/config/aws_config.json")
    return service.Runner(thing_instace)

if __name__ == "__main__":
    runner = aws_service()
    runner.run()