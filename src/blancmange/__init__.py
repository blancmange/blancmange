from __future__ import print_function
import argparse
import copy
import cPickle
import cStringIO
import logging
import mimetypes
import os
import pprint
import random
import re
import sys
import textwrap
import webbrowser

from sqlalchemy import create_engine, and_
from textblob import TextBlob
import IPython
from pyquery import PyQuery
from pygments.lexers import PythonLexer
from nltk.corpus import brown
from nltk.probability import FreqDist

from blancmange.models import DBSession, Base, Episode, Person, Sketch, Keyword
from blancmange.creation import creation

from blancmange.config import log


tokens = PythonLexer.tokens['builtins'] + PythonLexer.tokens['keywords']
PATTERNS = [re.compile(token[0]) for token in tokens]


def match_syntax(word):
    """ Accepts a dict of word results and spots matches.

    Kind of like camerl spotting, really.  Except this function will
    spot camerls and not just a picture of one.
    """
    return any(pattern.match(word) for pattern in PATTERNS)


def _filter_words(results):
    """ Accepts a dict of word results and spots Python to remove it.

    Kind of like camerl spotting, really.  Except this function will
    spot camerls and not just a picture of one.
    """
    return {word: results[word] for word in results if not match_syntax(word)}



def _calculate_frequencies():
    """ Spot instances of words within a copus.

    Kind of like camerl spotting, really.  Except this function will
    spot camels and not just a picture of one.
    """
    words = FreqDist()
    for sentence in brown.sents():
        for word in sentence:
            words.inc(word.lower())
    return words


def _print_heading(string):
    """ Learn how not to be seen by printing a heading.
    """
    print('')
    print(string)
    print('=' * len(string))
    print('')


def _print_results(results_items, verbose=False):
    if verbose:
        pprint.pprint(results_items)
    else:
        print(*[result[0] for result in results_items], sep=", ")


def print_wordle(results_sorted):
    for word, result in results_sorted[:250]:
        print('%s:%i' % (word, result['score']))


