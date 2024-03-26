import json
import requests

def get_newest_github_sha(repo_url):
    # Extract owner and repository name from the URL
    parts = repo_url.strip('/').split('/')
    owner, repo = parts[-2], parts[-1]

    # GitHub API endpoint for getting the latest commit
    url = f"https://api.github.com/repos/{owner}/{repo}/commits"
    
    # Make a GET request to the GitHub API
    response = requests.get(url)
    
    # Check if the request was successful
    if response.status_code == 200:
        # Parse JSON response
        commits = response.json()
        if commits:
            # Return SHA of the newest commit
            return commits[0]['sha']
        else:
            return "No commits found"
    else:
        # If request fails, print the error status code
        return f"Error: {response.status_code}"

def find_outdated_assets(json_path: str):
    with open(json_path) as json_file:
        data = json.load(json_file)

    outdated_urls = []
    for asset in data:
        url = asset['url']
        newest_commit_in_store = asset['commits'][max(asset['commits'])]
        newest_commit_on_github = get_newest_github_sha(url)

        if newest_commit_in_store != newest_commit_on_github:
            outdated_urls.append(url)

    return outdated_urls

def update_assets(json_path: str, app_version: str = None):
    with open(json_path) as json_file:
        data = json.load(json_file)

    for asset in data:
        url = asset['url']
        newest_commit_in_store = asset['commits'][max(asset['commits'])]
        newest_commit_on_github = get_newest_github_sha(url)

        if newest_commit_in_store != newest_commit_on_github:
            version = max(asset['commits']) if app_version is None else app_version
            asset['commits'][version] = newest_commit_on_github

    with open(json_path, 'w') as json_file:
        json.dump(data, json_file, indent=4)

print(find_outdated_assets('Icons.json'))
update_assets('Icons.json', app_version="1.2.0-alpha")