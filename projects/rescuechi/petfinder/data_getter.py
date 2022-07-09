import os
import pandas as pd
import requests
from pathlib import Path
import pickle

DATA_DIR = Path(__file__).parent / "data"


def check_for_secrets():
    """
    Checks that you have the required credentials in your environment
    """
    assert os.getenv("PETFINDER_KEY") is not None
    assert os.getenv("PETFINDER_SECRET") is not None


def get_token() -> str:
    """
    Returns
    -------
    Access token for the PetFinder API

    Notes
    -----
    This is the example of getting a token from the petfinder docs:
    curl -d "grant_type=client_credentials&client_id={CLIENT-ID}&client_secret=\
        {CLIENT-SECRET}" https://api.petfinder.com/v2/oauth2/token
    """
    # make sure you have required variables in your environment
    check_for_secrets()

    url = "https://api.petfinder.com/v2/oauth2/token"

    CLIENT_ID = os.getenv("PETFINDER_KEY")
    CLIENT_SECRET = os.getenv("PETFINDER_SECRET")

    headers = {
        "Content-Type": "application/x-www-form-urlencoded",
    }

    data = f"grant_type=client_credentials&client_id={CLIENT_ID}&client_secret={CLIENT_SECRET}"

    response = requests.post(url, headers=headers, data=data)

    # make sure it succeeded
    assert response.status_code == 200

    # just return the access_token
    return response.json()["access_token"]


def get_organizations() -> pd.DataFrame:
    """
    Returns
    -------
    List of all organizations listed on PetFinder within 100 miles of Chicago, formatted
    in a pandas DataFrame
    """

    token = get_token()

    # this is where we'll save our results
    DATA_DIR.mkdir(parents=True, exist_ok=True)

    url = "https://api.petfinder.com/v2/organizations"

    headers = {"Authorization": f"Bearer {token}"}

    params = {
        "location": "Chicago, IL",
        "sort": "distance",
        "distance": 100,
        "limit": 100,
        "page": 1,
    }

    # make the first call, and check how many total pages there are
    response = requests.get(url, headers=headers, params=params)

    # make sure that it actually worked
    assert response.status_code == 200

    # save temp results to file, so that we have them if something goes awry
    with open(DATA_DIR / "backup" / "orgs_page_1.pkl", "wb") as f:
        pickle.dump(response.json()["organizations"], f)

    pagination = response.json()["pagination"]

    # this is how many pages we need to iterate over
    num_pages = pagination["total_pages"]

    # this is how many total orgs we expect to catch
    total_count = pagination["total_count"]

    print(f"Found {total_count} organizations.")

    # start a list of orgs that we'll append to
    all_orgs = response.json()["organizations"]

    # iterate over all pages, starting with the 2nd page
    for page in range(2, num_pages + 1):
        # update params for current page
        params["page"] = page

        # make the call
        response = requests.get(url, headers=headers, params=params)

        # append orgs to master list
        all_orgs += response.json()["organizations"]

        # save temp results to file, so that we have them if something goes awry
        with open(DATA_DIR / "backup" / f"orgs_page_{page}.pkl", "wb") as f:
            pickle.dump(response.json()["organizations"], f)

    # check that we acutally got all organizations
    assert len(all_orgs) == total_count

    # convert to pandas
    df_orgs = pd.DataFrame(all_orgs)

    # save to pickle file
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    df_orgs.to_pickle(DATA_DIR / "chicago_orgs.pkl")
    df_orgs.to_csv(DATA_DIR / "chicago_orgs.csv", index=False)

    return df_orgs


def get_animals(
    type="dog", status="adopted", organization=None, max_pages=None
) -> pd.DataFrame:
    """
    Parameters
    ----------
    organization: string, optional
        String of organization ID, or comma-separated list of organization IDs
    type: string, optional
        Animal type, possible options can be looked up with PetFinder's Animal Types
        endpoint
    status: string, optional
        Accepted values include adoptable, adopted, found
    max_pages: int, optional
        Maximum number of pages to query over. Default is to collect all available pages

    Returns
    -------
    List of all animals listed on PetFinder within 100 miles of Chicago, formatted
    in a pandas DataFrame. If max_pages is specified, then returns 100 * max_pages
    animals sorted by proximity to Chicago
    """

    token = get_token()

    # this is where we'll save our results
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    (DATA_DIR / "backup").mkdir(parents=True, exist_ok=True)

    url = "https://api.petfinder.com/v2/animals"

    headers = {"Authorization": f"Bearer {token}"}

    params = {
        "type": type,
        "status": status,
        "organization": organization,
        "location": "Chicago, IL",
        "sort": "distance",
        "distance": 100,
        "limit": 100,
        "page": 1,
    }

    # make the first call, and check how many total pages there are
    response = requests.get(url, headers=headers, params=params)

    # make sure that it actually worked
    assert response.status_code == 200

    # save temp results to file, so that we have them if something goes awry
    with open(DATA_DIR / "backup" / f"animals_page_1.pkl", "wb") as f:
        pickle.dump(response.json()["animals"], f)

    pagination = response.json()["pagination"]

    # this is how many pages we need to iterate over
    num_pages = pagination["total_pages"]

    # this is how many total animals we expect to catch
    total_count = pagination["total_count"]

    print(f"Found {total_count} animals.")

    # start a list of animals that we'll append to
    all_animals = response.json()["animals"]

    # iterate over all remaining pages, starting with the 2nd page
    # if we set a value for max number of pages, only pull that many
    if max_pages is not None:
        num_pages = max_pages

    for page in range(2, num_pages + 1):
        # update params for current page
        params["page"] = page

        # make the call
        response = requests.get(url, headers=headers, params=params)

        # if it was not successful, finish and save results collected so far
        if response.status_code != 200:
            print(f"Completed pages 1 - {page-1} out of the requested {num_pages}")
            break

        # save temp results to file, so that we have them if something goes awry
        with open(DATA_DIR / "backup" / f"animals_page_{page}.pkl", "wb") as f:
            pickle.dump(response.json()["animals"], f)

        # append orgs to master list
        all_animals += response.json()["animals"]

    # convert to pandas
    df_animals = pd.DataFrame(all_animals)

    # save to pickle and csv file
    df_animals.to_pickle(DATA_DIR / "chicago_animals.pkl")
    df_animals.to_csv(DATA_DIR / "chicago_animals.csv", index=False)

    return df_animals

if __name__=="__main__":
    get_animals(
        type="dog", status="adopted", organization=None, max_pages=None
    )