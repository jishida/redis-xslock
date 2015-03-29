# coding: utf-8

__author__ = 'Junki Ishida'

from .locks import ExclusiveLockBase, SharedLockBase

from redis import StrictRedis


__lock_class_dict = {}


def register_lock_classes(mode, xlock_class, slock_class):
    if issubclass(xlock_class, ExclusiveLockBase) and \
            issubclass(slock_class, SharedLockBase) and \
                    xlock_class is not ExclusiveLockBase and \
                    slock_class is not SharedLockBase:
        __lock_class_dict[mode] = (xlock_class, slock_class,)
    else:
        raise ValueError()


def exclusive_lock(redis=None, key='redis-2way-lock', timeout=30, expire=300,
                   retry_interval=0.01, init_on_error=False, mode='safe_uuid', **options):
    return __lock_class_dict[mode][0](redis, key, timeout, expire, retry_interval, init_on_error, **options)


def shared_lock(redis=None, key='redis-2way-lock', timeout=30, expire=300,
                retry_interval=0.01, init_on_error=False, mode='safe_uuid', **options):
    return __lock_class_dict[mode][1](redis, key, timeout, expire, retry_interval, init_on_error, **options)


class LockFactory:
    def __init__(self, redis=None, prefix=None, suffix=None, mode='safe_uuid',
                 default_key=None, default_timeout=None, default_expire=None,
                 default_retry_interval=None, default_init_on_error=None, **default_options):
        self.redis = redis or StrictRedis()
        self.prefix = prefix
        self.suffix = suffix
        self.mode = mode
        self.default_key = default_key
        self.default_timeout = default_timeout
        self.default_expire = default_expire
        self.default_retry_interval = default_retry_interval
        self.default_init_on_error = default_init_on_error
        self.default_options = default_options.copy()

    def getkey(self, key=None):
        key = key or self.default_key or 'redis-2way-lock'
        return '{0}{1}{2}'.format(self.prefix or '', key, self.suffix or '')

    def exclusive_lock(self, key=None, timeout=None, expire=None,
                  retry_interval=None, init_on_error=None, **options):
        opts = self.default_options.copy()
        opts.update(options)
        return exclusive_lock(
            self.redis,
            self.getkey(key),
            timeout or self.default_timeout or 30,
            expire or self.default_expire or 300,
            retry_interval or self.default_retry_interval or 0.01,
            self.default_init_on_error if init_on_error is None else init_on_error,
            self.mode,
            **opts
        )

    def shared_lock(self, key=None, timeout=None, expire=None,
               retry_interval=None, init_on_error=None, **options):
        opts = self.default_options.copy()
        opts.update(options)
        return shared_lock(
            self.redis,
            self.getkey(key),
            timeout or self.default_timeout or 30,
            expire or self.default_expire or 300,
            retry_interval or self.default_retry_interval or 0.01,
            self.default_init_on_error if init_on_error is None else init_on_error,
            self.mode,
            **opts
        )

    xlock = exclusive_lock
    slock = shared_lock