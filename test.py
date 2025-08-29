
import os
import sys

# Ensure the current directory is in sys.path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from createGoogleForm import GoogleFormsCreator

if __name__ == "__main__":
    creator = GoogleFormsCreator()
    try:
        result = creator.create_form_from_json("form_config.json")
        print("Form created successfully!")
        print(f"Form ID: {result['form_id']}")
        print(f"Responder URL: {result['responder_uri']}")
        print(f"Edit URL: {result['edit_uri']}")
    except FileNotFoundError:
        print("Error: form_config.json not found. Please ensure the file exists in the same directory.")
        print("Check that your JSON configuration file is named 'form_config.json'")
    except Exception as e:
        print(f"An error occurred: {str(e)}")
        print("Please check your credentials and API permissions.")