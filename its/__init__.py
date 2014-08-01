import sys
import argparse
import logging

from sqlalchemy import create_engine
from its.models import DBSession, Base
from its.creation import creation

logging.basicConfig(level=logging.DEBUG)
from its.config import log


def main():
    parser = argparse.ArgumentParser(
        formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument('-c', '--create-tables',
                        action='store_true',
                        help='Create tables in given database.')
    parser.add_argument('database', default="sqlite:///:memory:", help='Database file to use')
    config = parser.parse_args()

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

    from its.models import Episode, Person, Sketch, Keyword
    episodes = DBSession.query(Episode).all()

    people = DBSession.query(Person).all()
    for person in people:
        print('%s: %i keywords' % (person.name, len(person.keywords)))

    import ipdb; ipdb.set_trace()

#XXX Analysis needs to strip out all the common words

# Notes
# Hand editing of data was required - some errors are present! Yikes! (episode13.html has duplicate IDs)
# Final credits are considered part of the final sketch.  This is inconsistent depending on episode.
# Some discrepency over the episode titles. Accepting first Wikipedia title for each episode as true. I don't have my DVD box set with me.  Feel free to come riff with me afterwards.
