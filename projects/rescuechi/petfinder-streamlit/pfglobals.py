import streamlit as st
import pandas as pd
import os
import psycopg2
from psycopg2.extras import RealDictCursor

showQueries = os.environ['PETFINDER_STREAMLIT_SHOW_QUERIES']

DATABASE_URL = os.environ['HEROKU_POSTGRESQL_AMBER_URL']
WHERE_START = " WHERE "
AND_START = " AND "
BOOLEAN_DB_TYPE = "boolean"
STRING_DB_TYPE = "string"
DEFAULT_DROPDOWN_TEXT = "No value applied"

los_sort = ""
limit_query = ""
breeds_list = []
breeds_array = []

# @st.experimental_singleton
def init_connection(returnDict):
    if returnDict:
        return psycopg2.connect(DATABASE_URL, sslmode='require', cursor_factory=RealDictCursor)
    else:
        return psycopg2.connect(DATABASE_URL, sslmode='require'
                                )


# @st.experimental_memo(ttl=600)
def run_query(query, conn):
    with conn.cursor() as cur:
        cur.execute(query)
        return cur.fetchall()


conn_no_dict = init_connection(False)
conn_dict = init_connection(True)


def create_data_frame(data, index_column):
    df = pd.DataFrame().from_dict(data)
    df.set_index(index_column, inplace=True)
    return df


def create_array_of_db_values(db_column):
    # First get the list of values to be used for user interactions
    list_values_query = """
        SELECT DISTINCT(%s) FROM "%s" ORDER BY %s ASC;
        """ % (db_column, DATABASE_TABLE, db_column)
    #st.markdown(list_values_query)
    results = run_query(list_values_query, conn_no_dict)

    values_array = []
    for value in results:
        values_array.append(value[0])

    return values_array


# Create select boxes for the left and right side of charts
# isBoolean determines whether the DB column is a boolean, and thus whether we need to remove quotes
def create_select_boxes(db_column, text, col1, col2, is_boolean):
    db_col_type = STRING_DB_TYPE
    if is_boolean:
        # if we execute a query to find all True/False/None then the app takes way too long to load
        values = ["True", "False"]
    else:
        values = create_array_of_db_values(db_column)
    values.insert(0, DEFAULT_DROPDOWN_TEXT)

    with col1:
        select_box_left = st.selectbox(
            text,
            values,
            key=db_column + "_left"
        )

    with col2:
        select_box_right = st.selectbox(
            text,
            values,
            key=db_column + "_right"
        )
    return {"db_column": db_column, "db_col_type": db_col_type, "left": select_box_left, "right": select_box_right}


def create_comparison_chart(column, values, og_where_clause, main_db_col, is_los):
    if not og_where_clause:
        comparison_where_clause = WHERE_START
    else:
        comparison_where_clause = og_where_clause + " AND "

    i = 0
    while i < len(values):
        if i > 0 and values[i]["select_box"] != DEFAULT_DROPDOWN_TEXT and (comparison_where_clause != WHERE_START) and not (comparison_where_clause.endswith(AND_START)):
            comparison_where_clause += " AND "
        if values[i]["select_box"] != DEFAULT_DROPDOWN_TEXT and values[i]["db_col_type"] == STRING_DB_TYPE:
            comparison_where_clause += values[i]["db_column"] + "='" + values[i][
                "select_box"] + "'"  # need to get the attribute key in here (add to object above)
        elif values[i]["select_box"] != DEFAULT_DROPDOWN_TEXT and values[i]["db_col_type"] == BOOLEAN_DB_TYPE:
            if values[i]["select_box"]:
                comparison_where_clause += values[i]["db_column"] + "=True"
            elif not values[i]["select_box"]:
                comparison_where_clause += values[i]["db_column"] + "=False"
            else:
                comparison_where_clause += values[i]["db_column"] + "=None"
        i += 1

    # this means our where clause is empty, so clear it out
    if comparison_where_clause == WHERE_START:
        comparison_where_clause = ""

    # this means we have breeds set but nothing else, so set back to the breeds where query
    if comparison_where_clause.endswith(AND_START):
        comparison_where_clause = og_where_clause

    # if is_los then use LOS as the second column, otherwise just use count
    # (could be expanded later to other things as well)
    if is_los:
        comparison_query = """
            SELECT %s,AVG(los)::bigint as "LOS" FROM "%s" %s GROUP BY %s %s %s;
            """ % (main_db_col, DATABASE_TABLE, comparison_where_clause, main_db_col, los_sort, limit_query)
    else:
        comparison_query = """
                    SELECT %s,Count(*) as "Count" FROM "%s" %s GROUP BY %s %s %s;
                    """ % (main_db_col, DATABASE_TABLE, comparison_where_clause, main_db_col, los_sort, limit_query)

    with column:
        if showQueries:
            st.markdown("#### Query")
            st.markdown(comparison_query)
        query_results = run_query(comparison_query, conn_dict)
        if len(query_results) > 0:
            st.bar_chart(create_data_frame(query_results, main_db_col))
        else:
            st.write("Uh oh, no results were found with this criteria!  Please update your parameters to find results.")


def place_breeds_in_sidepanel():
    global breeds_list
    global breeds_array
    list_breeds_query = """
        SELECT DISTINCT(breed_primary) FROM "%s" ORDER BY breed_primary ASC;
        """ % DATABASE_TABLE
    if showQueries:
        st.markdown(list_breeds_query)

    breeds_results = run_query(list_breeds_query, conn_no_dict)

    breeds_array = []
    breeds_array_default = []
    for breed in breeds_results:
        breeds_array.append(breed[0])
    total_num_breeds = len(breeds_array)
    breeds_list = st.sidebar.multiselect(
        'Choose the breeds you want to see (will ignore the number of breeds set below if this field is set)',
        breeds_array, st.session_state.selected_breeds, key="selected_breeds"
    )
    if len(breeds_list) <= 0:
        number_of_breeds_slider = st.sidebar.slider(
            'How many breeds would you like to see?',
            1, 100, (20)
        )
    else:
        number_of_breeds_slider = 0

    return number_of_breeds_slider


def place_other_attributes_in_sidepanel(attribute_info_array):
    return_lists = []

    # first create a radio button with the possible attributes so that the user can choose the one they want
    attributes_array = []
    for attribute_info in attribute_info_array:
        attributes_array.append(attribute_info["text"])

    attributes_radio = st.sidebar.radio(
        "Choose an attribute",
        attributes_array
    )

    # now create a multiselect box for each attribute
    for attribute_info in attribute_info_array:
        db_column = attribute_info["db_column"]
        text = attribute_info["text"]

        if text == attributes_radio:
            array_of_items = create_array_of_db_values(db_column)

            selectbox = st.sidebar.multiselect(
                text,
                array_of_items,
                default=array_of_items
            )

            return_lists.append({"selectbox": selectbox, "value_list": selectbox, "db_column": db_column, "text": text})

    return return_lists


def place_los_sort_in_sidepanel(number_of_breeds_slider):
    global los_sort
    global limit_query
    los_sort_selectbox = st.sidebar.selectbox(
        'Sort By Length of Stay',
        ('DESC', 'ASC', 'NONE')
    )

    los_sort = "ORDER BY AVG(los) %s" % los_sort_selectbox if los_sort_selectbox != 'NONE' else ''
    limit_query = ""
    if number_of_breeds_slider > 0:
        limit_query = "LIMIT %s" % number_of_breeds_slider


if "DATABASE_TABLE" in os.environ:
    DATABASE_TABLE = os.environ['DATABASE_TABLE']
else:
    DATABASE_TABLE = "petfinder_with_dates"
