# onelogin_to_github_invite.py - Alternative using GitHub REST API
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

# GitHub Environment
GPAT = os.getenv("GPAT")
GENTERPRISE = os.getenv("GENTERPRISE")
GITHUB_ORG = os.getenv("GITHUB_ORG")  # Organization name within the enterprise (optional)
GITHUB_ROLE = os.getenv("GITHUB_ROLE", "direct_member")

if not GPAT:
    raise ValueError("Please set GPAT in the .env file.")

# Determine invitation method based on available configuration
if GITHUB_ORG:
    INVITATION_METHOD = "organization"
    print(f"Using organization invitation method for org: {GITHUB_ORG}")
elif GENTERPRISE:
    INVITATION_METHOD = "enterprise"
    print(f"Using enterprise invitation method for enterprise: {GENTERPRISE}")
else:
    raise ValueError("Please set either GITHUB_ORG (for organization invites) or GENTERPRISE (for enterprise invites) in the .env file.")

EMAIL_CSV = 'user_emails.csv'

def get_access_token():
    url = "https://api.us.onelogin.com/auth/oauth2/v2/token"
    headers = {"Content-Type": "application/json"}
    payload = {
        "grant_type": "client_credentials",
        "client_id": CLIENTID,
        "client_secret": CLIENTSECRET
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

def invite_user(email):
    """Invite user to GitHub using either organization or enterprise API"""
    
    if INVITATION_METHOD == "organization":
        return invite_user_to_org(email)
    elif INVITATION_METHOD == "enterprise":
        return invite_user_to_enterprise(email)
    else:
        print(f"❌ Unknown invitation method: {INVITATION_METHOD}")
        return False

def invite_user_to_org(email):
    """Invite user to GitHub organization using REST API"""
    url = f"https://api.github.com/orgs/{GITHUB_ORG}/invitations"
    
    headers = {
        "Accept": "application/vnd.github+json",
        "Authorization": f"Bearer {GPAT}",
        "X-GitHub-Api-Version": "2022-11-28",
        "Content-Type": "application/json"
    }
    
    payload = {
        "email": email,
        "role": GITHUB_ROLE
    }
    
    response = requests.post(url, headers=headers, json=payload)
    print(f"Inviting {email} to organization {GITHUB_ORG}: {response.status_code}")
    
    if response.status_code in (200, 201):
        invitation_data = response.json()
        print(f"  ✅ Organization invitation sent successfully. Invitation ID: {invitation_data.get('id')}")
        return True
    else:
        print(f"  ❌ Error: {response.text}")
        return False

def invite_user_to_enterprise(email):
    """Invite user to GitHub enterprise using REST API (if supported)"""
    # Note: Direct enterprise invitations may not be available via API
    # This is a placeholder for potential enterprise-level invitation logic
    
    # Alternative: Try to add as enterprise member (requires different permissions)
    url = f"https://api.github.com/enterprises/{GENTERPRISE}/actions/runner-groups"
    
    headers = {
        "Accept": "application/vnd.github+json",
        "Authorization": f"Bearer {GPAT}",
        "X-GitHub-Api-Version": "2022-11-28"
    }
    
    # Test if we have enterprise access
    test_response = requests.get(url, headers=headers)
    
    if test_response.status_code == 200:
        print(f"✅ Enterprise API access confirmed for {GENTERPRISE}")
        print(f"⚠️  Direct enterprise invitation for {email} not implemented - requires organization membership")
        print(f"   Consider using SCIM or adding to a specific organization within the enterprise")
        return False
    else:
        print(f"❌ No enterprise API access for {GENTERPRISE}: {test_response.status_code}")
        print(f"   Cannot invite {email} at enterprise level")
        return False

def main():
    if not CLIENTID or not CLIENTSECRET or not BASEURL:
        raise ValueError("Please set CLIENTID, CLIENTSECRET, and BASEURL in the .env file.")

    print("Getting OneLogin access token...")
    token = get_access_token()
    print("Token obtained successfully")
    
    results = []
    invitations_sent = 0

    try:
        with open(EMAIL_CSV, newline='', encoding='utf-8') as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                email = row.get("email", "").strip()
                if not email or email.startswith("#"):  # Skip comments and empty lines
                    continue
                    
                print(f"\nProcessing: {email}")
                try:
                    # Fetch user data from OneLogin
                    user_data = fetch_user_by_email(email, token)
                    if user_data:
                        for user in user_data:
                            results.append(user)
                            # Try to invite user to GitHub
                            if invite_user(user['email']):
                                invitations_sent += 1
                    else:
                        print(f"  User not found in OneLogin: {email}")
                        # Still try to invite by email
                        if invite_user(email):
                            invitations_sent += 1
                except Exception as e:
                    print(f"  Error processing {email}: {str(e)}")
                    
    except FileNotFoundError:
        print(f"{EMAIL_CSV} file not found. Please create it with email addresses.")
        return
    except Exception as e:
        print(f"Unexpected error: {e}")
        return

    print(f"\n=== Summary ===")
    print(f"Total invitations sent: {invitations_sent}")
    
    if results:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_file = f"onelogin_user_details_{timestamp}.csv"
        df = pd.DataFrame(results)
        df.to_csv(output_file, index=False)
        print(f"OneLogin user details saved to '{output_file}'")

if __name__ == "__main__":
    main()
