from typing import Callable, Hashable, Any


class Signal:
    """Implements a QT-like signal system with instance-specific filtering.

    Please note that any connected functions will KEEP result in them staying alive in memory until disconnected (so make sure to disconnect any methods before deleting and object).
    """
    __slots__ = ('callables', 'restricted_callables')

    def __init__(self) -> None:
        self.callables: list[Callable] = []
        # Maps a specific instance to a list of callbacks intended only for it (the caller must pass the hashable as args[0])
        self.restricted_callables: dict[Hashable, list[Callable]] = {}

    @property
    def callables_count(self) -> int:
        return len(self.callables) + sum(len(v) for v in self.restricted_callables.values())

    def emit(self, *args: Any, **kwargs: Any) -> None:
        # Standard global callbacks
        for c in self.callables:
            c(*args, **kwargs)

        # Instance-restricted callbacks
        try:
            for c in self.restricted_callables[args[0]]:
                c(*args, **kwargs)
        except (TypeError,  # in the event that args[0] is not hashable... must use try-catch due to fake hash being detected on certain objects (like RuleMatch) that contain un-hashables.
                KeyError,  # if the args[0] does not exist in the dictionary
                IndexError):  # if the index 0 does not exist in args.
            pass

    def connect(self, func: Callable, restrict_to_instance: Hashable = None) -> None:
        if restrict_to_instance is not None:
            callbacks = self.restricted_callables.setdefault(restrict_to_instance, [])
            if func not in callbacks:
                callbacks.append(func)
        else:
            if func not in self.callables:
                self.callables.append(func)

    def disconnect(self, func: Callable, restrict_to_instance: Hashable = None) -> None:
        try:
            if restrict_to_instance is not None:
                self.restricted_callables[restrict_to_instance].remove(func)
                if not self.restricted_callables[restrict_to_instance]:
                    del self.restricted_callables[restrict_to_instance]
            else:
                self.callables.remove(func)
        except (ValueError, KeyError):
            pass
