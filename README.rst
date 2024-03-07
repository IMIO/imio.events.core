.. This README is meant for consumption by humans and pypi. Pypi can render rst files so please do not use Sphinx features.
   If you want to learn more about writing documentation, please check out: http://docs.plone.org/about/documentation_styleguide.html
   This text does not appear on pypi or github. It is a comment.

.. image:: https://github.com/IMIO/imio.events.core/workflows/Tests/badge.svg
    :target: https://github.com/IMIO/imio.events.core/actions?query=workflow%3ATests
    :alt: CI Status

.. image:: https://coveralls.io/repos/github/IMIO/imio.events.core/badge.svg?branch=main
    :target: https://coveralls.io/github/IMIO/imio.events.core?branch=main
    :alt: Coveralls

.. image:: https://img.shields.io/pypi/v/imio.events.core.svg
    :target: https://pypi.python.org/pypi/imio.events.core/
    :alt: Latest Version

.. image:: https://img.shields.io/pypi/status/imio.events.core.svg
    :target: https://pypi.python.org/pypi/imio.events.core
    :alt: Egg Status

.. image:: https://img.shields.io/pypi/pyversions/imio.events.core.svg?style=plastic   :alt: Supported - Python Versions

.. image:: https://img.shields.io/pypi/l/imio.events.core.svg
    :target: https://pypi.python.org/pypi/imio.events.core/
    :alt: License


================
imio.events.core
================

Core product form iMio events website

Features
--------

This products contains:
- Content types: Agenda, Folder, Event


Examples
--------

- https://agenda.enwallonie.be


Documentation
-------------


    **ODWB endpoints:**

    @odwb

    - Push event(s) in odwb table : "iMio - Agenda - événements"

    - some subscribers are called to push/remove event in odwb table

    - We add an event in odwb table when it is published and remove it when it is unpublished (or deleted)

    - When we duplicate an event, the copy of this event is not push to odwb until it is published

    - When we move an event into another agenda, the event is updated in odwb table (the agenda title and its uid change)


    @odwb_entities

    - Push entities in odwb table : "iMio - Agenda - Entités"



Translations
------------

This product has been translated into

- French


Installation
------------

Install imio.events.core by adding it to your buildout::

    [buildout]

    ...

    eggs =
        imio.events.core


and then running ``bin/buildout``


Contribute
----------

- Issue Tracker: https://github.com/collective/imio.events.core/issues
- Source Code: https://github.com/collective/imio.events.core


License
-------

The project is licensed under the GPLv2.