def _database_parser():
    """ Prepare database parser. Refer to the gorilla librarian.
    """
    parser = argparse.ArgumentParser(
        formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument('-v', '--verbose',
                        action='store_true',
                        help='Enable verbose logging.')
    parser.add_argument('database',
                        nargs="?",
                        default="cheese-shop.db",
                        help='Database file to use')
    return parser


def calculate_score(word, frequencies, source_normalisation=1, python_weight=2, frequency_factor=1):
    """
    'score': (source_count * normalisation) + (flying_circus_count ** 2)
    """
    if word['source_count'] == 0:
        return 0
    source = word['source_count'] * source_normalisation
    flying_circus = word['flying_circus_count'] ** python_weight
    frequency = frequencies.get(word['word'], frequency_factor)
    return (source * flying_circus) / frequency

def recalculate_scores(results, frequencies, **kwargs):
    for word in results:
        results[word]['score'] = calculate_score(results[word], frequencies, **kwargs)

def sort_results(results):
    return sorted(results.items(), key=lambda r: r[1]['score'], reverse=True)

def configure_environment(config):
    if config.verbose:
        logging.basicConfig(level=logging.DEBUG)
    else:
        logging.basicConfig(level=logging.WARN)

    # Database configuration
    database = 'sqlite:///%s' % config.database \
        if '://' not in config.database else config.database
    engine = create_engine(database)
    DBSession.configure(bind=engine)
    Base.metadata.bind = engine


def create_database():
    """ Script for creating the underlying database.
    """
    parser = _database_parser()
    parser.description = completely_different.__doc__
    config = parser.parse_args()
    configure_environment(config)

    # Create tables & process data if not already existing
    Base.metadata.create_all()
    creation(DBSession)

    log.info('Created database at %s' % config.database)


def be_completely_different(syntax=True, width=70):
    lines = [sketch.lines for sketch in DBSession.query(Sketch).all() if sketch.lines]
    _print_heading('And now for something completely different.  It\'s...')
    line_text = PyQuery(random.choice(random.choice(lines))).text()

    if not syntax:
        print(line_text)
    else:
        wrapper = textwrap.TextWrapper(width=width,
                                       initial_indent="# ",
                                       subsequent_indent="# ")
        print(*wrapper.wrap(line_text), sep='\r\n')


# Scripts for enjoyment of your package.
# Please mind out for dirty forks & knives.

def completely_different():
    """ Be completely different and return a line from Flying Circus.

    Lines are formatted in Python source comment style for easy
    inclusion in your code!

    Script is completely-different.
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
    configure_environment(config)

    be_completely_different(syntax=not config.no_syntax, width=config.width)


def find_episode():
    """ Let's go camel spotting and find the episode that you want.

    Script is spot-camels.
    """
    parser = _database_parser()
    parser.description = completely_different.__doc__
    parser.add_argument('-w', '--web-browser',
                        action='store_true',
                        help='Open the first resulting episode in your web browser.')
    parser.add_argument('term',
                        type=unicode,
                        help='The search term or terms to go hunting for.')
    config = parser.parse_args()
    configure_environment(config)

    conditions = [Keyword.keyword == term.lower() for term in config.term.split()]
    results = DBSession.query(Episode, Sketch).join(Sketch, Keyword).filter(and_(*conditions)).all()
    for episode, sketch in results:
        print('%s in %r' % (sketch.name, episode))

    if not results:
        log.error("I'm sorry, I'm not allowed to argue any more.")
    else:
        if config.web_browser:
            episode = results[0][0]
            url = 'file://' + episode.path
            webbrowser.open(url)

    #episodes = DBSession.query(Episode).join(Sketch, Keyword).filter(and_(*conditions)).all()


def flying_circus_stats():
    """ Get some statistics about llamas appearing in Flying Circus.

    Script is flying-circus.
    """
    parser = _database_parser()
    config = parser.parse_args()
    configure_environment(config)

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
        sum(len(sketch.lines) for sketch in DBSession.query(Sketch).all()))
    print('%i total words in the script' % sum(len(episode.textblob.words)
        for episode in DBSession.query(Episode).all()))

    be_completely_different(syntax=False)


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
                        default='cheese-shop-cheddar.pickle',
                        help='Location to store the count structure pickle for speed.')
    parser.add_argument('path',
                        nargs='+',
                        help='Paths or directories to scan for files to check.')
    config = parser.parse_args()
    configure_environment(config)

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
    frequencies = None
    if config.count_pickle:
        if os.path.exists(config.count_pickle):
            with open(config.count_pickle, 'rb') as pickle:
                data = cPickle.load(pickle)
                results = data['counts'] # Analysis results for current target code
                frequencies = data['frequencies'] # Brown copus analysis for words
                log.debug('Loaded counts from pickle in %s' % config.count_pickle)

    if not frequencies:
        frequencies = _calculate_frequencies()

    if not results:
        normalisation = sum(len(episode.text) for episode in episodes) / (len(python_source) * 1.0)

        # Calculate what factor we need to decrease our source-count by
        # to normalise with the Flying Circus scripts.
        for episode in episodes:
            if not config.spoken_only:
                counts = episode.textblob.word_counts
            else:
                counts = episode.textblob_spoken.word_counts

            for word, count in counts.iteritems():
                if len(word) >= config.min_length:
                    word = word.encode('utf8')
                    flying_circus_count = results[word]['flying_circus_count'] + count if word in results else count
                    # XXX A serious CPU sucker. Needs to be improved.
                    source_count = python_source.count(word) # TextBlob possible?

                    results[word] = {'word': word,
                                     'source_count': source_count,
                                     'flying_circus_count': flying_circus_count,
                                     'score': 0}
                    results[word]['score'] = calculate_score(results[word], frequencies, normalisation, 2, 0.3)
            log.debug('Finished processing for %r' % episode)
        log.debug('Summed counts for all words within Flying Circus')
        log.debug('Counted all words from Flying Circus inside source code.')

        # Strip Python syntax
        #results = 


        if config.count_pickle:
            with open(config.count_pickle, 'wb') as pickle:
                data = {'counts': results, 'frequencies': frequencies}
                cPickle.dump(data, pickle)
                log.debug('Dumped counts to pickle in %s.' % config.count_pickle)


    results_sorted = sort_results(results)
    _print_heading('Words mentioned in source code:')
    portion = results_sorted[:100]
    _print_results(portion, config.verbose)

    _print_heading('Words that need love:')
    portion = results_sorted[-100:]
    _print_results(portion, config.verbose)

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

