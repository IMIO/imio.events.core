Using the development buildout
==============================

Create a virtualenv in the package::

    $ python3.10 -m venv .

Install requirements with pip::

    $ ./bin/pip3.10 install -r requirements.txt

Run buildout::

    $ ./bin/buildout

Start Plone in foreground:

    $ ./bin/instance fg


Running tests
-------------

    $ tox

list all tox environments:

    $ tox -l
    py38-Plone52
    build_instance
    code-analysis
    lint-py38
    coverage-report

run a specific tox env:

    $ tox -e py38-Plone52
