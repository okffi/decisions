Helsinki Decisions
==================

Browse and annotate decisions made by the [city of Helsinki](http://www.hri.fi/en/) and other
[OpenAhjo](http://dev.hel.fi/apis/openahjo/) users.

The annotated information is made available on this service using
OpenAhjo format, with annotations added on.

This is a project funded by the European Union through the [D-CENT
project](http://dcentproject.eu) and managed by [Open Knowledge Foundation](http://okfn.org).

Install
-------

Pre-requisites: A Postgresql database. For default config, create a
database named `helsinkidecisions` that your user Postgresql account has
permissions for.

A minimal runnable instance can be operated as follows:

1. Go to the web/ directory
2. Install project requirements with `pip install -U -r requirements.txt`
3. Migrate database with `python manage.py migrate`
4. Compile translations with `python manage.py compilemessages`
5. Finally, run the project with `python manage.py runserver`

Repeat these steps every time you update for smooth sailing. For
production deployment, also run `python manage.py collectstatic`.

When first importing data to an empty database, create the text search
engine index with `python manage.py rebuild_index`. You can rebuild
the index any time.

Docker
------

Alternatively, you can build and run a composed Docker setup.

To create initial Docker environment:

    $ docker-machine create -d virtualbox dev

To enable Docker environment variables:

    $ eval $(docker-machine env dev)

To build/update existing containers:

    $ docker-compose build
    $ docker-compose up -d
    $ docker-compose run web /usr/local/bin/python manage.py migrate
    $ docker-compose run web /usr/local/bin/python manage.py collectstatic
    $ docker-machine ip dev

Optional things
---------------

Install libvoikko (e.g. 4.0.2) to your system to enable a little
smarter spelling in searching. We include the Python bindings.

Usage
-----

Fetch, index and process new decisions from external sources with
`python manage.py process_all`.

Acknowledgements
----------------

This project bundles the following third party assets and software
either modified or as is:

* [autocomplete.js (MIT)](https://github.com/autocompletejs/autocomplete.js)
* [optimal-select.js (MIT)](https://github.com/Autarc/optimal-select)
* [libvoikko Python bindings (MPL)](https://github.com/voikko/corevoikko)
* [jQuery (MIT)](https://github.com/jquery/jquery)
* [Bootstrap (MIT)](https://github.com/twbs/bootstrap)
