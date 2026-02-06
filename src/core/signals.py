from typing import Callable, Hashable, Any


class Signal:
    """Implements a QT-like signal system with instance-specific filtering."""
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
        if args and args[0] in self.restricted_callables:
            for c in self.restricted_callables[args[0]]:
                c(*args, **kwargs)

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
