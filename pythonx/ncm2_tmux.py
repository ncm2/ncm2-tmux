# -*- coding: utf-8 -*-

import vim
from ncm2 import Ncm2Source, Popen, getLogger
import subprocess
import re

logger = getLogger(__name__)


class Source(Ncm2Source):

    def on_complete(self, ctx):
        pat = re.compile(ctx['word_pattern'])

        # tmux list-window -F '#{window_index}'
        # tmux capture-pane -p -t "$window_index.$pane_index"
        proc = Popen(args=['tmux', 'list-window', '-F', '#{window_index} #{window_active}'],
                     stdin=subprocess.PIPE,
                     stdout=subprocess.PIPE,
                     stderr=subprocess.PIPE)

        outs, errs = proc.communicate(timeout=5)
        windows = outs.decode('utf-8')
        logger.info('list-window: %s', windows)

        # parse windows
        panes = []
        for win in windows.strip().split('\n'):
            wid, wactive = win.split(' ')
            wactive = int(wactive)

            proc = Popen(args=['tmux', 'list-panes', '-t', wid, '-F', '#{pane_index} #{pane_active}'],
                         stdin=subprocess.PIPE,
                         stdout=subprocess.PIPE,
                         stderr=subprocess.PIPE)
            outs, errs = proc.communicate(timeout=5)
            pane_ids = outs.decode('utf-8')

            for pane in pane_ids.strip().split('\n'):
                pid, pactive = pane.split(' ')
                pactive = int(pactive)

                if wactive and pactive:
                    # ignore current pane
                    continue

                proc = Popen(args=['tmux', 'capture-pane', '-p', '-t', '{}.{}'.format(wid, pid)],
                             stdin=subprocess.PIPE,
                             stdout=subprocess.PIPE,
                             stderr=subprocess.PIPE)
                outs, errs = proc.communicate(timeout=5)
                try:
                    outs = outs.decode('utf-8')
                    panes.append(outs)
                except Exception as ex:
                    logger.exception(
                        'exception, failed to decode output, %s', ex)
                    pass

        b = ctx['base']
        matcher = self.matcher_get(ctx['matcher'])
        matches = []

        for pane in panes:
            for word in pat.finditer(pane):
                m = self.match_formalize(ctx, word.group())
                if matcher(b, m):
                    matches.append(m)

        self.complete(ctx, ctx['startccol'], matches)


source = Source(vim)

on_complete = source.on_complete
