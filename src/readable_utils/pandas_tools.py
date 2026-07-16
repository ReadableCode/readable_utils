# %%
# Imports #

import json
import math
import os
import sys

import numpy as np
import pandas as pd

# append grandparent
if __name__ == "__main__":
    sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


import readable_utils.config_utils  # noqa: F401
from readable_utils.display_tools import pprint_df, print_logger
from readable_utils.number_tools import force_to_number

# %%
# Functions #


def compare_dataframe_columns(df_1, df_2, df_1_name, df_2_name):
    df_excel_columns = pd.DataFrame()
    df_excel_columns[f"columns_{df_1_name}"] = df_1.columns.tolist()
    df_snowflake_columns = pd.DataFrame()
    df_snowflake_columns[f"columns_{df_2_name}"] = df_2.columns.tolist()

    df_compare_columns = df_excel_columns.merge(
        df_snowflake_columns,
        how="outer",
        left_on=[f"columns_{df_1_name}"],
        right_on=[f"columns_{df_2_name}"],
        indicator=True,
    )
    df_compare_columns = df_compare_columns.sort_values(by=f"columns_{df_1_name}")

    print("df_compare_columns")
    pprint_df(df_compare_columns)

    print("columns not matches")
    pprint_df(df_compare_columns[df_compare_columns["_merge"] != "both"])


def merge_and_return_unmerged(df1, df2, merge_cols, how="left"):
    """
    Merge two dataframes on specified columns and return the merged dataframe
    and a dataframe with unmerged rows from the first dataframe.

    Parameters:
    - df1 (DataFrame): First DataFrame to merge.
    - df2 (DataFrame): Second DataFrame to merge.
    - merge_cols (list of str): List of columns to merge on.
    - how (str, optional): Type of merge to be performed.
        - 'left' (default): Use keys from left frame only,
            similar to a SQL left outer join.
        - 'right': Use keys from right frame only,
            similar to a SQL right outer join.
        - 'outer': Use union of keys from both frames,
            similar to a SQL full outer join.
        - 'inner': Use intersection of keys from both frames,
            similar to a SQL inner join.

    Returns:
    - merged_df (DataFrame): The merged DataFrame.
    - unmerged_df (DataFrame): Rows from df1 that did not merge.
    """

    # Merging the two dataframes
    merged_df = pd.merge(df1, df2, on=merge_cols, how=how, indicator=True)

    # Finding the rows from df1 that did not merge
    unmerged_df = merged_df.loc[merged_df["_merge"] == "left_only"].drop(
        columns=["_merge"]
    )

    # Drop the indicator column from merged dataframe
    merged_df = merged_df.drop(columns=["_merge"])

    return merged_df, unmerged_df


def read_csv_with_decode_error_handling(
    file_path, run_byte_and_symbol_replacement=False
):
    if run_byte_and_symbol_replacement:
        # Read the file in binary mode ('rb')
        with open(file_path, "rb") as f:
            file_content_bytes = f.read()

        dict_bytes_to_replace = {
            b"\x96": b"",
            b"\x92": b"",
            b"\x93": b"",
            b"\x94": b"",
            b"\xcf": b"",
            b"\xc8": b"",
            b"\xd1": b"",
            b"\xd9": b"",
            b"\xc0": b"",
            b"\xae": b"",
            b"\xc7": b"",
        }

        print("replaced bytes")

        for byte_to_replace, replacement in dict_bytes_to_replace.items():
            file_content_bytes = file_content_bytes.replace(
                byte_to_replace, replacement
            )

        # Open the file in write binary mode ('wb') to overwrite its content
        with open(file_path, "wb") as f:
            f.write(file_content_bytes)

        with open(file_path, "r") as f:
            file_contents = f.read()

        dict_strings_to_replace = {
            "Ñ": "N",
            "’": "",
            "Ù": "U",
            "À": "A",
            "®": "",
            "Ç": "C",
        }

        for string_to_replace, replacement in dict_strings_to_replace.items():
            file_contents = file_contents.replace(string_to_replace, replacement)

        # Write the modified contents to a new file
        with open(file_path, "w") as f:
            f.write(file_contents)

    try:
        df = pd.read_csv(file_path, low_memory=False)
    except Exception as e:
        print_logger(f"Failed to read file: {file_path} because {e}")
        if run_byte_and_symbol_replacement:
            raise Exception(f"Failed to read file: {file_path} because {e}")

        return read_csv_with_decode_error_handling(
            file_path, run_byte_and_symbol_replacement=True
        )

    return df


def list_to_df_columns(ls_values, number_of_columns, total_rows=None):
    # If total_rows is specified, pad the list to match the desired row count
    if total_rows:
        ls_values = ls_values[:total_rows]
        padded_values = ls_values + [""] * (total_rows - len(ls_values))
    else:
        padded_values = ls_values

    # Calculate the total length and items per column
    total_length = len(padded_values)
    items_per_column = math.ceil(total_length / number_of_columns)

    # Split the padded list into the required number of columns
    columns = [
        padded_values[i : i + items_per_column]
        for i in range(0, total_length, items_per_column)
    ]

    # Transpose the columns into rows to create a DataFrame
    df_columns = pd.DataFrame(columns).transpose()
    df_columns = df_columns.fillna("")
    return df_columns


# %%
# Upload Preparation Functions #


