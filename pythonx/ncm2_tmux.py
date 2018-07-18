# -*- coding: utf-8 -*-

import vim
from ncm2 import Ncm2Source, Popen, getLogger
import subprocess
import re

logger = getLogger(__name__)


class Source(Ncm2Source):

    def on_complete(self, ctx):
        pat = re.compile(ctx['word_pattern'])

        # get current session id

        proc = Popen(args=['tmux', 'display-message', '-p', '#{session_id}'],
                     stdin=subprocess.PIPE,
                     stdout=subprocess.PIPE,
                     stderr=subprocess.PIPE)
        outs, errs = proc.communicate(timeout=5)
        cur_session = outs.decode().strip()

        proc = Popen(args=['tmux', 'list-panes', '-a', '-F', '#{session_id} #{pane_id} #{pane_active} #{window_active}'],
                     stdin=subprocess.PIPE,
                     stdout=subprocess.PIPE,
                     stderr=subprocess.PIPE)
        outs, errs = proc.communicate(timeout=5)
        lines = outs.decode('utf-8')

        base = ctx['base']
        matcher = self.matcher_get(ctx['matcher'])
        matches = []
        seen = {}

        for line in lines.strip().split('\n'):
            session_id, pane_id, pactive, wactive = line.split(' ')
            pactive, wactive = int(pactive), int(wactive)

            if wactive and pactive and session_id == cur_session:
                # ignore current pane
                continue

            proc = Popen(args=['tmux', 'capture-pane', '-p', '-t', '{}'.format(pane_id)],
                         stdin=subprocess.PIPE,
                         stdout=subprocess.PIPE,
                         stderr=subprocess.PIPE)
            outs, errs = proc.communicate(timeout=5)
            try:
                outs = outs.decode('utf-8')

                for word in pat.finditer(outs):
                    w = word.group()
                    if w in seen:
                        m = seen[w]
                        ud = m['user_data']
                    else:
                        m = self.match_formalize(ctx, w)
                        ud = m['user_data']
                        ud['location'] = []
                        if not matcher(base, m):
                            continue
                        matches.append(m)
                    ud['location'].append(dict(pane_id=pane_id,
                                               start=word.start()))
            except Exception as ex:
                logger.exception(
                    'exception, failed to decode output, %s', ex)
                pass

        self.complete(ctx, ctx['startccol'], matches)


source = Source(vim)

on_complete = source.on_complete
