# Overview

Code in this directory is responsible for pulling, cleaning, and syncing PetFinder data
to the Code for Chicago Rescue Chicago Heroku Postgres database.

This is divided into three main scripts:

1. `data_getter.py` : Pulls data from the PetFinder API and saves it to a local file
1. `data_cleaner.py` : Cleans data into analytics-friendly features
1. `data_putter.py` : Syncs local data to the Heroku Postgres database

# Setup

To run any of these scripts, you'll need to install the requirements:

```bash
pip install -r requirements.txt
```

## Data Getter

To use the functions in this script, you'll need to set up your PetFinder API key
and secret as environment variables.

First, request an API and secret, and put these somewhere safe. You can request an API
key [here](https://www.petfinder.com/developers/).

Next, export your key and secret to your enviornment. For example, you could run:

```bash
export PETFINDER_KEY=<your-api-key>
export PETFINDER_SECRET=<your-api-secret>
```

Now, you're ready to run the script. To pull down the first 100K results for dogs in and
around Chicago, you can run:

```python
python data_getter.py
```

This will create a file called `chicago_animals.pkl` in the `rescuechi/petfinder/data`
folder.

## Data Cleaner

This script reads and saves files locally, so no extra set-up beyond installing the
python requirements is needed.

The script can be run by calling:

```python
python data_cleaner.py
```

This will create a file called `chicago_animals_clean.pkl` in the
`rescuechi/petfinder/data` folder.


## Data Putter

This script syncs data to Heroku, and in order to do so, requires you to set up the
database uri as an environment variable. There are two ways to do so, either by copying
the uri manually from the Heroku UI, or through the Heroku CLI.

### Option 1: Manual

To copy the uri manually, you will first need to be part of the team's Heroku account.
Then, navigate to https://data.heroku.com/ and select the datastore called
`postgresql-corrugated-21223`. Click on `settings`, then `View Credentials...`, and look for a variable called `URI`.

From the command line, run the following, replacing the value of `<paste-uri-here>`
with the value you see on Heroku's UI. It should start with `postgres://`:

```bash
export DATABASE_URL=<paste-uri-here>
```

You can test that this worked by running

```bash
echo $DATABASE_URL
```

and checking that it prints back your uri.

### Option 2: CLI

To use the Heroku CLI to get the database URI, first you will need to install the Heroku
CLI by following the instructions [here](https://devcenter.heroku.com/articles/heroku-cli#install-the-heroku-cli).

After this is installed and configured, you can run the following command:

```bash
export DATABASE_URL=$(heroku config:get HEROKU_POSTGRESQL_AMBER_URL --app  codeforchicago-rescuechi)
```

You can test that this worked by running

```bash
echo $DATABASE_URL
```

and checking that it prints back your uri.
