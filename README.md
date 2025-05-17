# GitHub IssueOps: SCIM Provisioning and Deprovisioning

## 📋 Overview

This repository automates SCIM user provisioning and deprovisioning for GitHub Enterprise via OneLogin using GitHub Issues (IssueOps) and GitHub Actions.

## 🔧 Prerequisites

### ✅ Secrets (add to GitHub repository settings under `Settings > Secrets and variables > Actions > Secrets`):

* `CLIENT_ID`: OneLogin OAuth2 client ID
* `CLIENT_SECRET`: OneLogin OAuth2 client secret
* `BASE_URL`: OneLogin API base URL (e.g., `https://canarys2051.onelogin.com`)
* `GITHUB_TOKEN`: GitHub SCIM Personal Access Token with `admin:enterprise` scope
* `GITHUB_ENTERPRISE`: GitHub Enterprise slug (e.g., `my-enterprise`)

### ✅ Required Files:

* `onelogin_to_github_provision.py`: Python script to provision SCIM users
* `deprovision_scim_users.py`: Python script to deprovision SCIM users
* `.github/ISSUE_TEMPLATE/*.yml`: Issue templates for provisioning and deprovisioning
* `.github/workflows/*.yml`: Workflows to automate each task

### ✅ Required Python Packages

These are installed automatically via GitHub Actions:

```txt
requests
python-dotenv
pandas
```

## 📂 Directory Structure

```bash
├── .github
│   ├── ISSUE_TEMPLATE
│   │   ├── provision_user.yml
│   │   ├── provision_enterprise_owner.yml
│   │   └── deprovision_user.yml
│   └── workflows
│       ├── issueops-provision-scim.yml
│       └── issueops-deprovision-scim.yml
├── onelogin_to_github_provision.py
├── deprovision_scim_users.py
├── requirements.txt
└── README.md
```

## 🚀 How It Works

### 1. Provision Users (`User` Role)

* Open a new issue using the `Provision SCIM User` template.
* Paste a list of emails:

```
user1@example.com
user2@example.com
```

* GitHub Actions fetches these from OneLogin and provisions them as `User` in GitHub.

### 2. Provision Enterprise Owners

* Open a new issue using the `Provision SCIM Enterprise Owner` template.
* Paste a list of emails:

```
owner1@example.com
owner2@example.com
```

* They will be provisioned with `enterprise_owner` role.

### 3. Deprovision Users

* Open a new issue using the `Deprovision SCIM Users` template.
* Paste email addresses (one per line) to be removed:

```
user1@example.com
user2@example.com
```

* These users will be removed via SCIM.

## 🧠 Scripts Summary

### `onelogin_to_github_provision.py`

* Reads emails from `user_emails.csv`
* Fetches user metadata from OneLogin
* Provisions users to GitHub Enterprise via SCIM
* Role is defined via `.env` as `GITHUB_ROLE`

### `deprovision_scim_users.py`

* Reads emails from `users_to_deprovision.csv`
* Fetches SCIM user ID by email
* Deletes user via SCIM API

## 📜 Logging & Output

* Terminal output shows success/error for each user
* A file like `onelogin_user_details_<timestamp>.csv` is saved as a record of provisioned users

## 🧪 Example Use

1. Open GitHub > Issues > New Issue
2. Select the appropriate IssueOps template
3. Paste user email(s)
4. Submit issue — workflow is triggered

## ❓ FAQs

* **What if a user isn’t found in OneLogin?** The script skips and logs it.
* **What if GitHub provisioning fails?** The error is logged in the workflow run and issue comment.

## 🤝 Contributions

Feel free to fork, open issues or PRs to extend functionality (e.g., group-based provisioning, role mapping).

---

© 2025 Canarys Automations | GitHub SCIM Automation Toolkit
