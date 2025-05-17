# deprovision_scim_users.py
import csv
import requests
import os
import sys
from dotenv import load_dotenv

load_dotenv()

BASE_URL = "https://api.github.com/scim/v2/enterprises"
TOKEN = os.getenv("GITHUB_TOKEN")
ENTERPRISE = os.getenv("ENTERPRISE_SLUG")
CSV_FILE = os.getenv("CSV_FILE", "users_to_deprovision.csv")

HEADERS = {
    "Authorization": f"Bearer {TOKEN}",
    "Accept": "application/scim+json"
}

def get_scim_user_id(email):
    url = f"{BASE_URL}/{ENTERPRISE}/Users"
    response = requests.get(url, headers=HEADERS)

    if response.status_code != 200:
        print(f"Failed to fetch SCIM Users: {response.status_code} {response.text}")
        sys.exit(1)

    users = response.json().get("Resources", [])
    for user in users:
        if user.get("emails", [{}])[0].get("value") == email:
            return user.get("id")

    print(f"No SCIM User ID found for email: {email}")
    return None

def delete_user(scim_user_id):
    url = f"{BASE_URL}/{ENTERPRISE}/Users/{scim_user_id}"
    response = requests.delete(url, headers=HEADERS)

    if response.status_code == 204:
        print(f"Successfully deleted user with SCIM ID: {scim_user_id}")
    else:
        print(f"Failed to delete user: {response.status_code} {response.text}")

def main():
    if not TOKEN or not ENTERPRISE:
        print("Error: GITHUB_TOKEN or ENTERPRISE_SLUG is not set.")
        sys.exit(1)

    try:
        with open(CSV_FILE, mode="r") as file:
            reader = csv.DictReader(file)
            for row in reader:
                email = row.get("email")
                if not email:
                    print("Email missing in row, skipping...")
                    continue

                print(f"Processing email: {email}")
                scim_user_id = get_scim_user_id(email)
                if scim_user_id:
                    delete_user(scim_user_id)
    except FileNotFoundError:
        print(f"Error: CSV file '{CSV_FILE}' not found.")
        sys.exit(1)

if __name__ == "__main__":
    main()
