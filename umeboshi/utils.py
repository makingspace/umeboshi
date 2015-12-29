"""
Umeboshi provides two locking mechanisms. If using a cache with its own
`lock()` method (such as [python redis lock][prs]), it will make use of that.
Otherwise it provides its own simple locking implementation.

[prs]: https://pypi.python.org/pypi/python-redis-lock
"""
from django.core.cache import cache
import contextlib
import time

__all__ = ('lock',)

lock_key = 'umeboshi-event-{}'


@contextlib.contextmanager
def simple_lock(lock_key, timeout=5000):
    """
    A simple context manager that raises the passed exception
    if a lock can't be acquired.
    """

    acquire_lock = lambda: cache.add(lock_key, 1, timeout)
    release_lock = lambda: cache.delete(lock_key)

    waited, hops = 0, 10
    while not acquire_lock():
        time.sleep(float(hops) / 1000.0)
        waited += hops
        if waited > timeout:
            raise RuntimeError('Lock could not be acquired after {}ms'.format(waited))

    try:
        yield
    finally:
        release_lock()


if hasattr(cache, 'lock'):
    lock = lambda id: cache.lock(lock_key.format(id), expire=15)
else:
    lock = lambda id: simple_lock(lock_key.format(id))
