# onelogin_to_github_provision.py
import csv
import requests
import json
import os
from dotenv import load_dotenv
import pandas as pd
from datetime import datetime

# Load environment variables
load_dotenv()

# OneLogin Environment
CLIENTID = os.getenv('CLIENTID')
CLIENTSECRET = os.getenv('CLIENTSECRET')
BASEURL = os.getenv('BASEURL')

# GitHub SCIM Environment
GPAT = os.getenv("GPAT")
GENTERPRISE = os.getenv("GENTERPRISE")
GITHUB_ROLE = os.getenv("GITHUB_ROLE", "member")

if not GPAT or not GENTERPRISE:
    raise ValueError("Please set GPAT and GENTERPRISE in the .env file.")

GITHUB_SCIM_URL = f"https://api.github.com/scim/v2/enterprises/{GENTERPRISE}/Users"
EMAIL_CSV = 'user_emails.csv'

def get_access_token():
    url = "https://api.us.onelogin.com/auth/oauth2/v2/token"
    headers = {"Content-Type": "application/json"}
    payload = {
        "grant_type": "client_credentials",
        "CLIENTID": CLIENTID,
        "CLIENTSECRET": CLIENTSECRET
    }
    response = requests.post(url, headers=headers, json=payload)
    response.raise_for_status()
    return response.json().get("access_token")

def fetch_user_by_email(email, token):
    url = f"{BASEURL}/api/1/users"
    headers = {
        "Authorization": f"bearer:{token}",
        "Accept": "application/json"
    }
    params = {"email": email}
    response = requests.get(url, headers=headers, params=params)
    response.raise_for_status()

    users = []
    for user in response.json().get("data", []):
        user_id = user.get("id", "")
        username = user.get("username", "")
        first_name = user.get("firstname", "")
        last_name = user.get("lastname", "")
        email = user.get("email", "")
        full_name = f"{first_name} {last_name}".strip()

        users.append({
            "externalId": user_id,
            "userName": username,
            "formatted": full_name,
            "familyName": last_name,
            "givenName": first_name,
            "displayName": full_name,
            "email": email,
            "role": GITHUB_ROLE
        })

    return users

def provision_user(row):
    if not row.get('userName') or not row.get('email'):
        print(f"Skipping row due to missing userName or email: {row}")
        return

    payload = {
        "schemas": ["urn:ietf:params:scim:schemas:core:2.0:User"],
        "externalId": str(row.get('externalId')),
        "active": True,
        "userName": row.get('userName'),
        "name": {
            "formatted": row.get('formatted'),
            "familyName": row.get('familyName'),
            "givenName": row.get('givenName')
        },
        "displayName": row.get('displayName'),
        "emails": [{
            "value": row.get('email'),
            "type": "work",
            "primary": True
        }],
        "roles": [{
            "value": row.get('role'),
            "primary": False
        }]
    }

    headers = {
        "Accept": "application/scim+json",
        "Authorization": f"Bearer {GPAT}",
        "X-GitHub-Api-Version": "2022-11-28",
        "Content-Type": "application/json"
    }

    response = requests.post(GITHUB_SCIM_URL, headers=headers, data=json.dumps(payload))
    print(f"Provisioning {row['userName']} ({row['email']}) with role '{row['role']}': {response.status_code}")
    if response.status_code not in (200, 201):
        print("Error:", response.text)

def main():
    if not CLIENTID or not CLIENTSECRET or not BASEURL:
        raise ValueError("Please set CLIENTID, CLIENTSECRET, and BASEURL in the .env file.")

    token = get_access_token()
    results = []

    try:
        with open(EMAIL_CSV, newline='', encoding='utf-8') as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                email = row.get("email")
                if not email:
                    continue
                try:
                    user_data = fetch_user_by_email(email, token)
                    if user_data:
                        for user in user_data:
                            results.append(user)
                            provision_user(user)
                    else:
                        print(f"User not found in OneLogin: {email}")
                except Exception as e:
                    print(f"Error processing {email}: {str(e)}")
    except FileNotFoundError:
        print("users.csv file not found.")
    except Exception as e:
        print(f"Unexpected error: {e}")

    if results:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_file = f"onelogin_user_details_{timestamp}.csv"
        df = pd.DataFrame(results)
        df.to_csv(output_file, index=False)
        print(f"\nResults saved to '{output_file}'")

if __name__ == "__main__":
    main()
