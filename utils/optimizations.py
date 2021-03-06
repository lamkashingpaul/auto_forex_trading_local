from billiard.pool import Pool
from celery_progress.backend import ProgressRecorder
from numbers import Number
from pathlib import Path
from tqdm.auto import tqdm

import backtrader as bt
import collections
import csv
import itertools
import math
import numbers
import pandas as pd
import pickle

PBAR = None


class Optimizer:
    def start(self):
        runstrat = self.cerebro.run(runonce=False, stdstats=False)
        self.strats = [x[0] for x in runstrat]  # flatten 2d list
        self.strats_df = self.build_strats_df()

    def update_progress_bar(self):
        return

    def build_strats_df(self):
        cols = tuple(self.strats[0].p._getkeys())
        for name_of_analyzer, analyzer in zip(self.strats[0].analyzers._names, self.strats[0].analyzers._items):
            if name_of_analyzer in ('tradeanalyzer', 'transactions'):
                continue

            else:
                rets_dict = analyzer.get_analysis()
                rets_dict = flatten_dict(rets_dict)
                for name_of_ret in rets_dict.keys():
                    cols += (f'{name_of_analyzer}_{name_of_ret}',)

        df = pd.DataFrame(columns=cols)
        self.pregress, self.total_testcase = 0, len(self.strats)

        for strat in self.strats:
            row = [value if isinstance(value, numbers.Number) else str(value) for value in strat.p._getvalues()]
            for name_of_analyzer, analyzer in zip(strat.analyzers._names, strat.analyzers._items):
                if name_of_analyzer in ('tradeanalyzer', 'transactions'):
                    continue

                else:
                    rets_dict = analyzer.get_analysis()
                    rets_dict = flatten_dict(rets_dict)
                    for ret in rets_dict.values():
                        row += [ret if isinstance(ret, Number) else str(ret)]

            df.loc[len(df)] = row

            self.update_progress_bar()

        return df

    def save_strats(self, output_path, chunk_size=512):
        filepath = Path(f'{output_path}.csv')
        filepath.parent.mkdir(parents=True, exist_ok=True)
        self.strats_df.to_csv(filepath)

        for i in range(math.ceil(len(self.strats) / chunk_size)):
            pickle.dump(self.strats[i * chunk_size: (i + 1) * chunk_size], open(f'{output_path}_{i * chunk_size}_{(i + 1) * chunk_size - 1}.pickle', 'wb'))


class OptimizerCLI(Optimizer):
    def __init__(self, cerebro, strategy, generator, **kwargs):
        self.cerebro = cerebro

        total_testcase = sum(1 for _ in generator(**kwargs))

        global PBAR
        PBAR = tqdm(smoothing=0.05, desc='Optimization', total=total_testcase)

        self.cerebro.optstrategy(strategy, optimization_dict=generator(**kwargs))
        self.cerebro.optcallback(cb=self.bt_opt_callback)

    def bt_opt_callback(self, cb):
        global PBAR
        PBAR.update()


class OptimizerCelery(Optimizer):
    def __init__(self, celery, cerebro, strategy, generator, **kwargs):
        self.cerebro = cerebro
        self.progress_recorder = ProgressRecorder(celery)
        self.pregress = 0
        self.total_testcase = sum(1 for _ in generator(**kwargs))

        self.cerebro.optstrategy(strategy, optimization_dict=generator(**kwargs))
        self.cerebro.optcallback(cb=self.bt_opt_callback)

    def update_progress_bar(self):
        self.pregress += 1
        self.progress_recorder.set_progress(self.pregress + 1, self.total_testcase)

    def bt_opt_callback(self, cb):
        self.pregress += 1
        self.progress_recorder.set_progress(self.pregress + 1, self.total_testcase)


def flatten_dict(d, parent_key='', sep='_'):
    items = []
    for k, v in d.items():
        new_key = parent_key + sep + k if parent_key else k
        if isinstance(v, collections.abc.MutableMapping):
            items.extend(flatten_dict(v, new_key, sep=sep).items())
        else:
            items.append((new_key, v))
    return dict(items)


