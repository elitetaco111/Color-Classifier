import pandas as pd
from fuzzywuzzy import process

def classify_colors(input_csv, reference_csv, mapping_csv, output_csv, log_csv):
    # Load the input CSV (first file)
    input_data = pd.read_csv(input_csv)

    # Load the reference CSV (second file)
    reference_data = pd.read_csv(reference_csv)

    # Load the color mapping CSV (third file)
    color_mapping = pd.read_csv(mapping_csv)

    # Ensure the output columns exist in the input data
    input_data['Parent Color Primary'] = ""
    input_data['Item Name Color Primary'] = ""

    # List to store log messages
    log_messages = []

    # Iterate through each row in the input data
    for index, row in input_data.iterrows():
        team = row['Team']
        color_list = row['Color List']

        # Check if Color List is missing
        if pd.isna(color_list) or color_list.strip() == "":
            message = f"Missing Color List for Name: {row['Name']}, Team: {team}"
            print(message)
            log_messages.append({"Name": row['Name'], "Team": team, "Message": message})
            input_data.at[index, 'Parent Color Primary'] = "FAIL"
            input_data.at[index, 'Item Name Color Primary'] = "FAIL"
            continue

        # Convert Color List to all caps before comparing
        color_list_upper = color_list.upper()

        # Map the Color List to the New Color using the ColorMappingList
        color_mapping_row = color_mapping[color_mapping['Color List'] == color_list_upper]
        if color_mapping_row.empty:
            message = f"No mapping found for Color List: {color_list_upper}"
            print(message)
            log_messages.append({"Name": row['Name'], "Team": team, "Message": message})
            input_data.at[index, 'Parent Color Primary'] = "FAIL"
            input_data.at[index, 'Item Name Color Primary'] = "FAIL"
            continue

        new_color = color_mapping_row.iloc[0]['New Color']

        # Filter the reference data for the same team
        team_reference = reference_data[reference_data['Team'] == team]

        if team_reference.empty:
            message = f"No reference data found for Team: {team}"
            print(message)
            log_messages.append({"Name": row['Name'], "Team": team, "Message": message})
            input_data.at[index, 'Parent Color Primary'] = "FAIL"
            input_data.at[index, 'Item Name Color Primary'] = "FAIL"
            continue

        # Check for a perfect match first
        if new_color in team_reference['Parent Color Primary'].values:
            matched_row = team_reference[team_reference['Parent Color Primary'] == new_color].iloc[0]

            # Copy the Parent Color Primary and Item Name Color Primary to the input data
            input_data.at[index, 'Parent Color Primary'] = matched_row['Parent Color Primary']
            input_data.at[index, 'Item Name Color Primary'] = matched_row['Item Name Color Primary']
        else:
            # If no perfect match, perform fuzzy matching
            parent_colors = team_reference['Parent Color Primary'].tolist()
            closest_match, score = process.extractOne(new_color, parent_colors)

            if score >= 80:  # Use a threshold of 80 for a good match
                # Get the row in the reference data that matches the closest Parent Color Primary
                matched_row = team_reference[team_reference['Parent Color Primary'] == closest_match].iloc[0]

                # Copy the Parent Color Primary and Item Name Color Primary to the input data
                input_data.at[index, 'Parent Color Primary'] = matched_row['Parent Color Primary']
                input_data.at[index, 'Item Name Color Primary'] = matched_row['Item Name Color Primary']
            else:
                message = f"No good match found for New Color: {new_color} in Team: {team}"
                print(message)
                log_messages.append({"Name": row['Name'], "Team": team, "Message": message})
                input_data.at[index, 'Parent Color Primary'] = "FAIL"
                input_data.at[index, 'Item Name Color Primary'] = "FAIL"

    # Save the updated input data to the output CSV
    input_data.to_csv(output_csv, index=False)
    print(f"Updated data saved to {output_csv}")

    # Save the log messages to a CSV file
    log_df = pd.DataFrame(log_messages)
    log_df.to_csv(log_csv, index=False)
    print(f"Log messages saved to {log_csv}")

# Example usage
if __name__ == "__main__":
    input_csv = "iowa_state_test.csv"  # Replace with the path to the first CSV
    temp = input_csv.replace(".csv", "")
    reference_csv = "BuyerParentColorView.csv"  # Replace with the path to the second CSV
    mapping_csv = "ColorMappingList.csv"  # Replace with the path to the color mapping CSV
    output_csv = f"{temp}_output.csv"  # Replace with the desired output file path
    log_csv = f"{temp}_log.csv"  # File to save log messages

    classify_colors(input_csv, reference_csv, mapping_csv, output_csv, log_csv)