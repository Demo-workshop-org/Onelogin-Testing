name: "Provision SCIM Users from IssueOps"
on:
  issues:
    types: [opened, edited]

jobs:
  provision:
    if: github.event.issue.title == 'provision_user' || github.event.issue.title == 'provision_enterprise_owner'
    runs-on: ubuntu-latest
    permissions:
      issues: write
      contents: read

    steps:
      - name: Checkout code
        uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'

      - name: Create requirements.txt
        run: |
          echo "requests" > requirements.txt
          echo "python-dotenv" >> requirements.txt
          echo "pandas" >> requirements.txt

      - name: Install dependencies
        run: pip install -r requirements.txt

      - name: Extract user emails from issue body
        id: extract
        run: |
          echo "email" > user_emails.csv
          echo "${{ github.event.issue.body }}" | tr -d '\r' >> user_emails.csv

      - name: Write .env file
        run: |
          echo "CLIENT_ID=${{ secrets.CLIENT_ID }}" >> .env
          echo "CLIENT_SECRET=${{ secrets.CLIENT_SECRET }}" >> .env
          echo "BASE_URL=${{ secrets.BASE_URL }}" >> .env
          echo "GITHUB_TOKEN=${{ secrets.GITHUB_TOKEN }}" >> .env
          echo "GITHUB_ENTERPRISE=${{ secrets.GITHUB_ENTERPRISE }}" >> .env
          if [[ "${{ github.event.issue.title }}" == "provision_user" ]]; then
            echo "GITHUB_ROLE=User" >> .env
          else
            echo "GITHUB_ROLE=enterprise_owner" >> .env
          fi

      - name: Run Provisioning Script
        run: |
          python onelogin_to_github_provision.py

      - name: Comment on issue
        uses: actions/github-script@v7
        with:
          script: |
            github.rest.issues.createComment({
              issue_number: context.issue.number,
              owner: context.repo.owner,
              repo: context.repo.repo,
              body: "✅ SCIM provisioning has been triggered. Check the workflow run for detailed logs."
            })
