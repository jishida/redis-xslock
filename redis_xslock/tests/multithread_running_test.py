__author__ = 'owner'

from redis import StrictRedis
import unittest, threading, time, redis_xslock


class LockTestCase(unittest.TestCase):
    def test_001_simple(self):
        self.do('simple')

    def test_002_uuid(self):
        self.do('uuid')

    def test_003_safe_uuid(self):
        self.do('safe_uuid')

    def do(self, mode):
        redis = StrictRedis()
        factory = redis_xslock.LockFactory(redis=redis, prefix='test:', mode=mode)
        redis.delete(factory.getkey())
        exclusive_lock = threading.Lock()
        shared_lock = threading.Lock()
        print_lock = threading.Lock()
        incr_lock = threading.Lock()
        exclusive_results = []
        shared_results = []
        self.processid = 0

        def exclusive_process(index):
            with factory.xlock():
                with incr_lock:
                    self.processid += 1
                    id = self.processid
                start = time.time()
                time.sleep(0.2)
                end = time.time()
                with exclusive_lock:
                    exclusive_results.append((start, end, id))
            with print_lock:
                print('{3}:exclusive[{0}] ({1}, {2})'.format(index, start, end, id))

        def shared_process(index):
            with factory.slock():
                with incr_lock:
                    self.processid += 1
                    id = self.processid
                start = time.time()
                time.sleep(0.1)
                end = time.time()
                with shared_lock:
                    shared_results.append((start, end, id))
            with print_lock:
                print('{3}:shared[{0}] ({1}, {2})'.format(index, start, end, id))

        def exclusive_loop(index):
            for i in range(25):
                exclusive_process(index)
                time.sleep(0.01)

        def shared_loop(index):
            for i in range(50):
                shared_process(index)
                time.sleep(0.05)

        def duplicate(result1, result2):
            return not (result1[1] <= result2[0] or result1[0] >= result2[1])


        exclusive_threads = range(2)
        shared_threads = range(4)
        threads = []

        print(mode)

        start = time.clock()
        for i in exclusive_threads:
            thread = threading.Thread(target=exclusive_loop, args=(i,))
            threads.append(thread)
            thread.start()

        for i in shared_threads:
            thread = threading.Thread(target=shared_loop, args=(i,))
            threads.append(thread)
            thread.start()

        for thread in threads:
            thread.join()

        end = time.clock()

        print('[exclusive results]')
        print(len(exclusive_results))
        print('[shared results]')
        print(len(shared_results))

        for exr in exclusive_results:
            for shr in shared_results:
                self.assertFalse(duplicate(exr, shr), "exclusive id:{0}, shared id{1}".format(exr[2], shr[2]))

        count = 0
        while len(shared_results) > 0:
            dup_list = []
            r1 = shared_results.pop(0)
            for r2 in shared_results:
                if duplicate(r1, r2):
                    dup_list.append(r2)
                    count += 1
            for dup in dup_list:
                shared_results.remove(dup)
        print('[shared duplicate count]')
        print(count)
        self.assertTrue(count > 1)
        print('[elapsed time]')
        print('{0}s'.format(end - start))