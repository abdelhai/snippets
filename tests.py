import unittest

from event_loop import TimerManager


class TestingTimeFunction(object):
    """
    An instance can be used as a dummy time function for tests.
    Tests can then set the "time" independently of real time.
    """
    def __init__(self):
        self.time = 0
    
    def __call__(self):
        # Absolute value should not matter
        return self.time + 42


class MockCallback(object):
    """
    A callback object that tells you how many times it was called.
    """
    def __init__(self):
        self.nb_calls = 0
    
    def __call__(self):
        self.nb_calls += 1


class TestTimerManager(unittest.TestCase):

    def test_empty_timer_list(self):
        manager = TimerManager()
        self.assertRaises(ValueError, manager.sleep_time)
    
    def test_invalid_timeouts(self):
        manager = TimerManager()
        self.assertRaises(AssertionError, manager.add_timer, 0, None)
        self.assertRaises(AssertionError, manager.add_timer, -1, None)
    
    def test_single_timer(self):
        time = TestingTimeFunction()
        manager = TimerManager(_time_function=time)
        callback = MockCallback()
        manager.add_timer(30, callback)
        
        assert manager.sleep_time() == 30
        assert callback.nb_calls == 0
        
        manager.run()
        assert callback.nb_calls == 0

        time.time = 22
        assert manager.sleep_time() == 8

        manager.run()
        assert callback.nb_calls == 0

        time.time = 30
        assert manager.sleep_time() == 0

        manager.run()
        assert callback.nb_calls == 1
        # Timer was removed from the list
        self.assertRaises(ValueError, manager.sleep_time)

        time.time = 100
        manager.run()
        # not called a second time
        assert callback.nb_calls == 1

    def test_single_repeating_timer(self):
        time = TestingTimeFunction()
        manager = TimerManager(_time_function=time)
        callback = MockCallback()
        manager.add_timer(30, callback, repeat=True)
        
        assert manager.sleep_time() == 30
        assert callback.nb_calls == 0
        
        manager.run()
        assert callback.nb_calls == 0

        time.time = 22
        assert manager.sleep_time() == 8

        manager.run()
        assert callback.nb_calls == 0

        time.time = 30
        assert manager.sleep_time() == 0

        manager.run()
        assert callback.nb_calls == 1
        # Timer was NOT removed from the list
        assert manager.sleep_time() == 30

        time.time = 71
        assert manager.sleep_time() == 0
        manager.run()
        assert callback.nb_calls == 2
        assert manager.sleep_time() == 19

        # "Wait" more than one interval
        time.time = 200
        assert manager.sleep_time() == 0
        manager.run()
        # Only called once more
        assert callback.nb_calls == 3
        # Next is at t = 21
        assert manager.sleep_time() == 10


    def test_long_callback(self):
        time = TestingTimeFunction()
        manager = TimerManager(_time_function=time)
        
        def loose_time():
            time.time += 11
            
        manager.add_timer(2, loose_time, repeat=True)

        manager.run()        
        assert time.time == 0

        time.time = 2
        manager.run()
        assert time.time == 13
        # t = 4, 6, 8, 12 were skipped, next is t = 14
        assert manager.sleep_time() == 1
    
    def test_many(self):
        time = TestingTimeFunction()
        manager = TimerManager(_time_function=time)

        c5 = MockCallback()
        manager.add_timer(5, c5, repeat=True)
        c7 = MockCallback()
        manager.add_timer(7, c7, repeat=True)
        c13 = MockCallback()
        manager.add_timer(13, c13, repeat=True)
        
        while 1:
            time.time += manager.sleep_time()
            if time.time >= 100:
                break
            manager.run()
        
        assert c5.nb_calls == 19
        assert c7.nb_calls == 14
        assert c13.nb_calls == 7

    def test_many_contsant_sleep(self):
        time = TestingTimeFunction()
        manager = TimerManager(_time_function=time)

        c5 = MockCallback()
        manager.add_timer(5, c5, repeat=True)
        c7 = MockCallback()
        manager.add_timer(7, c7, repeat=True)
        c13 = MockCallback()
        manager.add_timer(13, c13, repeat=True)
        
        
        for time.time in xrange(100):
            # manager.sleep_time() is optimal, but calling run() more often
            # also works. (Here every "second")
            manager.run()
            
            if time.time == 42:
                def check_time():
                    assert time.time == 48
                one_shot = MockCallback()
                manager.add_timer(6, check_time)
                manager.add_timer(6, one_shot)
        
        assert c5.nb_calls == 19
        assert c7.nb_calls == 14
        assert c13.nb_calls == 7
        assert one_shot.nb_calls == 1


if __name__ == '__main__':
    unittest.main()