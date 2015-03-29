# coding: utf-8

__author__ = 'Junki Ishida'

from . import scripts
from .exceptions import IntegrityError, MissingError, TimeoutError

import time, uuid, math
from redis import StrictRedis


class LockBase(object):
    def __init__(self, redis=None, key='redis-2way-lock', timeout=30, expire=300,
                 retry_interval=0.01, init_on_error=False, **options):
        self.key = key
        self.redis = redis or StrictRedis()
        self.timeout = timeout
        self.expire = expire
        self.retry_interval = retry_interval
        self.init_on_error = init_on_error
        self.__is_active = False

    def acquire(self):
        if not isinstance(self.expire, int) or self.expire <= 0:
            raise ValueError()
        if not self.__is_active:
            self.__is_active = True
        else:
            raise IntegrityError()

    def release(self):
        if self.__is_active:
            self.__is_active = False
        else:
            raise IntegrityError()

    def __enter__(self):
        self.acquire()

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.release()

    @property
    def _init_on_error(self):
        return b'1' if self.init_on_error else b'0'


class ExclusiveLockBase(LockBase):
    pass


class SharedLockBase(LockBase):
    pass


class SimpleExclusiveLock(ExclusiveLockBase):
    def acquire(self):
        super(SimpleExclusiveLock, self).acquire()
        end = time.time() + self.timeout
        while end > time.time():
            if scripts.get_xlock_simple.execute(self.redis, self.key, self.expire) == 0:
                break
            time.sleep(self.retry_interval)
        else:
            raise TimeoutError()

    def release(self):
        super(SimpleExclusiveLock, self).release()
        if scripts.release_xlock_simple.execute(self.redis, self.key, self._init_on_error) == 1:
            raise MissingError()


class SimpleSharedLock(SharedLockBase):
    def acquire(self):
        super(SimpleSharedLock, self).acquire()
        end = time.time() + self.timeout
        while end > time.time():
            if scripts.get_slock_simple.execute(self.redis, self.key, self.expire) == 0:
                break
            time.sleep(self.retry_interval)
        else:
            raise TimeoutError()

    def release(self):
        super(SimpleSharedLock, self).release()
        if scripts.release_slock_simple.execute(self.redis, self.key, self._init_on_error) == 1:
            raise MissingError()


class IdentifiedExclusiveLock(ExclusiveLockBase):
    def acquire(self):
        super(IdentifiedExclusiveLock, self).acquire()
        end = time.time() + self.timeout
        self._euuid = b'e' + uuid.uuid4().__str__().encode()
        while end > time.time():
            if scripts.get_xlock_uuid.execute(self.redis, self.key, self._euuid, self.expire) == 0:
                break
            time.sleep(self.retry_interval)
        else:
            raise TimeoutError()

    def release(self):
        super(IdentifiedExclusiveLock, self).release()
        uuid = self._euuid
        self._euuid = None
        if scripts.release_xlock_uuid.execute(self.redis, self.key, self._init_on_error, uuid) == 1:
            raise MissingError()


class IdentifiedSharedLock(SharedLockBase):
    def acquire(self):
        super(IdentifiedSharedLock, self).acquire()
        end = time.time() + self.timeout
        self._suuid = b's' + uuid.uuid4().__str__().encode()
        while end > time.time():
            r = scripts.get_slock_uuid.execute(self.redis, self.key, self._suuid, self.expire)
            if r == 0:
                break
            elif r == 2:
                self._suuid = b's' + uuid.uuid4().__str__().encode()
            time.sleep(self.retry_interval)
        else:
            raise TimeoutError()

    def release(self):
        super(IdentifiedSharedLock, self).release()
        uuid = self._suuid
        self._suuid = None
        if scripts.release_slock_uuid.execute(self.redis, self.key, self._init_on_error, uuid) == 1:
            raise MissingError()


class SafeIdentifiedExclusiveLock(ExclusiveLockBase):
    def acquire(self):
        super(SafeIdentifiedExclusiveLock, self).acquire()
        self._uuid = uuid.uuid4().__str__().encode()
        redis_stdtime = self.redis.time()[0]
        stdtime = time.time()
        end = stdtime + self.timeout
        while True:
            now = time.time()
            if end < now:
                raise TimeoutError()
            redis_now = redis_stdtime + math.floor(now - stdtime)
            if scripts.get_xlock_safe_uuid.execute(self.redis, self.key, self._uuid, redis_now, self.expire) == 0:
                break
            time.sleep(self.retry_interval)

    def release(self):
        super(SafeIdentifiedExclusiveLock, self).release()
        uuid = self._uuid
        self._uuid = None
        if scripts.release_xlock_safe_uuid.execute(self.redis, self.key, self._init_on_error, uuid) == 1:
            raise MissingError()


class SafeIdentifiedSharedLock(SharedLockBase):
    def acquire(self):
        super(SafeIdentifiedSharedLock, self).acquire()
        self._uuid = uuid.uuid4().__str__().encode()
        redis_stdtime = self.redis.time()[0]
        stdtime = time.time()
        end = stdtime + self.timeout
        while True:
            now = time.time()
            if end < now:
                raise TimeoutError()
            redis_now = redis_stdtime + math.ceil(now - stdtime)
            r = scripts.get_slock_safe_uuid.execute(self.redis, self.key, self._uuid, redis_now, self.expire)
            if r == 0:
                break
            elif r == 2:
                self._uuid = uuid.uuid4().__str__().encode()
            time.sleep(self.retry_interval)

        else:
            raise TimeoutError()

    def release(self):
        super(SafeIdentifiedSharedLock, self).release()
        uuid = self._uuid
        self._uuid = None
        if scripts.release_slock_safe_uuid.execute(self.redis, self.key, self._init_on_error, uuid) == 1:
            raise MissingError()