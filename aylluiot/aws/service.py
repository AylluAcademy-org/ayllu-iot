"""
Runner for AWS IoT Thing Implementation
"""

# General imports
from threading import Event, Timer
from datetime import datetime

# Module imports
from aylluiot.aws.thing import IotCore


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

    Attributes
    ---------
    thing: IotCore
        Instance of IotCore Thing object.
    event_thread: Event
        Loop object for asynchronous execution.
    cache_timer: RepeatTimer
        Timer implementation to schedule an asynchronous action that cleans up
        the Thing `id_cache`.
    queue_timer: RepeatTimer
        Timer implementation to schedule an asynchronous action that cleans up
        any sub-topic queued that failed at execution and has been stuck
        on memory.
    """

    _thing: IotCore
    _event_thread: Event
    _cache_timer: RepeatTimer
    _queue_timer: RepeatTimer

    def __init__(self, thing_object: IotCore) -> None:
        """
        Constructor method for Runner object.
        """
        self._thing = thing_object
        self._event_thread = Event()
        self._cache_timer = RepeatTimer(300.0, self._clear_cache)
        self._queue_timer = RepeatTimer(3600.0, self._clear_remnants)

    @property
    def thing(self) -> IotCore:
        """
        Getter method for `thing` attribute.

        Returns
        -------
        IotCore
            Thing instance.
        """
        return self._thing

    @property
    def event_thread(self) -> Event:
        """
        Getter method for `event_thread` attribute.

        Returns
        ------
        Event
            Event Loop object.
        """
        return self._event_thread

    @property
    def cache_timer(self) -> RepeatTimer:
        """
        Getter method for `cache_timer` attribute.

        Returns
        ------
        RepeatTimer
            RepeatTimer instance with `_clear_cache` as callback.
        """
        return self._cache_timer

    @property
    def queue_timer(self) -> RepeatTimer:
        """
        Getter method for `queue_timer` attribute.

        Returns
        ------
        RepeatTimer
            RepeatTimer instance with `_clear_remnants` as callback.
        """
        return self._queue_timer

    def _clear_cache(self) -> None:
        """
        Internal helper function to clean up the `id_cache` of Thing object.
        """
        msg_counter = len(self.thing.id_cache)
        if msg_counter > 2:
            print(f"[{datetime.now()}] Cleaning cached messages \
                    #{msg_counter}...\n")
            del self.thing.id_cache[msg_counter]
        else:
            print(f"[{datetime.now()}] Message cache is clean\n")

    def _clear_remnants(self) -> None:
        """
        Internal helper function to clean up any stuck sub-topic in running
        `topic_queue` of Thing object.
        """
        to_clean = [topic for topic, cache in self.thing.topic_queue.items()
                    if self._time_diff(cache['start_time']) >= 1]
        print(
            f"[{datetime.now()}] Executing clean up of Queues for \
                {len(to_clean)} topics...\n")
        for remnant in to_clean:
            self.thing.topic_queue.pop(remnant)
            print(f"[{datetime.now()}] Topic {remnant} erased...\n")

    def _time_diff(self, start_time: datetime) -> int:
        """
        Internal helper function to calculate a time difference with time at
        function call.

        Parameters
        ----------
        start_time: datetime
            The initial time to be compare with.

        Returns
        -------
        int
            Difference of days from both times.
        """
        diff = datetime.now() - start_time
        return diff.days

    def _initialize_service(self) -> None:
        """
        Internal helper function that set-up the context for the runner.
        """
        self.thing.start_logging()
        # Start connection
        thing_connection = self.thing.connection.connect()
        thing_connection.result()
        print("\nConnected!\n")
        # Subscribe to topic
        _ = self.thing.topic_subscription()
        print("Subscribed!\n")

    def run(self) -> None:
        """
        Service main function that initializes the daemon.
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
