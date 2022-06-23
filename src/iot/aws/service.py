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
        self._thing = IotCore(DeviceCardano)
        self._event_thread = Event()
        self._cache_timer = RepeatTimer(300.0, self._clear_cache)
        self._queue_timer = RepeatTimer(3600.0, self._clear_remnants)

    @property
    def thing(self):
        return self._thing

    @property
    def event_thread(self):
        return self._event_thread

    @property
    def cache_timer(self):
        return self._cache_timer

    @property
    def queue_timer(self):
        return self._queue_timer

    def _clear_cache(self):
        msg_counter = len(self.thing.id_cache)
        if msg_counter > 2:
            print(f"[{datetime.now()}] Cleaning cached messages #{msg_counter}...\n")
            del self.thing.id_cache[msg_counter]
        else:
            print(f"[{datetime.now()}] Message cache is clean\n")

    def _clear_remnants(self):
        to_clean = [topic for topic, cache in self.thing.topic_queue.items()
                    if self._time_diff(cache['start_time']) >= 1]
        print(f"[{datetime.now()}] Executing clean up of Queues for {len(to_clean)} topics...\n")
        for remnant in to_clean:
            self.thing.topic_queue.pop(remnant)
            print(f"[{datetime.now()}] Topic {remnant} erased...\n")

    def _time_diff(self, start_time: datetime):
        diff = datetime.now() - start_time
        return diff.days

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
        self.cache_timer.start()
        self.queue_timer.start()
        self.event_thread.wait()

        # Disconnect
        print("Disconnecting...")
        disconnect_future = self.thing.connection.disconnect()
        disconnect_future.result()
        print("Disconnected!")
