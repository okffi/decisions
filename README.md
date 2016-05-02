[![Stories in Ready](https://badge.waffle.io/okffi/decisions.png?label=ready&title=Ready)](https://waffle.io/okffi/decisions)
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
    $ docker-compose run --rm web /usr/local/bin/python manage.py migrate
    $ docker-compose run --rm web /usr/local/bin/python manage.py collectstatic --noinput

You can find out the IP address to access the newly deployed site with
`docker-machine`:

    $ docker-machine ip dev

Deploying to production with Docker Compose
-------------------------------------------

The project will build a demo/development Docker cluster by
default. However, if you wish to deploy it in public, you should
create your own private settings:

1. Create a new Git branch.

2. Modify web/decisions/settings.py

3. Important: Change `SECRET_KEY`. Leaving the secret key unmodified allows
   strangers to guess session keys, etc. You can generate a new
   acceptable secret key with the following Python snippet:

        from django.utils.crypto import get_random_string
        chars = 'abcdefghijklmnopqrstuvwxyz0123456789!@#$%^&*(-_=+)'
        print get_random_string(50, chars)

4. Important: Change `DEBUG` to `False`. Leaving the debug state to true exposes
   a lot of internal information on error pages that probably
   shouldn't be shown to the general public.

5. Important: Change `ALLOWED_HOSTS` to only include fully qualified
   domain names you intend the site to be accessible on. You can have
   multiple.

6. Important: Change `SITE_URL` to point at a publicly accessible URL
   to the site root. This is used to build full URLs for email links
   and otherwise.

7. Change `ADMINS` with your name and email address. The site will
   send page error messages to you by mail.

8. You can set up a lot of site behavior with various settings. For
   example, you might want to setup your own email sending settings.

You should keep your own Git branch private. Push it to private
repositories, but not public ones.

After pulling new updates, sync them with your private branch with `git
merge`. From your branch:

    $ git merge master

You may need to resolve conflicts within your settings file.

Manual Docker deployment
------------------------

It might not be possible to use docker-compose to deploy, e.g. on a
shared host. Here are manual Docker commands to deploy on a generic
Docker host.

**Disclaimer:** These instructions are maintained separately from the
executable `docker-compose.yml` file, and the resulting setup might be
different/slightly out of date.

To get images for deployment, build containers with docker-compose as
usual:

    $ docker-compose build
    (test with docker-compose up)

Check the **names** of the built images with docker images (output may
look different)

    $ docker images
    REPOSITORY                          TAG                 IMAGE ID            CREATED             SIZE
    decisions_web               latest              8da3a688edd4        26 minutes ago      732.6 MB
    decisions_nginx             latest              1da419479050        26 minutes ago      206.1 MB

Then save the resulting web and nginx images

    $ docker save -o decisions.tar decisions_web
    $ docker save -o dec-nginx.tar decisions_nginx

Then upload them to host e.g. with scp or rsync

Set up Docker host for the first time, starting with network and volumes:

    # docker network create --driver bridge decisions
    # docker volume create --name dec-database
    # docker volume create --name dec-whoosh
    # docker volume create --name dec-static

Create generic service containers (postgres, redis):

    #  docker create --name dec-postgres \
        -v dec-database:/var/lib/postgresql \
        --expose 5432 \
        --restart always \
        --net-alias postgres \
        --net decisions \
	postgres:latest
    # docker create --name=dec-redis \
        --expose 6379 \
	--restart always \
        --net-alias redis \
	--net decisions \
	redis:latest

Update Docker images on the host:

    # docker load -i decisions.tar
    # docker load -i dec-nginx.tar

Create or re-create containers out of updated images:

    # docker create --name=decisions \
        -v dec-static:/usr/src/app/staticfiles \
	-v dec-whoosh:/usr/src/app/whoosh.idx \
	--expose 8000 \
	--env "DATABASE_URL=postgres://postgres:postgres@postgres:5432/postgres" \
	--restart always \
	--net-alias web \
	--net decisions \
	decisions_web
    # docker create --name=dec-nginx \
        -v dec-static:/usr/src/app/staticfiles \
	--restart=always \
	--net-alias=nginx \
	--net=decisions \
	--publish=8099:80 \
	decisions_nginx

You can now access the running Docker setup e.g. run management
commands with `docker exec`:

    # docker exec -it decisions python manage.py shell
    Python 2.7.11 (default, Mar 24 2016, 09:47:20)
    [GCC 4.9.2] on linux2
    Type "help", "copyright", "credits" or "license" for more information.
    (InteractiveConsole)
    >>>

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
