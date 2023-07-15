import sys
import os
import json
import requests
from datetime import datetime
from time import sleep
from github import Github

# Check if the access token is provided as a command-line argument and retrieve it
if len(sys.argv) < 2:
    print("Please provide the GitHub access token as a command-line argument.")
    sys.exit(0)
access_token = sys.argv[1]

# Check if the output format is provided as a command-line argument and retrieve it
if len(sys.argv) < 3:
    print("Please provide the output format (--html or --json) as a command-line argument, or provide --repo to create a list of all repositories availably wiht your account.")
    sys.exit(0)
option = sys.argv[2]
if option not in ["--html", "--json", "--repo"]:
    print("Invalid option arguement. Please choose either 'html', 'json' or '--repo'.")
    sys.exit(0)

# Initialize the PyGithub library with your access token
g = Github(access_token)

# Create a directory to store the JSON files
output_directory = "github_issues"
os.makedirs(output_directory, exist_ok=True)


# Download Images and PDFs and set the url to the local copy
def process_images_and_pdfs(content, data_directory, issue_number, comment_id=None):
    if content is None:
        return ""
    
    image_count = 0
    pdf_count = 0

    # Download and replace images
    content_iter = content
    while True:
        start_index = content_iter.find("![")
        if start_index == -1:
            break

        end_index = content_iter.find(")", start_index)
        if end_index == -1:
            break

        image_tag = content_iter[start_index:end_index + 1]
        image_url_start = image_tag.find("(") + 1
        image_url_end = image_tag.find(")")
        image_url = image_tag[image_url_start:image_url_end]

        if image_url.startswith("http"):
            image_count += 1
            image_extension = os.path.splitext(image_url)[1]
            if comment_id is not None:
                image_filename = f"{issue_number}_comment_{comment_id}_image_{image_count}{image_extension}"
            else:
                image_filename = f"{issue_number}_image_{image_count}{image_extension}"
            image_filepath = os.path.join(data_directory, image_filename)
            relative_image_path = os.path.relpath(image_filepath, repo_directory)
            if option == "--html":
                replace_string = "<img src='" + relative_image_path + "' alt='" + image_filename + "'>"
                content = content.replace(image_tag, replace_string)
            elif option == "--json":
                content = content.replace(image_url, relative_image_path)
            response = requests.get(image_url)
            with open(image_filepath, "wb") as image_file:
                image_file.write(response.content)

        content_iter = content_iter[end_index + 1:]

    # Download and replace PDFs
    # content_iter = content
    # while True:
    #     start_index = content_iter.find("[")
    #     if start_index == -1:
    #         break

    #     end_index = content_iter.find(")", start_index)
    #     if end_index == -1:
    #         break

    #     pdf_tag = content_iter[start_index:end_index + 1]
    #     pdf_url_start = pdf_tag.find("(") + 1
    #     pdf_url_end = pdf_tag.find(")")
    #     pdf_url = pdf_tag[pdf_url_start:pdf_url_end]

    #     if pdf_url.startswith("http") and pdf_url.lower().endswith(".pdf"):
    #         # print("PDF URL: " + pdf_url)
    #         pdf_count += 1
    #         pdf_extension = os.path.splitext(pdf_url)[1]
    #         if comment_id is not None:
    #             pdf_filename = f"{issue_number}_comment_{comment_id}_pdf_{pdf_count}{pdf_extension}"
    #         else:
    #             pdf_filename = f"{issue_number}_pdf_{pdf_count}{pdf_extension}"
    #         pdf_filepath = os.path.join(data_directory, pdf_filename)
    #         relative_pdf_path = os.path.relpath(pdf_filepath, repo_directory)
    #         content = content.replace(pdf_url, relative_pdf_path)
    #         response = requests.get(pdf_url, stream=True, allow_redirects=True)
    #         with open(pdf_filepath, "wb") as pdf_file:
    #             pdf_file.write(response.content)

    #     content_iter = content_iter[end_index + 1:]

    return content

def save_repo_list():
    repo_list = {}

    # Get the authenticated user
    user = g.get_user()

    # Get the user's repositories
    user_repos = [repo.full_name for repo in user.get_repos()]
    user_owned_repos = [repo for repo in user_repos if repo.split("/")[0] == user.login]
    if user_owned_repos:
        repo_list[user.login] = sorted(user_owned_repos, key=str.lower)

    # Get the user's organizations
    orgs = [org for org in user.get_orgs()]
    for org in orgs:
        org_repos = [repo.full_name for repo in org.get_repos()]
        org_owned_repos = [repo for repo in org_repos if repo.split("/")[0] == org.login]
        if org_owned_repos:
            repo_list[org.login] = sorted(org_owned_repos, key=str.lower)

    # Save the repository list to a JSON file
    with open("repo_list.json", "w") as file:
        json.dump(repo_list, file, indent=4)

    print("Repository list saved to repo_list.json")

# Check if the command-line argument "save_repos" is provided
if option == "--repo":
    save_repo_list()
    sys.exit(0)

