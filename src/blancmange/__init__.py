import os
import mimetypes
import sys
import cStringIO
import argparse
import logging

from sqlalchemy import create_engine
from blancmange.models import DBSession, Base, Episode, Person, Sketch, Keyword
from blancmange.creation import creation

logging.basicConfig(level=logging.DEBUG)
from blancmange.config import log


def _database_parser():
    parser = argparse.ArgumentParser(
        formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument('-c', '--create-tables',
                        action='store_true',
                        help='Create tables in given database.')
    parser.add_argument('database', default="sqlite:///:memory:", help='Database file to use')
    return parser


def _config_database(config):
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


def flying_circus_stats():
    parser = _database_parser()
    config = parser.parse_args()
    _config_database(config)


    keywords = DBSession.query(Keyword).all()
    print ('%i words said in total.' % len(keywords))

    people = DBSession.query(Person).all()
    for person in people:
        print('{}: {} keywords, {:.1%} of total'.format(person.name, len(person.keywords), len(person.keywords)*1.0/len(keywords)))


def main():
    parser = _database_parser()
    parser.add_argument('path', help='Path or directory to scan for files to check.')
    config = parser.parse_args()
    _config_database(config)

    if config.read_code:
        # XXX Blindly reads the given source code.  Splitting up into documentation would help.
        source_files = [os.path.join(dirpath, filename) for dirpath, dirnames, filenames in os.walk(config.path) for filename in filenames if '/.' not in dirpath and str(mimetypes.guess_type(filename)[0]).startswith('text/')]
        all_source = cStringIO.StringIO()
        for f in source_files:
            with open(f, 'r') as opened:
                all_source.write(opened.read())
        all_source.seek(0)
        python_source = all_source.read().lower()


    episodes = DBSession.query(Episode).all()

    word_totals = {}
    for episode in episodes:
        counts = episode.textblob.word_counts
        for word, count in counts.iteritems():
            if len(word) >= 4:
                word_totals[word] = word_totals[word] + count if word in word_totals else count
    word_results = sorted(word_totals.items(), key=lambda w: w[1], reverse=True)

    results = []
    for word, flying_circus_count in word_results[:1000]:
        source_count = python_source.count(word.encode('utf8'))
        results.append((word, source_count, source_count * flying_circus_count^10))

    results_sorted = sorted(results, key=lambda r: r[2], reverse=True)
    import ipdb; ipdb.set_trace()

    print('Word\t\tCount\t\tScore')
    print('====\t\t=====\t\t=====')
    for result in results_sorted:
        print('%s\t\t%i\t\t%i' % result)


#XXX Analysis needs to strip out all the common words

# Notes
# Restricted to words 4 characters and above. Spam/John are the starting point.
# Hand editing of data was required - some errors are present! Yikes! (episode13.html has duplicate IDs)
# Final credits are considered part of the final sketch.  This is inconsistent depending on episode.
# Some discrepency over the episode titles. Accepting first Wikipedia title for each episode as true. I don't have my DVD box set with me.  Feel free to come riff with me afterwards.
