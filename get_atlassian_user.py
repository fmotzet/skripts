# Reads data from a .env file in the same dir, requeires, your.atlassian.net domain, your email, your token.

import requests
import json
import csv
import os
from datetime import datetime
from typing import List, Dict, Optional
from dotenv import load_dotenv


class AtlassianUserExporter:
    def __init__(self, base_url: str, email: str, api_token: str):
        """
        Initialize the Atlassian User Exporter.
        
        Args:
            base_url: Your Atlassian instance URL (e.g., https://your-domain.atlassian.net)
            email: Your admin email address
            api_token: Your Atlassian API token
        """
        self.base_url = base_url.rstrip('/')
        self.auth = (email, api_token)
        self.headers = {
            'Accept': 'application/json',
            'Content-Type': 'application/json'
        }
        
    def get_all_users(self) -> List[Dict]:
        """
        Fetch all users from Atlassian.
        Uses pagination to retrieve all users.
        
        Returns:
            List of user dictionaries containing accountId, username, and displayName
        """
        all_users = []
        start_at = 0
        max_results = 100  # Maximum allowed by API
        
        print("Fetching users from Atlassian...")
        
        while True:
            # Atlassian Cloud uses /rest/api/3/users/search for Jira
            url = f"{self.base_url}/rest/api/3/users/search"
            params = {
                'startAt': start_at,
                'maxResults': max_results
            }
            
            try:
                response = requests.get(
                    url,
                    auth=self.auth,
                    headers=self.headers,
                    params=params,
                    timeout=30
                )
                response.raise_for_status()
                
                users = response.json()
                
                if not users:
                    break
                
                # Extract relevant user information
                for user in users:
                    user_data = {
                        'account_id': user.get('accountId', ''),
                        'email': user.get('emailAddress', user.get('name', '')),
                        'display_name': user.get('displayName', ''),
                        'active': user.get('active', False),
                        'account_type': user.get('accountType', '')
                    }
                    all_users.append(user_data)
                
                print(f"Retrieved {len(all_users)} users so far...")
                
                # Check if we've retrieved all users
                if len(users) < max_results:
                    break
                    
                start_at += max_results
                
            except requests.exceptions.RequestException as e:
                print(f"Error fetching users: {e}")
                if hasattr(e, 'response') and e.response is not None:
                    print(f"Response: {e.response.text}")
                raise
        
        print(f"Total users retrieved: {len(all_users)}")
        return all_users
    
    def export_to_csv(self, users: List[Dict], filename: Optional[str] = None) -> str:
        """
        Export users to CSV file.
        
        Args:
            users: List of user dictionaries
            filename: Optional custom filename
            
        Returns:
            Path to the created CSV file
        """
        if filename is None:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"atlassian_users_{timestamp}.csv"
        
        with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
            if users:
                fieldnames = ['account_id', 'email', 'display_name', 'active', 'account_type']
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                
                writer.writeheader()
                writer.writerows(users)
        
        print(f"CSV export completed: {filename}")
        return filename
    
    def export_to_json(self, users: List[Dict], filename: Optional[str] = None) -> str:
        """
        Export users to JSON file.
        
        Args:
            users: List of user dictionaries
            filename: Optional custom filename
            
        Returns:
            Path to the created JSON file
        """
        if filename is None:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"atlassian_users_{timestamp}.json"
        
        with open(filename, 'w', encoding='utf-8') as jsonfile:
            json.dump(users, jsonfile, indent=2, ensure_ascii=False)
        
        print(f"JSON export completed: {filename}")
        return filename


def main():
    """Main execution function."""
    # Load environment variables from .env file
    load_dotenv()
    
    # Load configuration from environment variables or config file
    base_url = os.environ.get('ATLASSIAN_URL')
    email = os.environ.get('ATLASSIAN_EMAIL')
    api_token = os.environ.get('ATLASSIAN_API_TOKEN')
    
    # Check if credentials are provided
    if not all([base_url, email, api_token]):
        print("ERROR: Missing required credentials!")
        print("\nPlease set the following environment variables:")
        print("  - ATLASSIAN_URL: Your Atlassian instance URL (e.g., https://your-domain.atlassian.net)")
        print("  - ATLASSIAN_EMAIL: Your admin email address")
        print("  - ATLASSIAN_API_TOKEN: Your Atlassian API token")
        print("\nAlternatively, create a .env file or modify this script directly.")
        return
    
    try:
        # Initialize exporter
        exporter = AtlassianUserExporter(base_url, email, api_token)
        
        # Fetch all users
        users = exporter.get_all_users()
        
        if not users:
            print("No users found!")
            return
        
        # Filter users with valid email addresses and exclude those with account_id starting with "qm:"
        users_with_email = [
            u for u in users 
            if u.get('email') 
            and '@' in u.get('email', '') 
            and not u.get('account_id', '').startswith('qm:')
        ]
        
        # Export to both CSV and JSON
        csv_file = exporter.export_to_csv(users)
        json_file = exporter.export_to_json(users)
        
        # Export users with email to separate CSV
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        csv_email_file = exporter.export_to_csv(users_with_email, f"atlassian_users_cleaned_up_{timestamp}.csv")
        
        print(f"\n✓ Successfully exported {len(users)} users!")
        print(f"  All users CSV: {csv_file}")
        print(f"  All users JSON: {json_file}")
        print(f"  Users with email CSV: {csv_email_file} ({len(users_with_email)} users)")
        
    except Exception as e:
        print(f"\nERROR: {e}")
        return


if __name__ == "__main__":
    main()
