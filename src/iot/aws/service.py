# General imports
import threading

# Module imports
from src.iot.aws.thing import IotCore
from src.iot.devices import DeviceCardano

received_count = 0
received_all_event = threading.Event()


def run_iot() -> None:
    """
    Service definition
    """
    # print("Connecting to {} with client ID '{}'...".format(
    #     endpoint, client_id))

    thing = IotCore(DeviceCardano)

    thing.start_logging()

    connect_future = thing.connection.connect()

    # Future.result() waits until a result is available
    connect_future.result()
    print("Connected!")

    # Subscribe
    # print("Subscribing to topic '{}'...".format(topic))
    subscribe_future, packet_id = thing.topic_subscription()

    # subscribe_result = subscribe_future.result()
    # print("Subscribed with {}".format(str(subscribe_result['qos'])))
    print("Subscribed!")

    # Wait for all messages to be received.
    # This waits forever if count was set to 0.
    # if args.count != 0 and not received_all_event.is_set():
    #     print("Waiting for all messages to be received...")

    # Prevents the execution of the code below (Disconnet) while
    # received_all_event flag is False
    received_all_event.wait()

    print(f"{received_count} message(s) received.")

    # Disconnect
    print("Disconnecting...")
    disconnect_future = thing.connection.disconnect()
    disconnect_future.result()
    print("Disconnected!")
