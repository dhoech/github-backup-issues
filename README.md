# Backup all your GitHub Issues
Python Script to Backup all Issues in all your Repositories (yours and all organizations you have access to) to json or html. Makes a local copy of images ~~and embedded PDFs~~ and replaces the urls to point to the local copy. Needs a GitHub Personal Access Token as an command-line arguement.

## Usage
- first use `python issue-backup.py YOUR_ACCESS_TOKEN --repos` to create a json of all available repos and modify as needed
- then use `python issue-backup.py YOUR_ACCESS_TOKEN [option]` to backup repos in the repo-list json
- options are --json or --html to create a json or html file as output

## Limitations
download of PDFs from issues, that are stored on github not working if you dont have admit rights for the repo they from. there doesnt seem to be a workaround; only if you have admit rights to access the pdf files
