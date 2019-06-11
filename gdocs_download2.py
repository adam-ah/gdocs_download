#!/usr/bin/env python
"""
Recursively extracts the text from a Google Doc.
"""
from __future__ import print_function

import argparse
import os
import sys

from apiclient import discovery
from httplib2 import Http
from oauth2client import client
from oauth2client import file as oauth2clientfile
from oauth2client import tools

reload(sys)
sys.setdefaultencoding('utf-8')

SCOPES = 'https://www.googleapis.com/auth/documents.readonly'
DISCOVERY_DOC = 'https://docs.googleapis.com/$discovery/rest?version=v1'

BASE_DIR = os.path.dirname(os.path.realpath(__file__))
CREDENTIALS_FILENAME = os.path.join(BASE_DIR, 'credentials.json')
TOKEN_FILENAME = os.path.join(BASE_DIR, 'token.json')

def get_credentials():
    """Gets valid user credentials from storage.

    If nothing has been stored, or if the stored credentials are invalid,
    the OAuth 2.0 flow is completed to obtain the new credentials.

    Returns:
        Credentials, the obtained credential.
    """
    store = oauth2clientfile.Storage(TOKEN_FILENAME)
    credentials = store.get()

    if not credentials or credentials.invalid:
        flow = client.flow_from_clientsecrets(CREDENTIALS_FILENAME, SCOPES)
        credentials = tools.run_flow(flow, store)
    return credentials

def read_paragraph_element(element):
    """Returns the text in the given ParagraphElement.

        Args:
            element: a ParagraphElement from a Google Doc.
    """
    text_run = element.get('textRun')
    if not text_run or text_run.get('suggestedDeletionIds'):
        return ''
    return text_run.get('content')


def read_strucutural_elements(elements):
    """Recurses through a list of Structural Elements to read a document's text where text may be
        in nested elements.

        Args:
            elements: a list of Structural Elements.
    """
    text = ''
    for value in elements:
        if 'paragraph' in value:
            elements = value.get('paragraph').get('elements')
            for elem in elements:
                text += read_paragraph_element(elem)
        elif 'table' in value:
            # The text in table cells are in nested Structural Elements and tables may be
            # nested.
            table = value.get('table')
            for row in table.get('tableRows'):
                cells = row.get('tableCells')
                for cell in cells:
                    text += read_strucutural_elements(cell.get('content'))
        elif 'tableOfContents' in value:
            # The text in the TOC is also in a Structural Element.
            toc = value.get('tableOfContents')
            text += read_strucutural_elements(toc.get('content'))
    return text


def get_document(document_id):
    """Uses the Docs API to print out the text of a document."""
    credentials = get_credentials()
    http = credentials.authorize(Http())
    docs_service = discovery.build(
        'docs', 'v1', http=http, discoveryServiceUrl=DISCOVERY_DOC)
    doc = docs_service.documents().get(documentId=document_id).execute()
    doc_content = doc.get('body').get('content')
    # print(doc_content)
    return read_strucutural_elements(doc_content)

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
