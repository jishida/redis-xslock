# redis-xslock

## Usage

```python
from redis import StrictRedis
from redis_xslock import LockFactory

redis_args = {
    # server parameters
}

client = StrictRedis(**redis_args)
lock_factory = LockFactory(client)

with lock_factory.xlock('keyword-of-the-lock'):
    """
    exclusive scope
    """

with lock_factory.slock('keyword-of-the-lock'):
	"""
    shared scope
    """
```