import pandas as pd
from pathlib import Path

DATA_FOLDER = Path(__file__).parent / "data"

def calc_los(raw_published_col, raw_status_change_col) -> pd.Series:
    """
    Calculate the length of stay.

    Parameters
    ----------
    raw_published_col : pd.Series
        Raw column as returned from the Petfinder API that contains the timestamp that
        the pet was first put on the website.
    raw_status_change_col : pd.Series
        Raw column as returned from te Petfinder API that contains the timestamp that
        the pet status was changed (presumably from 'adoptable' -> 'adopted')
    Returns
    -------
    DataFrame with columns for:
        - Length of stay for each animal, as an integer with units of number of days
        - Published date as a timestamp
        - Status changed date as a timestamp
    """

    published_dt = pd.to_datetime(raw_published_col)
    published_dt.name = "published_at"
    
    status_change_dt = pd.to_datetime(raw_status_change_col)
    status_change_dt.name = "status_changed_at"

    los_days = (status_change_dt - published_dt).dt.days
    los_days.name = "los"
    
    los_df = pd.concat([published_dt, status_change_dt, status_change_dt], axis=1)
    
    return los_df

def explode_column(col, col_prefix) -> pd.DataFrame:
    """
    Take a column that cocntains a dictionary (e.g. breed, colors) and split it into
    multiple columns, one for each key of the dictionary.

    Parameters
    ----------
    col : pd.Series
        Single column containing dictionaries of values. For example, the column of
        breeds contains a 'primary', 'secondary', etc. breed per dog.
    col_prefix : str
        Prefix to prepend to each column. For example, if the dictionary has a key of
        'primary' and the col_prefix is set to 'breed', this will produce a column
        called 'breed_primary'

    Returns
    -------
    Dataframe with one column per key in the original column dictionary
    """
    exploded = col.apply(pd.Series)
    exploded.columns = [f"{col_prefix}_{c}" for c in exploded.columns]

    return exploded

if __name__ == "__main__":

    # read in the raw data
    data_file = DATA_FOLDER / "chicago_animals.pkl"
    df_raw = pd.read_pickle(data_file)

    # calculate the length of stay
    los = calc_los(df_raw["published_at"], df_raw["status_changed_at"])

    # clean up the columns that are dictionaries
    breeds = explode_column(df_raw["breeds"], "breed")
    colors = explode_column(df_raw["colors"], "color")
    environ = explode_column(df_raw["environment"], "good_with")
    attributes = explode_column(df_raw["attributes"], "attribute")

    # we can keep some columns as-is
    cols_as_is = ["id", "organization_id", "age", "gender", "size", "coat", "name"]

    # concatenate the final columns
    df_final = pd.concat([df_raw[cols_as_is], los, breeds, colors, environ, attributes], axis=1)
    
    # save cleaned dataframe to a pickle file
    df_final.to_pickle(DATA_FOLDER / "chicago_animals_cleaned.pkl")
