# -*- coding: utf-8 -*-
from Bio import Entrez
from PyQt4 import QtGui, QtCore
from pyzotero import zotero, zotero_errors


class Query(object):
    def __init__(self):
        self.search_term = []

    def add_condition(self, condition, field, logic=''):
        for c in [condition]:
            for f in [field]:
                self.search_term.append(dict(logic=logic,
                                             field=f,
                                             condition=c))

    def get_query(self, db='Pubmed'):
        if db == 'Pubmed':
            output = [' {logic} ({condition}[{field}])'.format(**i) for i in self.search_term]
            return ''.join(output)


class Zotero(object):
    def __init__(self):
        self.zot = None
        self.lib_id = ''
        self.lib_api = ''
        self.lib_type = ''
        self.collection_choose = ''
        self.collections = []

    def connectZotero(self):
        self.zot = zotero.Zotero(library_id=self.lib_id, library_type=self.lib_type, api_key=self.lib_api)
        try:
            self.zot.key_info()
            return True
        except zotero_errors.UserNotAuthorised:
            return False

    def get_collections(self):
        self.collections = []
        for i in range(0, 5000, 50):
            tmp_colset = [i['data'] for i in self.zot.collections(limit=50, start=i)]
            print tmp_colset
            self.collections += tmp_colset
            if tmp_colset == []:
                break

    def make_collection_tree(self):
        self.collection_tree = {}
        tempcollections = self.collections[:]
        while tempcollections != []:
            rm_list = []
            for idx, val in enumerate(tempcollections):
                if not val[u'parentCollection']:
                    self.collection_tree[val[u'key']] = dict(name=val[u'name'],
                                                             parent=val[u'parentCollection'],
                                                             children=[])
                    rm_list.append(idx)
                    print val
                else:
                    try:
                        self.collection_tree[val[u'parentCollection']]['children'] += val[u'key']

                        self.collection_tree[val[u'key']] = dict(name=val[u'name'],
                                                                 parent=val[u'parentCollection'],
                                                                 children=[])
                        rm_list.append(idx)
                        # print val
                    except:

                        continue
            print rm_list, len(tempcollections), len(self.collection_tree)
            [tempcollections.pop(x) for x in sorted(rm_list, reverse=True)]

    def collections2tree(self):
        self.nodes = [TreeStructure({u'key': False, u'name': 'root'})]
        tempcollections = self.collections[:]
        while tempcollections != []:
            rm_list = []
            for idx, val in enumerate(tempcollections):
                try:
                    parent = self.nodes[self.nodes.index(val[u'parentCollection'])]
                    self.nodes.append(TreeStructure(val, parent=parent))
                    rm_list.append(idx)
                except:
                    print val

                    continue
            [tempcollections.pop(x) for x in sorted(rm_list, reverse=True)]

    def items_preparation(self, items):
        for indx, val in enumerate(items):
            items[indx][u'collections'] += [self.collection_choose]
        return items

    def send_items(self, items):
        return self.zot.create_items(items)


class TreeStructure(object):
    def __init__(self, value, parent=None):
        self.__value = value
        self.__parent = parent
        self.__children = []
        if parent is not None and not False:
            parent.add_child(self)

    def add_child(self, child):
        self.__children.append(child)

    def name(self):
        return self.__value[u'name']

    def key(self):
        return self.__value[u'key']

    def get_child(self, idx):
        return self.__children[idx]

    def child_count(self):
        return len(self.__children)

    def get_parent(self):
        return self.__parent

    def row(self):
        if self.__parent is not None:
            return self.__parent.__children.index(self)

    def log(self, tabLevel=-1):
        output = ''
        tabLevel += 1
        output += ''.join(['\t' for i in range(tabLevel)])
        output += self.name().encode('utf-8') + '\n'
        for child in self.__children:
            output += child.log(tabLevel)
        tabLevel -= 1
        output += '\n'
        return output

    def __repr__(self):
        return self.log()

    def __eq__(self, other):
        return other == self.key()


class ZoteroQt(Zotero, QtCore.QObject):
    connectionError = QtCore.pyqtSignal()
    connectionSuccess = QtCore.pyqtSignal()

    def __init__(self, parent=None):
        Zotero.__init__(self)
        QtCore.QObject.__init__(self)

    def connectZotero(self):
        response = Zotero.connectZotero(self)
        if response:
            self.connectionSuccess.emit()
        else:
            self.connectionError.emit()


