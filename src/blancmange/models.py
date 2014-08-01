from pyquery import PyQuery
from textblob import TextBlob

from sqlalchemy import Column, Integer, Unicode, ForeignKey
from sqlalchemy.orm import relationship, backref, scoped_session, sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from zope.sqlalchemy import ZopeTransactionExtension


Base = declarative_base()
DBSession = scoped_session(sessionmaker(extension=ZopeTransactionExtension()))


def utf8(fn):
    def wrapped(self):
        return fn(self).encode('utf8')
    return wrapped


class TextContainer(Base):
    """ HTML/Text helper methods for content.
    """
    __abstract__ = True

    #: Raw content can be processed for any script/unspoken words
    raw = Column(Unicode, nullable=False)

    @property
    def dom(self):
        return PyQuery(self.raw)

    @property
    def text(self):
        return self.dom.text()

    @property
    def textblob(self):
        return TextBlob(self.text)


class Person(Base):
    """ People need to be locatable using their id in the documents.
    """
    __tablename__ = 'people'
    id = Column(Unicode, primary_key=True)
    name = Column(Unicode)

    def __repr__(self):
        return '<Person %s>' % self.name

class Keyword(Base):
    __tablename__ = 'keywords'
    id = Column(Integer, primary_key=True, autoincrement=True)
    keyword = Column(Unicode)
    person_id = Column(Unicode, ForeignKey('people.id'))
    sketch_id = Column(Unicode, ForeignKey('sketches.id'))

    person = relationship('Person', backref='keywords')

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
    people = relationship('Person',
                          secondary=Keyword.__table__,
                          backref=backref('sketches'))

    def __repr__(self):
        return '<Sketch "%s" in "%s">' % \
            (self.name.encode('utf8'), self.episode.name.encode('utf8') if self.episode else self.episode)


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
        return '<Episode %i: "%s">' % (self.number, self.name.encode('utf8'))