# Load the repository list from the JSON file
try:
    with open("repo_list.json", "r") as file:
        repo_list = json.load(file)
except:
    print("Run with --repo arguement first to create repo list")
    sys.exit(0)

# Iterate over each repository in the repo_list
for owner, repos in repo_list.items():
    # Iterate over each repository
    for repo_name in repos:
        print("Limits: " + str(g.rate_limiting))
        repo_directory = os.path.join(output_directory, repo_name)
        os.makedirs(repo_directory, exist_ok=True)

        data_directory = os.path.join(repo_directory, "data")
        os.makedirs(data_directory, exist_ok=True)

        print("Repo: " + repo_name)
        repo = g.get_repo(repo_name)
        issues = repo.get_issues(state="all")

        # Iterate over each issue in the repository
        for issue in issues:
            # Check rate limits
            if g.rate_limiting[0] < 20:
                reset_time = datetime.utcfromtimestamp(g.rate_limiting_resettime)
                now = datetime.utcnow()
                duration = reset_time - now
                print("Rate Limit reached, waiting for " + str(duration.seconds/60) + " minutes")
                sleep(duration.seconds)
            issue_data = {
                "repo_name": repo_name,
                "number": issue.number,
                "title": issue.title,
                "state": issue.state,
                "date": issue.created_at.strftime("%Y-%m-%d"),
                "time": issue.created_at.strftime("%H:%M:%S"),
                "assignee": issue.assignee.login if issue.assignee else None,
                "labels": [label.name for label in issue.labels],
                "milestone": issue.milestone.title if issue.milestone else None,
                "body": process_images_and_pdfs(issue.body, data_directory, issue.number),
                "comments": []
            }

            # Retrieve comments for the issue
            comments = issue.get_comments()

            # Iterate over each comment
            for comment in comments:
                comment_data = {
                    "author": comment.user.login,
                    "date": comment.created_at.strftime("%Y-%m-%d"),
                    "time": comment.created_at.strftime("%H:%M:%S"),
                    "body": process_images_and_pdfs(comment.body, data_directory, issue.number, comment.id)
                }
                issue_data["comments"].append(comment_data)

            if option == "--html":
                # Generate HTML content for the issue
                html_content = f"""
                    <!DOCTYPE html>
                    <html>
                    <head>
                        <title>{issue.title}</title>
                        <style>
                            body {{
                                font-family: Arial, sans-serif;
                                margin: 20px;
                            }}
                            h1 {{
                                font-size: 24px;
                            }}
                            h2 {{
                                font-size: 20px;
                                margin-top: 20px;
                            }}
                            p {{
                                margin-top: 5px;
                            }}
                            div {{
                                margin-top: 10px;
                                margin-bottom: 10px;
                            }}
                            .comment {{
                                border: 1px solid #ccc;
                                padding: 10px;
                            }}
                            .comment p {{
                                margin: 0;
                            }}
                        </style>
                    </head>
                    <body>
                        <h1>{issue.title}</h1>
                        <div>
                            <p><strong>Repository:</strong> {repo_name}</p>
                            <p><strong>Issue Number:</strong> {issue.number}</p>
                            <p><strong>State:</strong> {issue.state}</p>
                            <p><strong>Date:</strong> {issue.created_at.strftime("%Y-%m-%d")}</p>
                            <p><strong>Time:</strong> {issue.created_at.strftime("%H:%M:%S")}</p>
                            <p><strong>Assignee:</strong> {issue.assignee.login if issue.assignee else 'None'}</p>
                            <p><strong>Labels:</strong> {', '.join([label.name for label in issue.labels])}</p>
                            <p><strong>Milestone:</strong> {issue.milestone.title if issue.milestone else 'None'}</p>
                            <h2>Body</h2>
                            <div>{issue_data["body"]}</div>
                        </div>
                """

                # Generate HTML content for comments
                for comment_data in issue_data["comments"]:
                    html_content += f"""
                        <div class="comment">
                            <p><strong>Author:</strong> {comment_data["author"]}</p>
                            <p><strong>Date:</strong> {comment_data["date"]}</p>
                            <p><strong>Time:</strong> {comment_data["time"]}</p>
                            <div>{comment_data["body"]}</div>
                        </div>
                    """

                html_content += """
                    </body>
                    </html>
                """

                # Save the HTML content to a file
                issue_filename = f"{issue.number}.html"
                issue_filepath = os.path.join(repo_directory, issue_filename)
                with open(issue_filepath, "w") as issue_file:
                    issue_file.write(html_content)

                print(f"Issue {issue.number} saved as HTML.")

            elif option == "--json":
                # Save the issue data as JSON
                issue_filename = f"{issue.number}.json"
                issue_filepath = os.path.join(repo_directory, issue_filename)
                with open(issue_filepath, "w") as issue_file:
                    json.dump(issue_data, issue_file, indent=4)

                print(f"Issue {issue.number} saved as JSON.")