# Import libraries
import requests
import json
import pandas as pd
import swifter
import matplotlib.pyplot as plt


def convert_address_to_json(address: str) -> dict:
    # Define payload
    payload = {
        "address": {
            "addressLines": [
                address
            ],
        }
    }

    payload_json = json.dumps(payload)

    # Send request
    response = requests.post(query, data=payload_json)
    json_data = response.json()

    return json_data


def get_address_data(address: str or dict) -> dict:
    # Sometimes the address is passed in as a string, rather than JSON. If so, we convert it to json using the API.
    if type(address) == str:
        json_data = convert_address_to_json(address)
    else:
        json_data = address

    result_data = {'formattedAddress': json_data['result']['address']['formattedAddress']}

    verdict_components = ['inputGranularity', 'validationGranularity', 'geocodeGranularity', 'addressComplete',
                          'hasInferredComponents']
    for component in verdict_components:
        try:
            result_data[component] = json_data['result']['verdict'][component]
        except:
            result_data[component] = False

    address_components = json_data['result']['address']['addressComponents']
    for component in address_components:
        c = component['componentType']
        result_data[c] = component['componentName']['text']
        try:
            result_data[c + '_inferred'] = component['inferred']
        except:
            result_data[c + '_inferred'] = False

    return result_data


def get_filtered_df(data_path: str, save=True, max_rows=None) -> pd.DataFrame:
    if max_rows is None:
        filtered_df = pd.read_excel(data_path)
    else:
        filtered_df = pd.read_excel(data_path, nrows=max_rows)

    # Drop na values
    filtered_df.dropna(subset=['BILLTOSTATE', 'BILLTOZIPCODE'], inplace=True)

    # Some of the columns contain the address, other are NaN. Combine the addresses into one column.
    address_columns = ['ADDRESS1', 'ADDRESS2', 'BILLTOADDRESS1', 'BILLTOADDRESS2']
    city_columns = ['BILLTOCITY', 'CITY']
    # Find the columns that contain the address
    address_column = [column for column in address_columns if column in filtered_df.columns][0]
    city_column = [column for column in city_columns if column in filtered_df.columns][0]
    # Combine the address columns into one column
    filtered_df['full_address'] = filtered_df[address_column] + ', ' + filtered_df[city_column] + ', ' + filtered_df[
        'BILLTOSTATE'] + ' ' + filtered_df['BILLTOZIPCODE'].astype(str)

    # Add a column to df that displays the json data
    filtered_df['json_data'] = filtered_df['full_address'].swifter.apply(convert_address_to_json)

    # Add a column for each component of the address data from the json
    filtered_df = pd.concat([filtered_df, filtered_df['json_data'].swifter.apply(get_address_data).apply(pd.Series)],
                            axis=1)

    # drop unnecessary columns
    filtered_df.drop(columns=['subpremise', 'subpremise_inferred', 'point_of_interest', 'point_of_interest_inferred'],
                     inplace=True)

    if save:
        filtered_df.to_csv('addresses', index=False)

    return filtered_df


def generate_report(df_for_report: pd.DataFrame) -> None:
    # Plot all the bar graphs in one figure
    plt.figure(figsize=(20, 15))

    # list columns to plot
    cols = ['inputGranularity', 'validationGranularity', 'geocodeGranularity', 'addressComplete',
            'hasInferredComponents', 'street_number_inferred', 'route_inferred', 'locality_inferred',
            'administrative_area_level_1_inferred', 'postal_code_inferred', 'country_inferred',
            'postal_code_suffix_inferred']
    # Plot the bar graphs
    for i, column in enumerate(cols):
        plt.subplot(3, 4, i + 1)
        df_for_report[column].value_counts().plot(kind='bar')
        plt.title(column)

    # Increase Vertical Spacing
    plt.subplots_adjust(hspace=1)

    plt.show()


api_key = 'AIzaSyBm32aJxJ2Glizkf1LBpl00e363dKZ-C0Q'
url = "https://addressvalidation.googleapis.com/v1:validateAddress?key="
query = url + api_key
path = r"C:\Users\shtey\Downloads\EpicData.xlsx"

df = get_filtered_df(path, max_rows=1000) # Delete max_rows to run on the entire dataset
generate_report(df)
