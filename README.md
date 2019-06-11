# Download Google Docs content into a plain text file


## Using the Google Docs API (recommended)

This will show the final document without comments.

Turn on Google Docs API https://developers.google.com/docs/api/quickstart/js , then run

    gdocs_download2.py documentid1234

## Using the Google Drive API (not recommended)

This will not show the suggested edits in the document, and  will leave the comments in the document.

Turn on Google Drive API https://developers.google.com/drive/api/v3/enable-sdk , then run

    gdocs_download.py documentid1234