import os
import glob
import transaction
import re

from pyquery import PyQuery
from textblob import TextBlob

from blancmange.config import log
from blancmange.models import Person, Episode, Sketch, Keyword


here = os.path.abspath(os.path.dirname(__file__))

EPISODES = None
EPISODE_PATH = os.path.join(here, 'www.ibras.dk', 'montypython', 'episode')

# Process the files
def creation(dbsession):
    # XXX This should be TheTVDB, except its DB/PHP fails :(
    with open(os.path.join(here, 'episodes.html'), 'rb') as episodes_file:
        episode_html = episodes_file.read()
        episode_rows = PyQuery(episode_html)('#listtable tr')
        episode_text_rows = [[PyQuery(element).text() \
            for element in PyQuery(row).children()] for row in episode_rows]
        # Remove all rows not related to a standard episode
        episodes_clean = [(row[0], row[1]) for row in episode_text_rows \
            if 'x' in row[0]]
        # Construct our dictionary of episodes
        EPISODES = dict(enumerate(episodes_clean, 1))

    episode_paths = glob.glob(EPISODE_PATH + '*')
    people = {}

    for path in episode_paths:
        with open(path, 'rb') as content:
            episode_content = content.read()
            document = PyQuery(episode_content)

            # Determine all people featured in the episode
            if not people:
                people_elements = \
                    document[0].xpath('//center[contains(text(), "Colour code")]//font')
                people = {element.attrib['id']: \
                    Person(id=element.attrib['id'],
                        name=element.text) for element in people_elements}

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
                              raw=sketches_wrapper.html(),
                              path=path)

            # Process sketch links so we know which sketches are in a document.
            sketch_lookup = {}
            for sketch_link in document('a[href*="#"]'):
                internal_id = re.search('#(.*?)$', sketch_link.attrib['href']).groups()[0]
                sketch_lookup[internal_id] = Sketch(internal_id=internal_id,
                                                    name=sketch_link.text)

            # Process the rest of the HTML in the document to find sketch details
            sketches_html = sketches_wrapper.html().split('<a name="')
            for sketch_html in sketches_html:

                # Check first characters to determine sketch
                first = sketch_html[:sketch_html.find('"')]
                if not first.isnumeric():
                    # No sketch, add to general episode keywords
                    sketch = Sketch(internal_id=0, name='Introduction')
                else:
                    # Crazy assumption: final credits are part of final skit.
                    # We can't know better. The Pythons don't, either.
                    sketch = sketch_lookup.get(first)
                    if not sketch:
                        log.error('Found a sketch %s in Episode %i that does not exist' % (first, episode_number))
                        continue

                # Can be processed for any general words or terms later
                sketch.raw = sketch_html

                # Process keywords, determining who said what.
                # Anything not in a font-tag is considered unspoken (at least by anyone who matters)
                for line_spoken in sketch.lines:
                    line_actor = people[line_spoken.attrib['id']]
                    line_words = TextBlob(PyQuery(line_spoken).text())
                    # XXX Contractions get separated (eg "It's")
                    for word in line_words.words.lower():
                        keyword = Keyword(keyword=word, person=line_actor)
                        sketch.keywords.append(keyword)

                episode.sketches.append(sketch)
                log.debug('Created %r' % sketch)

            dbsession.add(episode)
            log.debug('Created %r' % episode)
            transaction.commit()

    transaction.commit()