def sanitize_string_column(df, col_name):
    # Fill NaN with a placeholder
    df[col_name] = df[col_name].fillna("TempNaNPlaceholder")

    # Perform string operations
    df[col_name] = df[col_name].astype(str)
    df[col_name] = (
        df[col_name]
        .str.replace(",", "")
        .str.replace("'", "")
        .str.replace('"', "")
        .str.replace("\r", "")
        .str.replace("\n", "")
    )

    # Revert placeholder to NaN
    df[col_name] = df[col_name].replace("TempNaNPlaceholder", np.nan)

    return df


def sanitize_ls_string_cols(df, ls_cols):
    for col in ls_cols:
        df = sanitize_string_column(df, col)

    return df


def print_schema_yaml_datasets_format(dict_schema):
    """
    Prints out a schema like this:
    - name: "ch"
      type: "string"
      comment: ""
    - name: "company_name"
      type: "string"
      comment: "company"
    """

    for key, value in dict_schema.items():
        if value["col_type"] == "float64":
            type_to_print = "double"
        elif value["col_type"] == "bool":
            type_to_print = "boolean"
        elif value["col_type"] == "int64":
            type_to_print = "int"
        elif value["col_type"] == "datetime64[ns]":
            type_to_print = "timestamp"
        else:
            type_to_print = value["col_type"]

        print(f"- name: {key}")
        print(f"  type: {type_to_print}")
        print('  comment: ""')


def print_schema_yaml_limesync_format(dict_schema, save_path=None):
    """
    Prints out a schema like this:
    - name: "ch"
      type: "string"
      comment: ""
    - name: "company_name"
      type: "string"
      comment: "company"
    """
    print("schema:")
    for key, value in dict_schema.items():
        if value["col_type"] == "float64":
            type_to_print = "double"
        elif value["col_type"] == "bool":
            type_to_print = "boolean"
        elif value["col_type"] == "int64":
            type_to_print = "int"
        elif value["col_type"] == "datetime64[ns]":
            type_to_print = "timestamp"
        else:
            type_to_print = value["col_type"]
        print(f"    {key}: {type_to_print}")

    if save_path:
        with open(save_path, "w") as f:
            f.write("schema:\n")
            for key, value in dict_schema.items():
                if value["col_type"] == "float64":
                    type_to_print = "double"
                elif value["col_type"] == "bool":
                    type_to_print = "boolean"
                elif value["col_type"] == "int64":
                    type_to_print = "int"
                elif value["col_type"] == "datetime64[ns]":
                    type_to_print = "timestamp"
                else:
                    type_to_print = value["col_type"]
                f.write(f"    {key}: {type_to_print}\n")


def generate_schema_from_df(df, save_path=None):
    df_copy = df.copy()
    dict_schema = {}
    for col_name in df_copy.columns.tolist():
        col_dtype = df_copy[col_name].dtype
        if col_dtype == "object":
            col_dtype = "string"
        else:
            col_dtype = str(col_dtype)
        col_lowered = col_name.lower()
        col_lowered = (
            col_lowered.replace(".", "_").replace(" - ", "_").replace(" ", "_")
        )

        dict_schema[col_lowered] = {
            "ls_rename_cols": list(set([col_name, col_name.lower(), col_name.upper()])),
            "col_type": col_dtype,
        }
        print(
            {
                "ls_rename_cols": list(
                    set([col_name, col_name.lower(), col_name.upper()])
                ),
                "col_type": col_dtype,
            }
        )

    if save_path:
        with open(save_path, "w") as f:
            json.dump(dict_schema, f)

    return dict_schema


def apply_schema(df, dict_schema):
    """
    Apply schema to a dataframe.

    Parameters:
    - df (DataFrame): DataFrame to apply schema to.
    - dict_schema (dict): Dictionary containing schema information in for formt:
        {
            "column_name": {
                "ls_rename_cols": ["col_name_1", "col_name_2"],
                "col_type": "int" | "float64" | "string" | "double"
            }
        }

    Returns:
    - df (DataFrame): DataFrame with schema applied.
    """
    print_logger("Applying schema to DataFrame")
    for col, dict_col in dict_schema.items():
        # rename cols to this col in schema
        if "ls_rename_cols" in dict_col:
            ls_cols_to_rename_to_col = dict_col["ls_rename_cols"]
            for col_to_rename_orig in ls_cols_to_rename_to_col:
                if col_to_rename_orig in df.columns:
                    df.rename(columns={col_to_rename_orig: col}, inplace=True)
                    break
        # if col doesnt exist still, init
        if col not in df.columns:
            print_logger(
                f"Column {col} not found in DataFrame. Initializing.", level="warning"
            )
            df[col] = ""
        # set col type
        col_type = dict_col["col_type"]
        if col_type in ["int", "float64", "double"]:
            df[col] = df[col].apply(force_to_number)
        elif col_type == "string":
            df = sanitize_string_column(df, col)
        df[col] = df[col].astype(col_type)
    return df[dict_schema.keys()]


def get_col_widths_styles(dataframe):
    # Calculate maximum width needed for each column
    col_widths = []
    for col in dataframe.columns:
        max_length = max(dataframe[col].astype(str).apply(len).max(), len(col))
        if max_length > 50:
            max_length = 50
        col_widths.append(max_length)

    # Define styles for each column
    styles = [
        {"selector": "th", "props": [("text-align", "left"), ("padding", "0.5rem")]}
    ]
    for i, width in enumerate(col_widths):
        styles.append({"selector": f".col{i}", "props": [("min-width", f"{width}ch")]})

    return styles


# %%
