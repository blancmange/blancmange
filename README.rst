Blancmange
==========

**Do you have enough Python in your Python?**


Blancmange is sweet dessert that once featured in Monty Python's Flying Circus
playing tennis.  At the time of writing, this term isn't featured anywhere in
the CPython core code or documentation.  This is sad since the notion of a
large, extra-terrestrial dessert trying to take over the world whilst playing
tennis is quite hilarious.  There are many more Python references that aren't
present in the documentation, source, or elsewhere, so let's fix that.

This tool can scan a prescribed directory of source and determine which terms
from Monty Python's Flying Circus feature and which don't.

Use it to Python-ise your Python.

In addition, it can output some fun statistics and answer some queries regarding
the 45 standard English-language Flying Circus episodes, including:

* Total words spoken (165,483) [#f1]_
* Total lines spoken (10,100) [#f1]_
* Total number of sketches (~510) [#f1]_
* Which Python spoke the most words (Michael Palin, with 24%)
* How often Spam was mentioned (74 times in Flying Circus, 2225 times in CPython!)
* ...

.. [#f1] According to the source material.

Usage
=====

**Lacking rugged lumberjacks in your logging?**

**Not enough fun in your functions?**

Try Blancmanage today!

Script details
--------------

**flying-circus-db**
    Create the database that underpins the whole package. Draws data from
    the included HTML files.
**flying-circus**
    Output statistics on Flying Circus scripts.
**completely-different**
    Get a random line from Monty Python's Flying Circus
**blancmange**
    Perform textual analysis of a specified code base compared to the Flying
    Circus scripts.  Helpfully offers which areas of Monty Python you are
    lacking.

Installation
============

Install with ``easy_install blancmange`` or ``Buildout`` with the
``buildout.cfg`` in this package/repository.  Buildout is the easiest option
as this helps manage other parts such as episode data, and cloning the
CPython source automatically.

Todo
====

* Expand to encompass the movies and other specials
* Suggest where to add Python references and references which are needed.
  Working for non-Python languages would be a plus ;)
* Better code analysis and processing.  Just within comments or documentation,
  for example, or just variables.



