from ruleflow.core.signals import Signal


def test_signal_connection_and_emission():
    sig: Signal[int, str] = Signal()

    # Trackers
    calls = []

    # 1. Receiver expecting all args
    def receiver_full(a, b):
        calls.append(("full", a, b))

    # 2. Receiver expecting partial args (truncation test)
    def receiver_partial(a):
        calls.append(("partial", a))

    # 3. Receiver expecting no args
    def receiver_none():
        calls.append("none")

    sig.connect(receiver_full)
    sig.connect(receiver_partial)
    sig.connect(receiver_none)

    assert sig.callables_count == 3

    sig.emit(42, "hello")

    assert calls == [
        ("full", 42, "hello"),
        ("partial", 42),
        "none"
    ]


def test_signal_disconnection():
    sig = Signal()
    tracker = []

    def func():
        tracker.append(1)

    sig.connect(func)
    sig.emit()
    assert len(tracker) == 1

    sig.disconnect(func)
    sig.emit()
    assert len(tracker) == 1  # Should not increase
    assert sig.callables_count == 0
