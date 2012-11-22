#!/usr/bin/env python3

import sys, tty, termios
import csv
import sqlite3
from collections import namedtuple, OrderedDict

VOCABLE_FIELDS = ['front', 'back', 'score_fb', 'score_bf']
DELIM = '\t'

SCORE_MIN = 1
SCORE_MAX = 10
SCORE_INIT = SCORE_MAX

CTRL_C = chr(3)
CTRL_D = chr(4)
CHARS_QUIT = CTRL_C + CTRL_D + 'q'
CHARS_REVERSE = 'r'


class Score(object):
    def __init__(self, inc, keys):
        self.increment = inc
        self.keys = keys

SCORES = OrderedDict((
    ('easy',        Score(-1, 'ah')),
    ('moderate',    Score(+0, 'sj')),
    ('hard',        Score(+1, 'dk')),
    ('wrong',       Score(+3, 'fl')),
))

SCORES_WIDTH = max(len(k) for k in SCORES.keys())

def getch():
    fd = sys.stdin.fileno()
    old_settings = termios.tcgetattr(fd)
    try:
        tty.setraw(sys.stdin.fileno())
        ch = sys.stdin.read(1)
    finally:
        termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)
    return str(ch)

def clear_screen():
    import os
    os.system('clear')

def print_vocab(q, score, avg, reverse, a=None):
    print()
    print('Question:\t\t(score: {}, average: {}, reverse: {})'.format(
        score, avg, 'ON' if reverse else 'OFF'))
    print()
    print('\t{}'.format(q))

    if a:
        print()
        print('Answer:')
        print()
        print('\t{}'.format(a))
        
    print()

def print_keys(reverse):
    for k, v in SCORES.items():
        print('{}:\t{} ({:+})'.format(
            '/'.join(v.keys),
            k.ljust(SCORES_WIDTH),
            v.increment))
    print('{}:\treverse {}'.format('/'.join(CHARS_REVERSE),
                                    'OFF' if reverse else 'ON')
        )
    print('q:\tquit')

def practice(vocabs, reverse=False):
    ch = 'asdfasdf'

    while ch not in CHARS_QUIT:
        if not reverse:
            keys = ('front', 'back', 'score_fb')
        else:
            keys = ('back', 'front', 'score_bf')

        vocab = pick_vocab(vocabs, reverse)
        q, a, score = (vocab[key] for key in keys)
        score = int(score)
        avg = sum(int(v[keys[2]]) for v in vocabs) / len(vocabs)

        clear_screen()
        print_vocab(q, score, avg, reverse)
        print('any:\tshow answer' )
        print('q:\tquit')
        if getch() in CHARS_QUIT:
            break

        clear_screen()
        print_vocab(q, score, avg, reverse, a)
        print_keys(reverse)

        ch = getch()
        while ch in CHARS_REVERSE:
            reverse = not reverse
            clear_screen()
            print_vocab(q, score, avg, a)
            print_keys(reverse)
            ch = getch()

        for x in SCORES.values():
            if ch in x.keys:
                score += x.increment

        vocab[keys[2]] = str(max(SCORE_MIN, min(SCORE_MAX, score)))
            


def pick_vocab(vlist, reverse=False):
    from random import choice
    attr = 'score_bf' if reverse else 'score_fb'
    weighted = [ (x, x[attr]) for x in vlist ]
    population = [ val for val, count in weighted for i in range(int(count)) ]
    return choice(population)

def load_vocabs(csvfile):
    vocabs = []
    fronts = set()
    reader = csv.DictReader(csvfile,
        fieldnames = VOCABLE_FIELDS,
        restval = SCORE_INIT,
        delimiter= DELIM)

    for row in reader:
        f = row['front']
        if f not in fronts:
            vocabs.append(row)
            fronts.add(f)
        else:
            print('ignoring duplicate entry for "{}"'.format(f), file=sys.stderr)

    return vocabs
    

def save_vocabs(csvfile, vocabs):
    writer = csv.DictWriter(csvfile,
        fieldnames = VOCABLE_FIELDS,
        delimiter = DELIM)
    writer.writerows(vocabs)

    

if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(description='simple vocabulary trainer')

    parser.add_argument('-r', '--reverse',
                        action = 'store_true',
                        help = 'ask back-to-front'
                        )

    parser.add_argument('file', nargs='?',
                        type=str, default=None)
    parser.add_argument('outfile', nargs='?',
                        type=str, default=None)

    args = vars(parser.parse_args())
    print(args)
    if not args['file']:
        v = load_vocabs(sys.stdin)
        practice(v)
        save_vocabs(sys.stdout, v)
    else:
        with open(args['file'], newline='') as f:
            v = load_vocabs(f)

        practice(v)

        if not args['outfile']:
            args['outfile'] = args['file']

        with open(args['outfile'], mode='w', newline='') as f:
            save_vocabs(f, v)
