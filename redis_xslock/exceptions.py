# coding: utf-8

__author__ = 'Junki Ishida'


class IntegrityError(Exception):
    def __init__(self, *args, **kwargs):
        super(IntegrityError, self).__init__(*args, **kwargs)


class MissingError(IntegrityError):
    pass


class TimeoutError(Exception):
    pass