from __future__ import print_function
import re
import random
import os
import mimetypes
import sys
import cStringIO
import cPickle
import argparse
import logging
import textwrap
from pprint import pprint

from sqlalchemy import create_engine
from textblob import TextBlob
import IPython
from pyquery import PyQuery

from blancmange.models import DBSession, Base, Episode, Person, Sketch, Keyword
from blancmange.creation import creation

from blancmange.config import log


def _print_heading(string):
    """ Learn how not to be seen by printing a heading.
    """
    print('')
    print(string)
    print('=' * len(string))
    print('')

def _database_parser():
    """ Prepare database parser. Refer to the gorilla librarian.
    """
    parser = argparse.ArgumentParser(
        formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument('-v', '--verbose',
                        action='store_true',
                        help='Enable verbose logging.')
    parser.add_argument('-c', '--create-tables',
                        action='store_true',
                        help='Create tables in given database.')
    parser.add_argument('database', default="sqlite:///:memory:", help='Database file to use')

    return parser

def configure(config):
    if config.verbose:
        logging.basicConfig(level=logging.DEBUG)

    # Database configuration
    database = 'sqlite:///%s' % config.database \
        if '://' not in config.database else config.database
    engine = create_engine(database)
    DBSession.configure(bind=engine)
    Base.metadata.bind = engine

    if config.create_tables:
        # Create tables & process data if not already existing
        Base.metadata.create_all()
        creation(DBSession)


def completely_different():
    """ Be completely different and return a line from Flying Circus.

    Lines are formatted in Python source comment style for easy
    inclusion in your code!
    """
    parser = _database_parser()
    parser.description = completely_different.__doc__
    parser.add_argument('-n', '--no-syntax',
                        action='store_true',
                        help='Disable output as Python comment syntax.')
    parser.add_argument('-w', '--width',
                        default=70,
                        type=int,
                        help='Control the output width of comments.')
    config = parser.parse_args()
    configure(config)

    lines = [sketch.lines for sketch in DBSession.query(Sketch).all() if sketch.lines]
    _print_heading('And now for something completely different.  It\'s...')
    line_text = PyQuery(random.choice(random.choice(lines))).text()

    if config.no_syntax:
        print(line_text)
    else:
        wrapper = textwrap.TextWrapper(width=config.width,
                                       initial_indent="# ",
                                       subsequent_indent="# ")
        print(*wrapper.wrap(line_text), sep='\r\n')


def flying_circus_stats():
    """ Get some statistics about llamas appearing in Flying Circus.
    """
    parser = _database_parser()
    config = parser.parse_args()
    configure(config)

    keywords = DBSession.query(Keyword).all()

    _print_heading('Totals')
    print('%i words spoken throughout Flying Circus.' % len(keywords))

    people = DBSession.query(Person).all()
    for person in people:
        print('{}: {} keywords, {:.1%} of total'.format(
            person.name,
            len(person.keywords),
            len(person.keywords) * 1.0 / len(keywords)))

    print('%i total sketches' % DBSession.query(Sketch).count())
    print('%i total lines' % \
        sum([len(sketch.lines) for sketch in DBSession.query(Sketch).all()]))
    print('%i total words in the script' % sum([len(episode.textblob.words)
        for episode in DBSession.query(Episode).all()]))

    completely_different()


def main():
    """ Analyse the target source code for Pythonesqusness.

    Noone ever expects this function to work perfectly, much like
    the fact that noone expects the Spanish Inquistiion.
    """
    parser = _database_parser()
    parser.add_argument('-i', '--interactive',
                        action='store_true',
                        help='Launch an interactive console after finishing.')
    parser.add_argument('-l', '--min-length',
                        default=4, type=int,
                        help='Control the minimum length of words to count.')
    parser.add_argument('-w', '--max-words',
                        default=None, type=int,
                        help='Control the number of words to count.')
    parser.add_argument('-s', '--spoken-only',
                        action='store_true',
                        help='Only process and count words spoken, not the whole TV script.')
    parser.add_argument('-p', '--count-pickle',
                        help='Location to store the count structure pickle for speed.')
    parser.add_argument('path',
                        nargs='+',
                        help='Paths or directories to scan for files to check.')
    config = parser.parse_args()
    configure(config)

    # XXX Reads the given source code.  Splitting up into individual file
    # processing would be better.
    source_files = [os.path.join(dirpath, filename)
        for path in config.path
        for dirpath, dirnames, filenames in os.walk(path)
        for filename in filenames
        if '/.' not in dirpath and str(mimetypes.guess_type(filename)[0]).startswith('text/')
        or 'readme' in filename.lower() or re.match('.*\.(txt|TXT|rst|py|c)$', filename)]
    all_source = cStringIO.StringIO()
    for _file in source_files:
        with open(_file, 'r') as opened:
            all_source.write(opened.read())
    all_source.seek(0)
    python_source = all_source.read().lower()
    log.debug('Read all source code specified')

    # Pull all episode data from the database
    episodes = DBSession.query(Episode).all()
    log.debug('Loaded episode data from the database')

    # Sum all words
    results = {}
    if config.count_pickle:
        if os.path.exists(config.count_pickle):
            with open(config.count_pickle, 'rb') as pickle:
                results = cPickle.load(pickle)
                log.debug('Loaded counts from pickle in %s' % config.count_pickle)

    if not results:
        # Calculate what factor we need to decrease our source-count by
        # to normalise with the Flying Circus scripts.
        normalisation = sum([len(episode.text) for episode in episodes]) / (len(python_source) * 1.0)
        for episode in episodes:
            if not config.spoken_only:
                counts = episode.textblob.word_counts
            else:
                counts = episode.textblob_spoken.word_counts

            for word, count in counts.iteritems():
                if len(word) >= config.min_length:
                    word = word.encode('utf8')
                    flying_circus_count = results[word]['flying_circus_count'] + count if word in results else count
                    source_count = python_source.count(word) # TextBlob possible?
                    results[word] = {
                        'source_count': source_count,
                        'flying_circus_count': flying_circus_count,
                        'score': (source_count * normalisation) + (flying_circus_count ** 2)
                    }
            log.debug('Finished processing for %r' % episode)
        log.debug('Summed counts for all words within Flying Circus')
        log.debug('Counted all words from Flying Circus inside source code.')

        if config.count_pickle:
            with open(config.count_pickle, 'wb') as pickle:
                cPickle.dump(results, pickle)
                log.debug('Dumped counts to pickle in %s.' % config.count_pickle)


    results_sorted = sorted(results.items(), key=lambda r: r[1]['score'], reverse=True)
    _print_heading('Words mentioned in source code:')
    pprint(results_sorted[:100])

    _print_heading('Words that need love:')
    pprint(results_sorted[-100:])

    _print_heading('Pythons mentioned in source code:')
    people = DBSession.query(Person).all()
    for person in people:
        counts = (results.get(person.first_name.lower()),
                  results.get(person.surname.lower()))
        count = sum(c['source_count'] for c in counts if c)
        print('%s mentioned %i times' % (person.name, count))

    if config.interactive:
        IPython.embed()

#XXX Analysis needs to strip out all the common words
# Should less-common mentions in Flying Circus be ranked higher?
# Larger text pool needs to be normalised for counts; smaller pool can be weighted with exponential

# Most common words in Flying Circus
# Most 

# Notes
# Natural language processing is hard.  How does one 'value' "spam" over "with"?
# Name searches are inherently flawed.  Idle gets a major head start!
# Restricted to words 4 characters and above. Spam/John are the starting point.
# Hand editing of data was required - some errors are present! Yikes! (episode13.html has duplicate IDs)
# Final credits are considered part of the final sketch.  This is inconsistent depending on episode.
# Some discrepency over the episode titles. Accepting first Wikipedia title for each episode as true. I don't have my DVD box set with me.  Feel free to come riff with me afterwards.
