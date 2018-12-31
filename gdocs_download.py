#!/usr/bin/env python
import argparse
import io
import os
import sys

from apiclient.http import MediaIoBaseDownload
from googleapiclient.discovery import build
from httplib2 import Http
from oauth2client import client, file, tools

# If modifying these scopes, delete the file token.json.
SCOPES = 'https://www.googleapis.com/auth/drive'

basedir = os.path.dirname(os.path.realpath(__file__))
credentials_filename = os.path.join(basedir, 'credentials.json')
token_filename = os.path.join(basedir, 'token.json')


def getservice():
    store = file.Storage(token_filename)
    creds = store.get()
    if not creds or creds.invalid:
        # Get credentials.json from https://console.developers.google.com/apis/credentials
        flow = client.flow_from_clientsecrets(credentials_filename, SCOPES)
        creds = tools.run_flow(flow, store)
    service = build('drive', 'v3', http=creds.authorize(Http()))
    return service


def list_files():
    service = getservice()

    # Call the Drive v3 API
    results = service.files().list(
        pageSize=10, fields="nextPageToken, files(id, name)").execute()
    items = results.get('files', [])

    if not items:
        print 'No files found.'
    else:
        print 'Files:'
        for item in items:
            print item


def download(doc_id):
    service = getservice()

    request = service.files().export_media(fileId=doc_id, mimeType='text/plain')
    fh = io.BytesIO()
    downloader = MediaIoBaseDownload(fh, request)
    done = False
    while done is False:
        status, done = downloader.next_chunk()
        sys.stderr.write("Download Google Doc %d%%.\n" % int(status.progress() * 100))

    fh.seek(0)
    text_obj = fh.read().decode('UTF-8')
    return text_obj.encode('utf-8')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description='Download a Google Doc as text. ',
        formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument('doc_id', metavar='id',
                        help='Google Doc id (hint: it is in the URL document/d/[id]/edit)')
    parser.add_argument('--credentials_json', metavar='cred',
                        help='You will need a credentials.json file from ' +
                        'https://console.developers.google.com/apis/credentials',
                        default=credentials_filename)

    args = parser.parse_args()

    if not os.path.exists(credentials_filename):
        parser.print_help()
        sys.exit(0)

    print download(args.doc_id)
