from model import main
import ConfigParser
import os

search_model = main.PubMed_search('')
zotero_model = main.ZoteroQt()


cfg = ConfigParser.RawConfigParser()
cfg.read('../default.cfg')
search_model.add_email(cfg.get('PubMed','email'))
zotero_model.lib_id = cfg.get('Zotero','lib_id')
zotero_model.lib_api = cfg.get('Zotero','lib_api')
zotero_model.lib_type = cfg.get('Zotero','lib_type')
zotero_model.collection_choose = cfg.get('Zotero','collection')

search_model.items_id = ['24809235']
search_model.get_results()
print search_model.isArticle(search_model.items[0])
a = search_model.medline2zotero(search_model.items[0])
print a
"""
print [i[u'MedlineCitation'][u'Article'][u'PublicationTypeList'] for i in search_model.items]
def list_sanitize(l):
    return [unicode(i) for i in l]

def list_sanitize_MeSH(l):
    return [unicode(i[u'DescriptorName']) for i in l]


for i in search_model.items:
    o = search_model.extract_value(i,[u'MedlineCitation', u'KeywordList'],sanitize_fun=list_sanitize,dummy_return=[]) +\
        search_model.extract_value(i,[u'MedlineCitation', u'MeshHeadingList'],sanitize_fun=list_sanitize_MeSH,dummy_return=[])+\
        search_model.extract_value(i,[u'MedlineCitation', u'Article',u'PublicationTypeList'],sanitize_fun=list_sanitize,dummy_return=[])
    print search_model.medline2zotero(i)

"""