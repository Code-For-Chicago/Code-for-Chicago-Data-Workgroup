import os
import sqlalchemy
from pathlib import Path
import pandas as pd

DATA_DIR = Path(__file__).parent / "data"
FILE_TO_APPEND = "chicago_animals_cleaned.pkl"
TARGET_TABLE_NAME = "petfinder_with_dates"

def get_db_uri():
    """
    Returns
    -------
    uri : str
        Postgres uri that can be used to connect to our database
    """
    uri = os.getenv("DATABASE_URL")
    if uri is not None:
        # sqlalchemy has a little bit of funky behavior, see this heroku help article:
        # https://help.heroku.com/ZKNTJQSK/why-is-sqlalchemy-1-4-x-not-connecting-to-heroku-postgres
        if uri.startswith("postgres://"):
            uri = uri.replace("postgres://", "postgresql://", 1)
        return uri
    else:
        raise EnvironmentError(
            """
              To run this script, you'll need to set the Heroku Postgres URI as an 
              environment variable called `DATABASE_URL`.
              You can do this by either copy and pasting from the Heroku website:
              export DATABASE_URL=<paste-uri-here>
              Or by installing the heroku CLI and running:
              export DATABASE_URL=$(heroku config:get HEROKU_POSTGRESQL_AMBER_URL --app  codeforchicago-rescuechi)
              """
        )

def table_exists(engine: sqlalchemy.engine.Engine, table_name: str):
    """
    Given a database connection and table name, checks whether or not the table exists.
    
    Parameters
    ----------
    engine : sqlalchemy.engine.Engine
        Engine connection to the database
    table_name : str
        Name of the table to check for
    
    Returns
    -------
    bool
        Describes whether a table with the specified name exists in our database
    """
    exists_query = f"""
    SELECT EXISTS (
        SELECT FROM information_schema.tables
        WHERE table_name = '{table_name}'
    );
    """
    exists = engine.execute(exists_query).fetchone()[0]
    return exists

def print_row_count(engine: sqlalchemy.engine.Engine):
    """Prints a descriptive string about the number of rows in the global target table.

    Parameters
    ----------
    engine : sqlalchemy.engine.Engine
        Connection to the postgres database
    """
    exists = table_exists(engine, TARGET_TABLE_NAME)
    if not exists:
        print(f"Target table {TARGET_TABLE_NAME} does not yet exist.")
    else:
        num_rows = engine.execute(f"SELECT count(*) FROM {TARGET_TABLE_NAME}").fetchone()
        print(f"There are {num_rows} rows in table {TARGET_TABLE_NAME}")


def append_to_table(engine: sqlalchemy.engine.Engine):
    """Appends rows from the globally specified file to append to the target table.

    Parameters
    ----------
    engine : sqlalchemy.engine.Engine
        Connection to the postgres database
    """

    # this is the cleaned data that we'll append to the database
    df = pd.read_pickle(DATA_DIR / FILE_TO_APPEND)

    # append to the table if it already exists
    df.to_sql(TARGET_TABLE_NAME, con=engine, if_exists="append")


def drop_duplicate_rows(engine: sqlalchemy.engine.Engine):
    """Drops rows with dupliccatd 'id' values.
    
    Parameters
    ----------
    engine : sqlalchemy.engine.Engine
        Connection to the postgres database  
    """

    # delete any duplicate records, in case the same data gets added in multiple times
    delete_dupes_query = f"""
    DELETE FROM {TARGET_TABLE_NAME} a USING (
        SELECT MIN(ctid) as ctid, id
        FROM {TARGET_TABLE_NAME} 
        GROUP BY id HAVING COUNT(*) > 1
    ) b
    WHERE a.id = b.id 
    AND a.ctid <> b.ctid
    """
    engine.execute(delete_dupes_query)

if __name__=="__main__":
    # get the uri from environment variables
    uri = get_db_uri()
    
    # link to the postgres database
    engine = sqlalchemy.create_engine(uri, echo=False)
    print("Successfully connected to postgres")
    
    # check the current number of rows in the table
    print("Before modifying table: ")
    print_row_count(engine)
    
    # append datafile to table
    append_to_table(engine)
    
    # check the current number of rows in the table
    print("After appending data: ")
    print_row_count(engine)
    
    # remove any duplicated rows
    drop_duplicate_rows(engine)
    
    # check the current number of rows in the table
    print("After dropping duplicate rows: ")
    print_row_count(engine)