# General imports
from threading import Event, Timer
from datetime import datetime

# Module imports
from src.iot.aws.thing import IotCore
from src.iot.devices import DeviceCardano


class RepeatTimer(Timer):
    """
    Timer extension for continous calling
    """

    def run(self):
        while not self.finished.wait(self.interval):
            self.function(*self.args, **self.kwargs)


class Runner:
    """
    Execution class for IoT Service
    """

    def __init__(self):
        self._msg_counter = 0
        self._thing = IotCore(DeviceCardano)
        self._event_thread = Event()
        self._timer_thread = RepeatTimer(300.0, self._clear_cache)

    @property
    def thing(self):
        return self._thing

    @property
    def event_thread(self):
        return self._event_thread

    @property
    def timer_thread(self):
        return self._timer_thread

    @property
    def msg_counter(self):
        return self._msg_counter

    def _clear_cache(self):
        if self.msg_counter > 2:
            print(f"[{datetime.now()}] Cleaning cached messages #{self.msg_counter}...\n")
            del self.thing.id_cache[self.msg_counter - 1]
        else:
            print(f"[{datetime.now()}] Message cache is clean\n")

    def _initialize_service(self):
        self.thing.start_logging()
        # Start connection
        thing_connection = self.thing.connection.connect()
        thing_connection.result()
        print("\nConnected!\n")
        # Subscribe to topic
        subscribe_future, packet_id = self.thing.topic_subscription()
        print("Subscribed!\n")

    def run(self) -> None:
        """
        Service definition
        """
        # Wait for all messages to be received.
        # This waits forever if count was set to 0.
        # if args.count != 0 and not received_all_event.is_set():
        #     print("Waiting for all messages to be received...")

        # Prevents the execution of the code below (Disconnet) while
        # received_all_event flag is False
        self._initialize_service()
        self.timer_thread.start()
        self.event_thread.wait()

        # Disconnect
        print("Disconnecting...")
        disconnect_future = self.thing.connection.disconnect()
        disconnect_future.result()
        print("Disconnected!")
