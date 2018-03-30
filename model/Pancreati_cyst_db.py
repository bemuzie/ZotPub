__author__ = 'denest'
from pyzotero import zotero, zotero_errors

credentials = 'defaults.cfg'

#Connect to Zotero library

# You should choose name of collection or its ID if name isnt unique
COLLECTION_NAME = 'CysticLesions'
COLLECTION_ID = 'I3J8BP4Q'
lib_id = '786748'
lib_api = 'mhiIxCfyi2SgW6KI0C8ZrMVh'
lib_type = 'user'



zot = zotero.Zotero(library_id=lib_id, library_type=lib_type, api_key=lib_api)

#

collection = zot.collection(COLLECTION_ID)


def get_collection_list(collection_id):
    out = [zot.collection(collection_id),]
    subcollections = zot.collections_sub(collection_id)
    if subcollections:
        for i in subcollections:
            out2 = get_collection_list(i[u'key'])
            out += out2
        return out
    else:
        return out

collections =  get_collection_list(COLLECTION_ID)

items = []
for i in collections:
    items += zot.collection_items(i[u'key'])

print [i[u'data'][u'name'] for i in collections]


FIELDS = [u'title',u'date',u'tags']

def extract_fields(fields, item):
    return dict([[i,item[i]] for i in fields])

print [extract_fields(FIELDS,i['data']) for i in items if i[u'data'][u'itemType']==u'journalArticle']
