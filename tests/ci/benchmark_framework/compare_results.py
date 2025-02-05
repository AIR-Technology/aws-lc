# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

import sys
import pandas as pd
import numpy as np

# Array containing ignored fields
ignored_fields = np.array(['TrustToken-Exp1-Batch1 generate_key',
    'TrustToken-Exp1-Batch1 begin_issuance',
    'TrustToken-Exp1-Batch1 issue',
    'TrustToken-Exp1-Batch1 finish_issuance',
    'TrustToken-Exp1-Batch1 begin_redemption',
    'TrustToken-Exp1-Batch1 redeem',
    'TrustToken-Exp1-Batch1 finish_redemption',
    'TrustToken-Exp1-Batch10 generate_key',
    'TrustToken-Exp1-Batch10 begin_issuance',
    'TrustToken-Exp1-Batch10 issue',
    'TrustToken-Exp1-Batch10 finish_issuance',
    'TrustToken-Exp1-Batch10 begin_redemption',
    'TrustToken-Exp1-Batch10 redeem',
    'TrustToken-Exp1-Batch10 finish_redemption',
    'TrustToken-Exp2VOfPRF-Batch1 generate_key',
    'TrustToken-Exp2VOfPRF-Batch1 begin_issuance',
    'TrustToken-Exp2VOfPRF-Batch1 issue',
    'TrustToken-Exp2VOfPRF-Batch1 finish_issuance',
    'TrustToken-Exp2VOfPRF-Batch1 begin_redemption',
    'TrustToken-Exp2VOfPRF-Batch1 redeem',
    'TrustToken-Exp2VOfPRF-Batch1 finish_redemption',
    'TrustToken-Exp2VOPRF-Batch10 generate_key',
    'TrustToken-Exp2VOPRF-Batch10 begin_issuance',
    'TrustToken-Exp2VOPRF-Batch10 issue',
    'TrustToken-Exp2VOPRF-Batch10 finish_issuance',
    'TrustToken-Exp2VOPRF-Batch10 begin_redemption',
    'TrustToken-Exp2VOPRF-Batch10 redeem',
    'TrustToken-Exp2VOPRF-Batch10 finish_redemption',
    'TrustToken-Exp2PMB-Batch1 generate_key',
    'TrustToken-Exp2PMB-Batch1 begin_issuance',
    'TrustToken-Exp2PMB-Batch1 issue',
    'TrustToken-Exp2PMB-Batch1 finish_issuance',
    'TrustToken-Exp2PMB-Batch1 begin_redemption',
    'TrustToken-Exp2PMB-Batch1 redeem',
    'TrustToken-Exp2PMB-Batch1 finish_redemption',
    'TrustToken-Exp2PMB-Batch10 generate_key',
    'TrustToken-Exp2PMB-Batch10 begin_issuance',
    'TrustToken-Exp2PMB-Batch10 issue',
    'TrustToken-Exp2PMB-Batch10 finish_issuance',
    'TrustToken-Exp2PMB-Batch10 begin_redemption',
    'TrustToken-Exp2PMB-Batch10 redeem',
    'TrustToken-Exp2PMB-Batch10 finish_redemption'])

# Helper function to read json or csv file data obtained from the speed tool into a pandas dataframe
def read_data(file):
    if file.endswith(".json"):
        df = pd.read_json(file)
    else:
        # This assumes we're using a csv generated by convert_json_to_csv.py
        df = pd.read_csv(file, skiprows=1, index_col=0)
    return df

def significant_regressions(compared_df):
    if compared_df.empty:
        return False
    descriptions = compared_df['description.1']
    evaluation = np.isin(descriptions, ignored_fields)
    return not np.all(evaluation)

def main():
    if len(sys.argv) != 4:
        print("Usage: compare_results.py [file1] [file2] [output filename]", file=sys.stderr)
        sys.exit(1)

    file1 = sys.argv[1]
    file2 = sys.argv[2]

    if not (file1.endswith(".json") or file1.endswith(".csv")) and not (file2.endswith(".json") or file2.endswith(".csv")):
        print("Provided files must either be .json files or .csv files", file=sys.stderr)
        sys.exit(1)

    # Read contents of files into a dataframe in preparation for comparison
    # Note: we're assuming that the provided input is derived from the json output of the speed tool
    df1 = read_data(file1)
    df2 = read_data(file2)

    # Only compare benchmarks that appear in both of the files
    # We need this because the speed tool at the time of writing has some tests that are disabled for OpenSSL
    # We're using .iloc[:, 0] here because we're filtering out rows where the content of the 0th index column in one df isn't in the other
    # details of .iloc can be found here: https://pandas.pydata.org/pandas-docs/stable/reference/api/pandas.DataFrame.iloc.html
    # .shape[0] represents the number of rows in the dataframe
    # Details of .shape can be found here: https://pandas.pydata.org/pandas-docs/version/0.23/generated/pandas.DataFrame.shape.html
    if df1.shape[0] > df2.shape[0]:
        df1 = df1[df1.iloc[:, 0].isin(df2.iloc[:, 0])]
    elif df2.shape[0] > df1.shape[0]:
        df2 = df2[df2.iloc[:, 0].isin(df1.iloc[:, 0])]

    # Reset any broken indices in the dataframe from the above
    df1.reset_index(drop=True, inplace=True)
    df2.reset_index(drop=True, inplace=True)

    # Rename df1 column labels
    df1.columns = [str(col) + '.1' for col in df1.columns]
    df2.columns = [str(col) + '.2' for col in df2.columns]

    print(df1.columns)

    # Setup data
    df1_numCalls = df1['numCalls.1']
    df2_numCalls = df2['numCalls.2']
    df1_time = df1['microseconds.1']
    df2_time = df2['microseconds.2']
    df1_avg_time = df1_time.astype(float) / df1_numCalls
    df2_avg_time = df2_time.astype(float) / df2_numCalls

    # Put both dataframes side by side for comparison
    dfs = pd.concat([df1, df2], axis=1)

    # Filter out entries with a +15% regression
    compared = np.where(((df2_avg_time / df1_avg_time) - 1) >= 0.15, df1.iloc[:, 0], np.nan)

    compared_df = dfs.loc[dfs.iloc[:, 0].isin(compared)]

    # Setup data for regressed entries
    compared_df1_numCalls = compared_df['numCalls.1']
    compared_df2_numCalls = compared_df['numCalls.2']
    compared_df1_time = compared_df['microseconds.1']
    compared_df2_time = compared_df['microseconds.2']
    compared_df1_avg_time = compared_df1_time.astype(float) / compared_df1_numCalls
    compared_df2_avg_time = compared_df2_time.astype(float) / compared_df2_numCalls

    # Add regression data to the table
    compared_df.loc[:, "Percentage Difference"] = 100 * ((compared_df2_avg_time / compared_df1_avg_time) - 1)

    # If the compared dataframe isn't empty, there are significant regressions present
    if significant_regressions(compared_df):
        output_file = sys.argv[3]
        if not output_file.endswith(".csv"):
            output_file += ".csv"

        with open(output_file, "w") as f:
            f.write("{},,,,{},,,,\n".format(file1, file2))
        compared_df.to_csv(output_file, index=False, mode='a')

        # Exit with an error code to denote there is a regression
        print("Regression detected between {} and {}".format(file1, file2), file=sys.stderr)
        exit(5)


if __name__ == "__main__":
    main()
