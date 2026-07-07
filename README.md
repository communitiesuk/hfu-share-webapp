# Share Homes for Ukraine data webapp

Django app to manage data for the 'Homes for Ukraine' scheme.

## Contents

- [Quickstart](#quickstart)
- [Database management and seed data](#database-management-and-seed-data)
- [Linting formatting and tests](#linting-formatting-and-tests)
- [Docker and containerisation](#docker)
- [User management](#user-management)
- [Troubleshooting](#troubleshooting)
- [Extra documentation / guides](/docs/index.md)

## Quickstart

For general development, the instructions below are sufficient for running the app.  Refer to other sections of this README for more detailed information.

### Requirements

>- Python >= 3.13 (https://www.python.org/downloads/)
>- Poetry (https://python-poetry.org/)
>- Docker (https://docs.docker.com/get-started/get-docker/)
>- Docker compose (https://docs.docker.com/compose/install/)

### Running on local using Poetry

#### 1. Install packages
```shell
poetry install
```

#### 2. Set up environment
```shell
cp .env.dev .env
```

Set `DB_HOST=localhost`
#### 3. Bring up database
```shell
docker compose up -d database
```

#### 4. Run dev server
```shell
poetry run dev
```

### Running on local using docker compose

#### 1. Set up environment
```shell
cp .env.dev .env
```

#### 2. Run docker compose
```shell
docker compose up

# Hint: If you need to run any command:
docker compose run web python manage.py
```

These instructions will get the app running.  You may also want to seed the database. See [seed data](#seed-data).

## Database management and seed data

### Clearing the database
```shell
# Local development
python manage.py flush

# Force delete the db
docker compose down
docker volume rm hfu-case-management-webapp_postgres_data
docker compose up
```

### Seed data

We use Django 'fixtures' to handle our seed data.

Seeding using the seeder script
```shell
poetry run seed-db
```

#### Dumping database to use as seed data
```shell
python manage.py dumpdata --exclude auth.permission --exclude contenttypes --exclude admin.logentry > db.json
```

## Developing with AWS

We use LocalStack in our `docker-compose` setup to emulate AWS services locally. This allows you to develop and test AWS integrations (like S3) without connecting to real AWS services.

For unit and integration tests, we use `moto` to mock AWS services.
The `S3TestCaseMixin` class in `webapp/tests/test_s3.py` sets up a mocked S3 environment for your tests. If your test needs to test AWS features, just inherit from the `S3TestCaseMixin` class.

### LocalStack Setup

LocalStack automatically starts when you run:
```shell
docker compose up localstack
```

If you want to run both the database and localstack:
```shell
docker compose up database localstack
```

On start up localstack will run the bash script from `hfurb_scripts/localstack-script.sh`.
This creates a bucket with four files inside.

The database seeder creates UAM records that reference these LocalStack files as attachments.
This means UAM download functionality works immediately after running the seeder - no additional setup required.

If you run the web app outside Docker and want to use the LocalStack S3 service, make sure your environment variables in the .env file are set for the AWS region, S3 bucket name and LocalStack AWS endpoint.

Note: LocalStack is only required if you need upload and download functionality for files in UAMs, Interactions, and Comments. Without LocalStack, file features will be missing in the app.

## Linting, formatting, and tests
### Linting
```shell
poetry run lint
```

### Code formatter
```shell
poetry run format
```

### Tests
Note: this requires the database container to be up and running
```shell
poetry run test
poetry run test-parallel
poetry run test-parallel uams.tests.test_detail_files
```

### Install pre-commit hooks
If you've added a new pre-commit hook or the currently installed ones aren't running, you can try running
```shell
poetry run pre-commit install
```
and if you've added a new one, run it against all the files (pre-commit will only run on the changed files during git hooks)
```shell
poetry run pre-commit run --all-files
```

## Docker

Included in this repository is a `Dockerfile.local` for building an image to run the django web app. There is also a docker compose file that runs the aforementioned image along with nginx to serve static files and proxy requests along with a postgres database.

Docker volumes are used to store the database data and so will persist between container runs.

Before you run `docker compose up`, copy `.env.dev` to `.env`

### Running database for local development

If you're developing the webapp locally you'll need a postgres database running for it to connect to. You can run one via

```shell
docker compose up -d database
```

### Building docker images

Run

```shell
docker compose build
```

### Running migrations

You can apply the migrations from your local changes to the postgres database by running
```shell
python manage.py makemigrations
python manage.py migrate
```

You can apply the migrations in the `web` docker image to the postgres database running in docker by running

```shell
docker compose run web python manage.py makemigrations
docker compose run web python manage.py migrate
```

### Running full app in docker

The `docker-compose.yaml` contains a configuration of running the app using gunicorn to serve the app behind nginx which proxies the requests and serves the static files. A postgres database is also run.

Build the images
```shell
docker compose build
```

Run the app
```shell
docker compose up
```

Access at http://localhost:8010

## User management

This app uses the built-in [Django user system](https://docs.djangoproject.com/en/5.1/topics/auth/).

### Creating a superuser

```shell
poetry run python manage.py createsuperuser --username=joe --email=joe@example.com
```

### Creating a regular user

Use the admin interface while logged in as superuser.

## Using the admin site

Django includes a built-in admin site at [localhost:8000/admin](http://localhost:8000/admin). You'll need to create a super user account to be able to access it, see [creating a super user](#creating-a-superuser).

## Troubleshooting

### Pycharm templates can't find static files

If you encounter issues resolving the static files in the template files while using Pycharm, ensure you have marked the template folder as a 'template folder' and static as a 'Resource root', and importantly that the settings file in Settings/Languages & Frameworks/Django is set to caseManagement/settings.py

### Static file changes not reflected in app running in docker container
First stop any running containers,
```shell
docker compose down
```

then, try deleting the `static_volume` volume with
```shell
docker volume rm static_volume
```

finally, re-build the images
```shell
docker compose build
```

### Error running `poetry install`
If you get an error about having the incorrect python version, try using [pyenv](https://github.com/pyenv/pyenv) to install a supported version.


## Contributing

We are not accepting external contributions for this repository.

## Vulnerability Disclosure

If you are a security researcher and have discovered a vulnerability in this code, we
appreciate your help in disclosing it to us in a responsible manner. Please refer to
[MHCLG's vulnerability disclosure policy](https://www.gov.uk/guidance/vulnerability-disclosure-policy-mhclg) for details.
