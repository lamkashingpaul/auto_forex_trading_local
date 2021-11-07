from datetime import datetime, timedelta
import itertools
import random


def slides_generator(datetime_from, datetime_before, durations, steps, **kwargs):
    input_datetime_from, input_datetime_before = datetime_from, datetime_before

    for duration in durations:
        for step in steps:
            datetime_from, datetime_before = input_datetime_from, input_datetime_before
            while datetime_from < datetime_before:
                delta = datetime_before - datetime_from
                if duration > delta:
                    yield dict(datetime_from=datetime_from,
                               datetime_before=datetime_before,
                               **kwargs,)
                    break

                else:
                    yield dict(datetime_from=datetime_from,
                               datetime_before=datetime_from + duration,
                               **kwargs,)

                    datetime_from += step


def sma_testcase_generator(max_period, n=0):
    max_period += 1

    if n == 0:
        testcases = itertools.product(range(1, max_period), range(1, max_period), (0.0001, 0.0005, 0.0010))
        for fast_ma_period, slow_ma_period, strength in testcases:
            if fast_ma_period != slow_ma_period:
                for use_strength in (True, False):
                    yield dict(use_strength=use_strength,
                               strength=strength,
                               fast_ma_period=fast_ma_period,
                               slow_ma_period=slow_ma_period,
                               )
    else:
        for _ in range(n):
            fast_ma_period, slow_ma_period = random.sample(range(1, max_period), 2)
            for use_strength in (True, False):
                for strength in (0.0001, 0.0005, 0.0010):
                    yield dict(use_strength=use_strength,
                               strength=strength,
                               fast_ma_period=fast_ma_period,
                               slow_ma_period=slow_ma_period,
                               )


def rsi_testcase_generator(max_period, n=0, upper_unwind=30.0, lower_unwind=70.0):
    max_period += 1

    if n == 0:
        for period in range(1, max_period):
            yield dict(use_strength=True,
                       period=period,
                       upper_unwind=upper_unwind,
                       lower_unwind=lower_unwind,
                       )

    else:
        for _ in range(n):
            period = random.randint(1, max_period)
            yield dict(use_strength=True,
                       period=period,
                       upper_unwind=upper_unwind,
                       lower_unwind=lower_unwind,
                       )


if __name__ == '__main__':
    for i, slide in enumerate(slides_generator(datetime(2016, 1, 1),
                                               datetime(2021, 1, 1),
                                               [timedelta(days=30 * (i + 1)) for i in range(3)],
                                               [timedelta(days=1)],
                                               )):
        print(i, slide)
