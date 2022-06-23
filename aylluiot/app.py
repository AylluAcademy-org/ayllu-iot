# General imports
import argparse

# Module imports
from aylluiot.utils.path_utils import set_working_path

set_working_path()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Start IoT Services.')
    parser.add_argument('--provider', '-p', type=int, default=1,
                        help='Provide the key for the service to be \
                            initialized. \n1- AWS IoT Core')

    args = parser.parse_args()

    if args.provider == 1:
        from aylluiot.aws.service import Runner
        aws_service = Runner()
        aws_service.run()
    else:
        raise NotImplementedError("Provide a valid option")
