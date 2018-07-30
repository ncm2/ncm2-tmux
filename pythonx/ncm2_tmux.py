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

        for line in lines.split('\n'):
            if line == '':
                continue

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
                        ud['word'] = w
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

    def on_completed(self, ctx, completed):
        ud = completed['user_data']
        word = ud['word']
        location = ud['location']

        if ctx['dated']:
            logger.debug('ctx is dated')
            return

        pat = re.compile(ctx['word_pattern'])

        matches = []
        seen = {}

        panes = {}

        for loc in location:
            pane_id = loc['pane_id']
            if pane_id in panes:
                outs = panes[pane_id]
            else:
                proc = Popen(args=['tmux', 'capture-pane', '-p', '-t', '{}'.format(pane_id)],
                             stdin=subprocess.PIPE,
                             stdout=subprocess.PIPE,
                             stderr=subprocess.PIPE)
                outs, errs = proc.communicate(timeout=5)
                try:
                    outs = outs.decode('utf-8')
                    panes[pane_id] = outs
                except:
                    logger.exception(
                        'exception, failed to decode output, %s', ex)
                    continue

            start = loc['start']
            cur_word_end = start + len(word)
            cur_word = outs[start: cur_word_end]
            if word != cur_word.replace('\n', ' '):
                logger.debug('word [%s] != cur word [%s]',
                             word,
                             cur_word)
                continue

            searchstr = outs[cur_word_end:]
            mat = pat.search(searchstr)
            if mat is None:
                if not len(searchstr):
                    return
                w = searchstr
            else:
                w = searchstr[: mat.end()]

            w = w.replace('\n', ' ')
            if w in seen:
                m = seen[w]
                ud = m['user_data']
            else:
                m = self.match_formalize(ctx, w)
                ud = m['user_data']
                ud['word'] = w
                ud['location'] = []
                matches.append(m)
            ud['location'].append(dict(pane_id=pane_id,
                                       start=cur_word_end))

        self.complete(ctx, ctx['ccol'], matches)


source = Source(vim)

on_complete = source.on_complete
on_completed = source.on_completed
