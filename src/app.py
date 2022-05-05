# General imports
import argparse

# Module imports
from utils.path_utils import set_working_path

set_working_path()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Start IoT Services.')
    parser.add_argument('--provider', '-p', type=int, default=1,
                        help='Provide the key for the service to be \
                            initialized. \n1- AWS IoT Core')

    args = parser.parse_args()

    if args.provider == 1:
        from iot.aws.service import run_iot
        run_iot()
    else:
        raise NotImplementedError("Provide a valid option")
