import json
from hashlib import sha256
import pandas as pd
import matplotlib.pyplot as plt

def is_valid_indian_phone_number(phone_number):
    """
    Checks if a phone number is a valid Indian phone number (10 digits).

    Args:
        phone_number (str): The phone number to validate.

    Returns:
        bool: True if valid, False otherwise.
    """

    if phone_number is None:
        return False

    # Remove all characters except digits
    phone_number = ''.join(c for c in phone_number if c.isdigit())

    # Check length and prefix
    return len(phone_number) == 10 and (phone_number.startswith('91') or phone_number.startswith('+91'))

def calculate_age(birth_date):
    """
    Calculates the age from a birth date string in YYYY-MM-DD format.

    Args:
        birth_date (str): The birth date string.

    Returns:
        int: The calculated age, or None if birth date is null.
    """

    if birth_date is None:
        return None

    from datetime import date  # Import for age calculation

    try:
        birth_year = int(birth_date.split('-')[0])
        today = date.today()
        return today.year - birth_year
    except ValueError:
        return None  # Handle invalid birth date format

def process_json_data(filename):
    """
    Reads a JSON file, performs data manipulation, and returns the processed data as a pandas DataFrame.

    Args:
        filename (str): The path to the JSON file.

    Returns:
        pandas.DataFrame: The processed data, or None if there's an error.
    """

    with open(filename, 'r') as f:
        try:
            data = json.load(f)
        except json.JSONDecodeError:
            print("Error: Could not parse JSON data from the file.")
            return None  # Handle JSON parsing error

    processed_data = []
    for item in data:
        processed_item = {}
        processed_item['appointmentId'] = item.get('appointmentId')
        processed_item['phoneNumber'] = item.get('phoneNumber')

        # Extract patient details
        patient_details = item.get('patientDetails', {})
        processed_item['firstName'] = patient_details.get('firstName')
        processed_item['lastName'] = patient_details.get('lastName')
        processed_item['gender'] = patient_details.get('gender')
        processed_item['birthDate'] = patient_details.get('birthDate')

        # Transform gender
        processed_item['gender'] = 'male' if processed_item['gender'] == 'M' else (
            'female' if processed_item['gender'] == 'F' else 'others')

        # Rename birthDate to DOB and calculate age
        processed_item['DOB'] = processed_item.pop('birthDate')
        processed_item['Age'] = calculate_age(processed_item['DOB'])

        # Extract and process medicines (with logging)
        consultation_data = item.get('consultationData', {})
        medicines = consultation_data.get('medicines', [])
        print(f"Type of medicines before conversion: {type(medicines)}")

        # Handle potential non-list values in medicines
        if not isinstance(medicines, list):
            medicines = []  # Convert non-list values to empty lists
            print(f"Type of medicines after conversion (if necessary): {type(medicines)}


        processed_item['medicines'] = medicines

        # Derived column: fullName
        processed_item['fullName'] = ' '.join([processed_item.get('firstName', ''), processed_item.get('lastName', '')])

        # isValidMobile (using custom validation logic)
        processed_item['isValidMobile'] = is_valid_indian_phone_number(processed_item['phoneNumber'])

        # phoneNumberHash (SHA256 hash for valid numbers)
        if processed_item['isValidMobile']:
            phone_hash = sha256(processed_item['phoneNumber'].encode('utf-8')).hexdigest()
            processed_item['phoneNumberHash'] = phone_hash
        else:
            processed_item['phoneNumberHash'] = None

        processed_data.append(processed_item)

  df = pd.DataFrame(processed_data)
  return df

def generate_aggregated_data(dataframe):
    """
    Calculates aggregated data from the DataFrame and returns it as a dictionary.

    Args:
        dataframe (pandas.DataFrame): The DataFrame containing the processed data.

    Returns:
        dict: A dictionary containing the aggregated data.
    """

    def count_medicines(meds):
        """
        Counts the number of medicines in a list or handles non-list values.

        Args:
            meds: A medicine entry (potentially a list or other data type).

        Returns:
            int: The number of medicines (if meds is a list), or 0 otherwise.
        """

        if isinstance(meds, list):
            return len(meds)
        else:
            return 0  # Handle non-list values (e.g., log a warning or count as 0)

    aggregated_data = {
        'Age': dataframe['Age'].value_counts().to_dict(),
        'gender': dataframe['gender'].value_counts().to_dict(),
        'validPhoneNumbers': dataframe['isValidMobile'].sum(),
        'appointments': len(dataframe),
        'medicines': dataframe['medicines'].explode().apply(count_medicines).sum(),
        'activeMedicines': dataframe['medicines'].explode().apply(
            lambda medicine: medicine.get('IsActive', False)
        ).sum()  # Count active medicines across all appointments
    }

    return aggregated_data



def plot_pie_chart(aggregated_data):
    """
    Plots a pie chart for the number of appointments against gender distribution.

    Args:
        aggregated_data (dict): The dictionary containing the aggregated data.
    """

    gender_counts = aggregated_data['gender']
    gender_labels = gender_counts.keys()
    gender_values = gender_counts.values()

    plt.figure(figsize=(8, 8))
    plt.pie(gender_values, labels=gender_labels, autopct='%1.1f%%', startangle=140)
    plt.title('Number of Appointments by Gender')
    plt.axis('equal')  # Equal aspect ratio ensures a circular pie chart
    plt.show()


# Example usage
filename = '/content/DataEngineeringQ2.json'  # Replace with your JSON file path
dataframe = process_json_data(filename)

# Export to CSV
def export_to_csv(dataframe, filename, separator='~'):
    """
    Exports a pandas DataFrame to a CSV file with the specified separator and no index.

    Args:
        dataframe (pandas.DataFrame): The DataFrame to export.
        filename (str): The name of the CSV file.
        separator (str, optional): The separator to use between columns. Defaults to '~'.
    """

    dataframe.to_csv(filename, index=False, sep=separator)

# Export all columns to CSV
export_to_csv(dataframe, 'processed_data.csv')

# Generate aggregated data
aggregated_data = generate_aggregated_data(dataframe)

# Export aggregated data to JSON
with open('/content/DataEngineeringQ2.json', 'w') as f:
    json.dump(aggregated_data, f, indent=2)

# Plot pie chart
plot_pie_chart(aggregated_data)


