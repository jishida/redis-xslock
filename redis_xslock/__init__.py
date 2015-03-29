# coding: utf-8

__author__ = 'Junki Ishida'

from .utils import register_lock_classes, exclusive_lock, shared_lock, LockFactory
from .exceptions import IntegrityError, MissingError, TimeoutError
from .locks import (
    SimpleExclusiveLock,
    SimpleSharedLock,
    IdentifiedExclusiveLock,
    IdentifiedSharedLock,
    SafeIdentifiedExclusiveLock,
    SafeIdentifiedSharedLock,
)

register_lock_classes('simple', SimpleExclusiveLock, SimpleSharedLock)
register_lock_classes('uuid', IdentifiedExclusiveLock, IdentifiedSharedLock)
register_lock_classes('safe_uuid', SafeIdentifiedExclusiveLock, SafeIdentifiedSharedLock)