class ZoteroCollections_QtTree(QtCore.QAbstractItemModel):
    def __init__(self, root, parent=None):
        QtCore.QAbstractItemModel.__init__(self, parent)
        self._root_node = root

    def parent(self, index):
        node = index.internalPointer()
        parent_node = node.get_parent()
        if parent_node == self._root_node:
            return QtCore.QModelIndex()
        return self.createIndex(parent_node.row(), 0, parent_node)

    def index(self, row, column, parent):
        if not parent.isValid():
            parent_node = self._root_node
        else:
            parent_node = parent.internalPointer()

        child_item = parent_node.get_child(row)
        if child_item:
            return self.createIndex(row, column, child_item)
        else:
            return QtCore.QModelIndex()

    def rowCount(self, parent):
        if not parent.isValid():
            parent_node = self._root_node
        else:
            parent_node = parent.internalPointer()

        return parent_node.child_count()

    def columnCount(self, parent):
        return 1

    def flags(self, index):
        return QtCore.Qt.ItemIsEnabled | QtCore.Qt.ItemIsSelectable

    def headerData(self, p_int, Qt_Orientation, int_role=None):
        return 'Groups'

    def data(self, index, role):
        if not index.isValid():
            return None
        node = index.internalPointer()
        if role == QtCore.Qt.DisplayRole:
            return node.name()


class PubMed_search(QtCore.QObject):
    changed = QtCore.pyqtSignal()

    def __init__(self, email=''):
        self.add_email(email)
        QtCore.QObject.__init__(self)

    def search(self, term, **kwargs):
        query = Entrez.esearch('pubmed', term, retmax=100000, **kwargs)
        self.search_result = Entrez.read(query)
        self.items_id = self.search_result['IdList']
        self.changed.emit()
        query.close()

    def get_results(self):
        id_list = ','.join(self.items_id)
        items = Entrez.efetch(db='pubmed', id=id_list, retmode='xml')
        self.items = Entrez.read(items)
        print self.items

    def show_results(self,start,end):
        id_list = ','.join(self.search_result['IdList'][start:end])
        items = Entrez.efetch(db='pubmed', id=id_list, retmode='xml')
        article_names = []
        for i in Entrez.parse(items):
            article_names.append( self.extract_value(i, [u'MedlineCitation', u'Article', u'ArticleTitle']) )
        return article_names

    def get_items(self,start,end,step=1):
        return self.items[start:end:]

    def add_email(self,email):
        self.email=email
        Entrez.email = email




    @staticmethod
    def isArticle(biblioitem):
        article_definitions = ['Journal Article', 'JOURNAL ARTICLE', 'Review', 'REVIEW']
        try:
            publication_types = biblioitem[u'MedlineCitation'][u'Article'][u'PublicationTypeList']
        except KeyError:
            publication_types = biblioitem[u'BookDocument'][u'PublicationType']

        if any([i in publication_types for i in article_definitions]):
            return True
        else:
            return False

    def convert_items(self):
        for i in self.items:
            if self.isArticle(i):
                self.medline2zotero(i)

    @staticmethod
    def extract_value(item, path, filter=None, sanitize_fun=unicode, dummy_return=u''):
        out = item
        try:
            while path != []:
                out = out.__getitem__(path.pop(0))



            if filter is not None:
                for i in out:
                    if i.attributes == filter:
                        return sanitize_fun(i)
            else:
                return sanitize_fun(out)
        except KeyError:
            return dummy_return

    def format_abstract(self, abstract_list):
        if type(abstract_list) is list:
            return '\n'.join([unicode(i) for i in abstract_list])
        else:
            return abstract_list
    def list_sanitize(self,l):
        if type(l)==list and len(l)==1:
            input_list=l[0]
            return [unicode(i) for i in input_list]
        elif type(l)==list and len(l)==0:
            return []
        elif type(l)==list and len(l)>1:
            raise IndexError('Unexpected list recieved: %s. Nested list of length 1 expected.'%l)
        elif type(l)==Entrez.Parser.ListElement:
            return [unicode(i) for i in l]
        else:
            raise TypeError(type(l))



    def list_sanitize_MeSH(self,l):
        if len(l)>0:
            o = [unicode(i[u'DescriptorName']) for i in l]
        else:
            o = []
        return o



    def format_date(self,date_dict):
        try:
            return date_dict[u'MedlineDate']
        except KeyError:
            result = []
            for k in [u'Year',u'Month',u'Day']:
                try:
                    result.append(date_dict[k])
                except:
                    continue
            return ' '.join(result)




    def medline2zotero(self, item):

        zotero_item = {u'DOI': self.extract_value(item, [u'PubmedData', u'ArticleIdList'], {u'IdType': u'doi'}),
                       u'itemType': u'journalArticle',
                       u'extra': u'',
                       u'seriesText': u'',
                       u'series': u'',
                       u'abstractNote': self.extract_value(item, [u'MedlineCitation', u'Article', u'Abstract',
                                                                  u'AbstractText'], sanitize_fun=self.format_abstract),
                       u'archive': u'',
                       u'title': self.extract_value(item, [u'MedlineCitation', u'Article', u'ArticleTitle']),
                       u'ISSN': self.extract_value(item, [u'MedlineCitation', u'Article', u'Journal', u'ISSN']),
                       u'relations': {},
                       u'archiveLocation': u'',
                       u'collections': [],
                       u'journalAbbreviation': self.extract_value(item, [u'MedlineCitation', u'Article', u'Journal',
                                                                         u'ISOAbbreviation']),
                       u'issue': self.extract_value(item, [u'MedlineCitation', u'Article', u'Journal', u'JournalIssue',
                                                           u'Issue']),
                       u'seriesTitle': u'',
                       u'tags': self.extract_value(item,[u'MedlineCitation', u'KeywordList'],sanitize_fun=self.list_sanitize,dummy_return=[]) +\
                                self.extract_value(item,[u'MedlineCitation', u'MeshHeadingList'],sanitize_fun=self.list_sanitize_MeSH,dummy_return=[])+\
                                self.extract_value(item,[u'MedlineCitation', u'Article',u'PublicationTypeList'],sanitize_fun=self.list_sanitize,dummy_return=[]),
                       u'accessDate': u'',
                       u'libraryCatalog': u'',
                       u'volume': self.extract_value(item, [u'MedlineCitation', u'Article', u'Journal', u'JournalIssue',
                                                            u'Volume']),
                       u'callNumber': u'',
                       u'date': self.extract_value(item, [u'MedlineCitation', u'Article', u'Journal', u'JournalIssue',
                                                          u'PubDate'], sanitize_fun=self.format_date),
                       u'pages': self.extract_value(item,
                                                    [u'MedlineCitation', u'Article', u'Pagination', u'MedlinePgn']),
                       u'language': self.extract_value(item, [u'MedlineCitation', u'Article', u'Language']),
                       u'shortTitle': u'',
                       u'rights': u'',
                       u'url': u'http://www.ncbi.nlm.nih.gov/pubmed/' + self.extract_value(item, [u'MedlineCitation',
                                                                                                  u'PMID']),
                       u'publicationTitle': self.extract_value(item,
                                                               [u'MedlineCitation', u'Article', u'Journal', u'Title']),
                       u'creators': self.extract_value(item, [u'MedlineCitation', u'Article', u'AuthorList'],
                                                       sanitize_fun=list)}

        for idx, value in enumerate(zotero_item[u'creators']):
            try:
                zotero_item[u'creators'][idx] = {u'lastName': value[u'LastName'],
                                                 u'creatorType': u'author',
                                                 u'firstName': value[u'ForeName']}
            except KeyError:
                continue

        return zotero_item