class CeleryCerebro(bt.Cerebro):
    '''
    `billiard.pool.Pool` shall be used instead of multiprocessing.Pool,
    as the later one is not compatible with `celery`
    '''

    def run(self, **kwargs):
        self._event_stop = False  # Stop is requested

        if not self.datas:
            return []  # nothing can be run

        pkeys = self.params._getkeys()
        for key, val in kwargs.items():
            if key in pkeys:
                setattr(self.params, key, val)

        # Manage activate/deactivate object cache
        bt.linebuffer.LineActions.cleancache()  # clean cache
        bt.indicator.Indicator.cleancache()  # clean cache

        bt.linebuffer.LineActions.usecache(self.p.objcache)
        bt.indicator.Indicator.usecache(self.p.objcache)

        self._dorunonce = self.p.runonce
        self._dopreload = self.p.preload
        self._exactbars = int(self.p.exactbars)

        if self._exactbars:
            self._dorunonce = False  # something is saving memory, no runonce
            self._dopreload = self._dopreload and self._exactbars < 1

        self._doreplay = self._doreplay or any(x.replaying for x in self.datas)
        if self._doreplay:
            # preloading is not supported with replay. full timeframe bars
            # are constructed in realtime
            self._dopreload = False

        if self._dolive or self.p.live:
            # in this case both preload and runonce must be off
            self._dorunonce = False
            self._dopreload = False

        self.runwriters = list()

        # Add the system default writer if requested
        if self.p.writer is True:
            wr = bt.writer.WriterFile()
            self.runwriters.append(wr)

        # Instantiate any other writers
        for wrcls, wrargs, wrkwargs in self.writers:
            wr = wrcls(*wrargs, **wrkwargs)
            self.runwriters.append(wr)

        # Write down if any writer wants the full csv output
        self.writers_csv = any(map(lambda x: x.p.csv, self.runwriters))

        self.runstrats = list()

        if self.signals:  # allow processing of signals
            signalst, sargs, skwargs = self._signal_strat
            if signalst is None:
                # Try to see if the 1st regular strategy is a signal strategy
                try:
                    signalst, sargs, skwargs = self.strats.pop(0)
                except IndexError:
                    pass  # Nothing there
                else:
                    if not isinstance(signalst, bt.Strategy.SignalStrategy):
                        # no signal ... reinsert at the beginning
                        self.strats.insert(0, (signalst, sargs, skwargs))
                        signalst = None  # flag as not presetn

            if signalst is None:  # recheck
                # Still None, create a default one
                signalst, sargs, skwargs = bt.Strategy.SignalStrategy, tuple(), dict()

            # Add the signal strategy
            self.addstrategy(signalst,
                             _accumulate=self._signal_accumulate,
                             _concurrent=self._signal_concurrent,
                             signals=self.signals,
                             *sargs,
                             **skwargs)

        if not self.strats:  # Datas are present, add a strategy
            self.addstrategy(bt.Strategy)

        iterstrats = itertools.product(*self.strats)
        if not self._dooptimize or self.p.maxcpus == 1:
            # If no optimmization is wished ... or 1 core is to be used
            # let's skip process "spawning"
            for iterstrat in iterstrats:
                runstrat = self.runstrategies(iterstrat)
                self.runstrats.append(runstrat)
                if self._dooptimize:
                    for cb in self.optcbs:
                        cb(runstrat)  # callback receives finished strategy
        else:
            if self.p.optdatas and self._dopreload and self._dorunonce:
                for data in self.datas:
                    data.reset()
                    if self._exactbars < 1:  # datas can be full length
                        data.extend(size=self.params.lookahead)
                    data._start()
                    if self._dopreload:
                        data.preload()

            pool = Pool(self.p.maxcpus or None)
            for r in pool.imap(self, iterstrats):
                self.runstrats.append(r)
                for cb in self.optcbs:
                    cb(r)  # callback receives finished strategy

            pool.close()

            if self.p.optdatas and self._dopreload and self._dorunonce:
                for data in self.datas:
                    data.stop()

        if not self._dooptimize:
            # avoid a list of list for regular cases
            return self.runstrats[0]

        return self.runstrats
