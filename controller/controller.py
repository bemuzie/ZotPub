# -*- coding: utf-8 -*-
__author__ = 'denest'
from PyQt4 import QtCore
from PyQt4 import QtGui

from view import window, properties_zotero
from model import main


class CurrentQt(QtGui.QMainWindow, window.Ui_MainWindow):
    def __init__(self, parent=None):
        QtGui.QMainWindow.__init__(self, parent)
        self.gui = window.Ui_MainWindow()
        self.gui.setupUi(self)

        self.query_model = main.Query_Table()
        self.search_model = main.PubMed_search('cireto@gmail.com')
        self.zotero_model = None

        self.gui.tableView.setModel(self.query_model)

        self.gui.tableView.model().dataChanged.connect(self.refresh_generated_term)
        self.search_model.changed.connect(self.refresh_search_info)

        # ----------BUTTONS----------------------------------
        self.gui.pushButton_2.clicked.connect(self.search)
        self.gui.action_Zotero.triggered.connect(self.open_zotero_preferences)
        self.gui.pushButton.clicked.connect(self.send_to_zotero)

        # ----------DEFAULTS----------------------------------

    def open_zotero_preferences(self):
        zotpref = PreferencesZotero(self)
        zotpref.show()

    def send_to_zotero(self):
        #todo. make it asynchronous
        if isinstance(self.zotero_model, main.ZoteroQt):
            self.search_model.get_results()
            for i in self.search_model.items:
                if self.search_model.isArticle(i):
                    zot_dic = self.search_model.medline2zotero(i)
                    prepared_dicts = self.zotero_model.items_preparation([zot_dic, ])
                    response = self.zotero_model.send_items(prepared_dicts)
                    print response
        else:
            error_dialog = QtGui.QErrorMessage(self)
            error_dialog.showMessage(QtCore.QString(u'Настройте соединение с Zotero'))
            error_dialog.exec_()

    def refresh_generated_term(self):
        self.gui.plainTextEdit.setPlainText(self.tableView.get_query())

    def search(self):

        esearch_kwargs = dict(mindate=self.gui.dateEdit.date(),
                              maxdate=self.gui.dateEdit_2.date())
        print esearch_kwargs
        esearch_kwargs = dict([(k, str(i.toString('yyyy/MM/dd'))) for k, i in esearch_kwargs.items()])
        print esearch_kwargs

        search_term = str(self.gui.plainTextEdit.toPlainText())
        self.search_model.search(search_term,
                                 **esearch_kwargs)

    def refresh_search_info(self):
        print self.search_model.search_result['Count']
        self.gui.lineEdit.setText(self.search_model.search_result['Count'])


class PreferencesZotero(QtGui.QDialog, properties_zotero.Ui_Dialog):
    def __init__(self, parent=None):
        super(PreferencesZotero, self).__init__(parent)
        self.gui = properties_zotero.Ui_Dialog()
        self.gui.setupUi(self)
        self.zot_model = main.ZoteroQt()
        self.parent = parent

        self.zot_model.connectionError.connect(self.connectionErrorMsg)
        self.zot_model.connectionSuccess.connect(self.get_collections)

        self.gui.treeView.clicked.connect(self.choose_collection)

        # -------BUTTONS-------------------------
        self.gui.pushButton.clicked.connect(self.close)
        self.gui.pushButton_3.clicked.connect(self.connect_to_library)
        self.gui.pushButton_2.clicked.connect(self.save_connection)
        # -----------RADIOBUTTONS------------------------------
        self.gui.radioButton.toggled.connect(self.set_library_type)
        self.gui.radioButton_2.toggled.connect(self.set_library_type)
        # -------DEFAULTS-------------------------

    def set_library_type(self):
        for k, v in {'user': self.gui.radioButton,
                     'group': self.gui.radioButton_2}.items():
            if v.isChecked():
                self.zot_model.lib_type = k

    def choose_collection(self, index):
        collection_item = index.internalPointer()
        self.zot_model.collection_choose = collection_item.key()
        print collection_item.key()

    def get_collections(self):
        self.zot_model.get_collections()
        self.zot_model.collections2tree()
        self.zotero_tree_model = main.ZoteroCollections_QtTree(self.zot_model.nodes[0])
        self.gui.treeView.setModel(self.zotero_tree_model)

    def connectionErrorMsg(self):
        error_dialog = QtGui.QErrorMessage(self)
        error_dialog.showMessage(QtCore.QString(u'Соединение не удалось'))
        error_dialog.exec_()

    def connect_to_library(self):
        self.zot_model.lib_id = str(self.gui.lineEdit.text())
        self.zot_model.lib_api = str(self.gui.lineEdit_2.text())
        self.zot_model.connectZotero()

    def save_connection(self):
        self.parent.zotero_model = self.zot_model
        self.close()