class Query_Table(QtCore.QAbstractTableModel, Query):

    def __init__(self, parent=None):
        QtCore.QAbstractTableModel.__init__(self, parent)
        Query.__init__(self)

        self.column_conditdion={0:'condition',1:'field',2:'logic'}

    def rowCount(self, parent):
        return len(self.search_term)

    def columnCount(self, parent):
        return 3

    def data(self, index, role):
        if role == QtCore.Qt.DisplayRole or role == QtCore.Qt.EditRole:
            condition = self.search_term[index.row()]
            if index.column() == 0:
                return QtCore.QString(condition['condition'])
            if index.column() == 1:
                return QtCore.QString(condition['field'])
            if index.column() == 2:
                return QtCore.QString(condition['logic'])

    def flags(self, index):
        return QtCore.Qt.ItemIsEditable | QtCore.Qt.ItemIsEnabled | QtCore.Qt.ItemIsSelectable

    def setData(self, index, value, role=QtCore.Qt.EditRole):
        if role == QtCore.Qt.EditRole:
            row = index.row()
            column = index.column()
            print value.toString()
            self.search_term[row][self.column_conditdion[column]] = str(value.toString())
            self.dataChanged.emit(index,index)
            return True
        else:
            return False

    def insertRow(self, parent=QtCore.QModelIndex(), *args, **kwargs):
        self.beginInsertRows(parent, self.rowCount(self), self.rowCount(self))
        self.add_condition(condition=kwargs['condition'], field=kwargs['field'], logic=kwargs['logic'])
        self.dataChanged.emit(parent,parent)
        self.endInsertRows()

    def removeRow(self, p_int, parent=QtCore.QModelIndex(), *args, **kwargs):
        self.beginRemoveRows(parent, p_int, p_int)
        self.search_term.pop(p_int)
        self.dataChanged.emit(parent,parent)
        self.endRemoveRows()


