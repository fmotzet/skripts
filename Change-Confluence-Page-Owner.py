import requests
import json
from urllib.parse import urljoin
import time

# Function to get all pages with pagination
def get_all_pages_by_owner(owner_identifier):
    all_owner_pages = []
    
    # Start with the first page
    url = urljoin(base_url, "pages")
    params = {"limit": 100}  # Maximum allowed limit to reduce number of API calls
    next_page_token = None
    
    pageCounter = 1
    while True:
        # Add pagination token if available
        if next_page_token:
            params["cursor"] = next_page_token
            
        # Make the API request
        response = requests.get(
            url,
            params=params,
            auth=(email, api_token),
            headers={"Accept": "application/json"}
        )
                
        # Check if the request was successful
        if response.status_code != 200:
            print(f"Error during get_all_pages_by_owner: {response.status_code}")
            print(response.text)
            break
            
        data = response.json()
         
        print("Running... on Page " + str(pageCounter), end=" \r")
        pageCounter += 1
        
        # Filter pages by owner
        if "results" in data:
            for page in data["results"]:
                # Check if the page belongs to the target owner
                if page["ownerId"] == owner_identifier:
                    # If space filtering is enabled, check if the page belongs to the chosen space
                    if limit_to_space and page["spaceId"] != chosen_space_id:
                        continue
                    all_owner_pages.append(page)
        
        # Check if there are more pages
        if "_links" in data and "next" in data["_links"] and data["_links"]["next"]:
            # Extract the cursor from the next link
            next_page_token = data["_links"]["next"].split("cursor=")[1].split("&")[0] if "cursor=" in data["_links"]["next"] else None
        else:
            # No more pages
            print("\ndone")
            break
    
    return all_owner_pages

# Function to update page owner
def update_page_owner(page_id, new_owner_id):
    url = urljoin(base_url, f"pages/{page_id}")
    
    # According to Confluence API v2, we need to get the current version number first
    response = requests.get(
        url,
        auth=(email, api_token),
        headers={"Accept": "application/json"}
    )
    
    if response.status_code != 200:
        print(f"Error getting page {page_id}: {response.status_code}")
        print(response.text)
        return False
    
    page_data = response.json()
    current_version = page_data.get("version", {}).get("number", 0)
    
    # Now we can update the owner
    payload = {
        "id": page_data["id"],
        "status": page_data["status"],
        "title": page_data["title"],
        "ownerId": new_owner_id,
        "version": {
            "number": page_data["version"]["number"]+1,
            "message": "Updating page owner via Script"
        }
    }
    
    response = requests.put(
        url,
        json=payload,
        auth=(email, api_token),
        headers={
            "Accept": "application/json",
            "Content-Type": "application/json"
        }
    )
    
    if response.status_code == 200:
        return True
    else:
        print(f"Error updating page {page_id}: {response.status_code}")
        print(response.text)
        return False

# Function to convert space key to space ID
def get_space_id_from_key(space_key):
    space_url = urljoin(base_url, "spaces")
    space_params = {"keys": space_key}
    
    space_response = requests.get(
        space_url,
        params=space_params,
        auth=(email, api_token),
        headers={"Accept": "application/json"}
    )
    
    if space_response.status_code == 200:
        space_data = space_response.json()
        if "results" in space_data and len(space_data["results"]) > 0:
            space_id = space_data["results"][0]["id"]
            print(f"Found space ID: {space_id} for space key: {space_key}")
            return space_id
        else:
            print(f"Space with key '{space_key}' not found")
            return None
    else:
        print(f"Error getting space information: {space_response.status_code}")
        print(space_response.text)
        return None

# Confluence Cloud credentials
email = input("Enter Mail: ").rstrip()
api_token = input ("Enter API token: ")
base_url = "https://!!!YOURDOMAIN!!!.atlassian.net/wiki/api/v2/"

# Check if Owner Change should be limited to one Space
while True:
    limit_to_space_string = input("Should this be limited to one space? (y/n): ").lower().rstrip()
    if limit_to_space_string in ['y', 'n']:
        if limit_to_space_string == 'y':
            limit_to_space = True
        else: 
            limit_to_space = False
        break
    else:
        print("Invalid input. Please enter 'y' or 'n'.")

if limit_to_space == True:
    while True:
        space_key = input("Please enter the space key: ").rstrip()
        chosen_space_id = get_space_id_from_key(space_key)
        if chosen_space_id:
            break
        retry = input("Do you want to try a different space key? (y/n): ").lower().rstrip()
        if retry != 'y':
            print("Operation cancelled.")
            exit(1)

# The current owner's account ID
current_owner = input ("Enter curent owner ID: ").rstrip()

# The new owner's account ID that will replace the current owner
new_owner = input ("Enter new owner ID: ").rstrip()

# Get all pages by the current owner
print(f"Finding all pages owned by {current_owner}...")
print("Waiting on Atlassian Server...")
owner_pages = get_all_pages_by_owner(current_owner)

# Print the results
print(f"Found {len(owner_pages)} pages owned by {current_owner}")
print("Pages to be updated:")
for page in owner_pages:
    print(f"Title: {page['title']}, ID: {page['id']}, URL: {page['_links']['webui']}")


# Ask for confirmation before proceeding with updates
confirmation = input(f"\nDo you want to update all {len(owner_pages)} pages to the new owner {new_owner}? (y/n): ")

if confirmation.lower() == 'y':
    # Create a backup of the pages
    with open("pages_backup.json", "w") as f:
        json.dump(owner_pages, f, indent=2)
    print("Created backup in pages_backup.json")
    
    # Update each page owner
    success_count = 0
    failure_count = 0
    
    print(f"\nUpdating page owners from {current_owner} to {new_owner}...")
    for i, page in enumerate(owner_pages):
        page_id = page['id']
        title = page['title']
        
        print(f"Updating {i+1}/{len(owner_pages)}: {title} ({page_id})...", end=" ")
        
        if update_page_owner(page_id, new_owner):
            print("SUCCESS")
            success_count += 1
        else:
            print("FAILED")
            failure_count += 1
        
        # Add a small delay to avoid rate limiting
        time.sleep(0.5)
    
    print("\nUpdate completed!")
    print(f"Successfully updated: {success_count} pages")
    print(f"Failed updates: {failure_count} pages")
    
    # Save the results
    results = {
        "success_count": success_count,
        "failure_count": failure_count,
        "updated_pages": [page for page in owner_pages if update_page_owner(page['id'], new_owner)]
    }
    
    with open("update_results.json", "w") as f:
        json.dump(results, f, indent=2)
    
else:
    print("Update operation cancelled.")
