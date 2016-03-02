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

A minimal runnable instance can be operated as follows:

1. Install project requirements with `pip install -U -r requirements.txt`
2. Migrate database with `python manage.py migrate`
3. Compile translations with `python manage.py compilemessages`
4. Finally, run the project with `python manage.py runserver`

Repeat these steps every time you update for smooth sailing. For
production deployment, also run `python manage.py collectstatic`.