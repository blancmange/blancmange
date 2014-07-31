# -*- coding: utf-8 -*-
from __future__ import unicode_literals
import glob
import logging

from sqlalchemy import Column, Integer, Unicode, ForeignKey, create_engine
from sqlalchemy.orm import relationship, backref, scoped_session, sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from zope.sqlalchemy import ZopeTransactionExtension
import transaction

import re
from pyquery import PyQuery
from textblob import TextBlob

Base = declarative_base()
DBSession = scoped_session(sessionmaker(extension=ZopeTransactionExtension()))

log = logging.getLogger('okay-lumberjack')

with open('episodes.html', 'rb') as episodes_file:
    episode_html = episodes_file.read()
    episode_rows = PyQuery(episode_html)('#listtable tr')
    episode_text_rows = [[PyQuery(element).text() \
        for element in PyQuery(row).children()] for row in episode_rows]
    # Remove all rows not related to a standard episode
    episodes_clean = [(row[0], row[1]) for row in episode_text_rows \
        if 'x' in row[0]]
    # Construct our dictionary of episodes
    EPISODES = dict(enumerate(episodes_clean, 1))

# Counts can be completed with SQL queries
class TextContainer(Base):
    __abstract__ = True

    #: Raw content can be processed for any script/unspoken words
    raw = Column(Unicode, nullable=False)

    @property
    def textblob(self):
        return TextBlob(self.text)

    @property
    def text(self):
        return PyQuery(self.raw).text()


class Person(Base):
    """ People need to be locatable using their id in the documents.
    """
    __tablename__ = 'people'
    id = Column(Unicode, primary_key=True)
    name = Column(Unicode)

    def __repr__(self):
        return '<Person %s>' % (self.name)

class Keyword(TextContainer):
    __tablename__ = 'keywords'
    keyword = Column(Unicode, primary_key=True)
    person_id = Column(Unicode, ForeignKey('people.id'))
    person = relationship('Person', backref='keywords')
    sketch_name = Column(Unicode, ForeignKey('sketches.name'))

    def __init__(self, keyword, person):
        self.keyword = keyword
        if isinstance(person, basestring):
            person_obj = DBSession.query(Person).filter_by(Person.id == person).one()
            if not person_obj:
                log.error('Person not found - is %s a typo?' % person)
        else:
            person_obj = person
        self.person = person_obj

    def __str__(self):
        return self.keyword

class Sketch(TextContainer):
    __tablename__ = 'sketches'
    id = Column(Unicode, primary_key=True)
    episode_number = Column(Integer,
                            ForeignKey('episodes.number'),
                            primary_key=True)
    name = Column(Unicode, nullable=False)
    keywords = relationship('Keyword',
                            backref=backref('sketch', uselist=False))

    def __repr__(self):
        return '<Sketch "%s" in "%s">' % \
            (self.name, self.episode.name if self.episode else self.episode)

class Episode(TextContainer):
    __tablename__ = 'episodes'
    number = Column(Integer, primary_key=True)
    name = Column(Unicode, nullable=False)
    sketches = relationship('Sketch',
                            backref='episode')

    @property
    def season(self):
        return int(EPISODES[self.number][0][0])

    def __repr__(self):
        #XXX Causes a unicode expception due to self.name
        #return '<Episode %i: "%s">' % (self.number, self.name)
        return '<Episode %i>' % self.number



# Database configuration
engine = create_engine('sqlite:///:memory:')
DBSession.configure(bind=engine)
Base.metadata.bind = engine
Base.metadata.create_all()

# Process the files
episode_paths = glob.glob('./www.ibras.dk/montypython/episode*')

word_totals = {}

for path in episode_paths:
    with open(path, 'rb') as content:
        episode_content = content.read()
        document = PyQuery(episode_content)
        #import IPython; IPython.embed()

        episode_number = int(re.search('\d+', document('title').text()).group())
        # Some titles aren't split or have no specific name
        # XXX Source document is wrong
        # h1_parts = document('h1').text().split(': ')
        # name = h1_parts[1] if len(h1_parts) == 2 else h1_parts[0]
        episode_name = EPISODES[episode_number][1]

        # Strip out just the section of the DOM from one anchor to next
        sketches_wrapper = document('body > table')

        # Create the episode object
        episode = Episode(number=episode_number,
                          name=episode_name,
                          raw=sketches_wrapper.html())

        # Process sketch links so we know which sketches are in a document.
        sketch_lookup = {}
        for sketch_link in document('a[href*="#"]'):
            internal_id = re.search('#(.*?)$', sketch_link.attrib['href']).groups()[0]
            sketch_lookup[internal_id] = Sketch(id=internal_id,
                                                name=sketch_link.text)

        # Process the rest of the HTML in the document to find sketch details
        sketches_html = sketches_wrapper.html().split('<a name="')
        for sketch_html in sketches_html:

            # Check first characters to determine sketch
            first = sketch_html[:sketch_html.find('"')]
            if not first.isnumeric():
                # No sketch, add to general episode keywords
                sketch = Sketch(id=0, name='Introduction')
            else:
                # Crazy assumption: final credits are part of final skit.
                # We can't know better. The Pythons don't, either.
                sketch = sketch_lookup.get(first)
                if not sketch:
                    log.error('Found a sketch %s in Episode %i that does not exist' % (first, episode_number))
                    continue

            # Can be processed for any general words or terms later
            sketch.raw = sketch_html

            # XXX Process keywords, determining who said what.  Probably use <font> here.
            # Anything not in a font-tag is considered unspoken?
            sketch.keywords = []

            episode.sketches.append(sketch)

        DBSession.add(episode)

transaction.commit()

episodes = DBSession.query(Episode).all()
import ipdb; ipdb.set_trace()

# Notes
# Hand editing of data was required - some errors are present! Yikes! (episode13.html has duplicate IDs)
# Final credits are considered part of the final sketch.  This is inconsistent depending on episode.
# Some discrepency over the episode titles. Accepting first Wikipedia title for each episode as true. I don't have my DVD box set with me.  Feel free to come riff with me afterwards.
