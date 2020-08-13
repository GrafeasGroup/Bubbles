from typing import Any, Callable, Tuple, Dict
import threading


def fire_and_forget(
    func: Callable[[Any], Any], *args: Tuple, **kwargs: Dict
) -> Callable[[Any], Any]:
    """
    Decorate functions to build a thread for a given function and trigger it.

    Originally from https://stackoverflow.com/a/59043636, this function
    prepares a thread for a given function and then starts it, intentionally
    severing communication with the thread so that we can continue moving
    on.

    This should be used sparingly and only when we are 100% sure that
    the function we are passing does not need to communicate with the main
    process and that it will exit cleanly (and that if it explodes, we don't
    care).
    """

    def wrapped(*args: Tuple, **kwargs: Dict) -> None:
        threading.Thread(target=func, args=(args), kwargs=kwargs).start()

    return wrapped
