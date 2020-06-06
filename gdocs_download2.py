#!/usr/bin/env python3
"""
Recursively extracts the text from a Google Doc.
"""
import argparse
import os
import os.path
import pickle
import sys

from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

SCOPES = 'https://www.googleapis.com/auth/documents.readonly'
DISCOVERY_DOC = 'https://docs.googleapis.com/$discovery/rest?version=v1'

BASE_DIR = os.path.dirname(os.path.realpath(__file__))
CREDENTIALS_FILENAME = os.path.join(BASE_DIR, 'credentials.json')
TOKEN_FILENAME = os.path.join(BASE_DIR, 'token.pickle')

def get_credentials():
    """Shows basic usage of the Docs API.
    Prints the title of a sample document.
    """
    creds = None
    # The file token.pickle stores the user's access and refresh tokens, and is
    # created automatically when the authorization flow completes for the first
    # time.
    if os.path.exists(TOKEN_FILENAME):
        with open(TOKEN_FILENAME, 'rb') as token:
            creds = pickle.load(token)
    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                CREDENTIALS_FILENAME, SCOPES)
            creds = flow.run_local_server(port=0)
        # Save the credentials for the next run
        with open(TOKEN_FILENAME, 'wb') as token:
            pickle.dump(creds, token)
    return creds

def read_paragraph_element(element):
    """Returns the text in the given ParagraphElement.

        Args:
            element: a ParagraphElement from a Google Doc.
    """
    text_run = element.get('textRun')
    if not text_run or text_run.get('suggestedDeletionIds'):
        return ''
    return text_run.get('content')


def read_structural_elements(elements):
    """Recurses through a list of Structural Elements to read a document's text where text may be
        in nested elements.

        Args:
            elements: a list of Structural Elements.
    """
    text = ''
    for value in elements:
        if 'paragraph' in value:
            elements = value.get('paragraph').get('elements')
            for element in elements:
                text += read_paragraph_element(element)
        elif 'table' in value:
            # The text in table cells are in nested Structural Elements and tables may be
            # nested.
            table = value.get('table')
            for row in table.get('tableRows'):
                cells = row.get('tableCells')
                for cell in cells:
                    text += read_structural_elements(cell.get('content'))
        elif 'tableOfContents' in value:
            # The text in the TOC is also in a Structural Element.
            toc = value.get('tableOfContents')
            text += read_structural_elements(toc.get('content'))
    return text


def get_document(document_id):
    """Uses the Docs API to print out the text of a document."""
    credentials = get_credentials()
    # http = credentials.authorize(Http())
    docs_service = build('docs', 'v1', credentials=credentials)
    doc = docs_service.documents().get(documentId=document_id).execute()
    doc_content = doc.get('body').get('content')
    # print(doc_content)
    return read_structural_elements(doc_content)

def main():
    parser = argparse.ArgumentParser(
        description='Download a Google Doc as text. ',
        formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument('doc_id', metavar='id',
                        help='Google Doc id (hint: it is in the URL document/d/[id]/edit)')
    parser.add_argument('--credentials_json', metavar='cred',
                        help='You will need a credentials.json file from ' +
                        'https://console.developers.google.com/apis/credentials ' +
                        ' and probably you will need to enable Docs API as well ' +
                        ' at https://console.developers.google.com/apis/api/docs.googleapis.com',
                        default=CREDENTIALS_FILENAME)

    args = parser.parse_args()

    if not os.path.exists(CREDENTIALS_FILENAME):
        parser.print_help()
        sys.exit(0)

    print(get_document(args.doc_id))

if __name__ == '__main__':
    main()
