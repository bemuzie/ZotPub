# -*- coding: utf-8 -*-
__author__ = 'denest'
import ConfigParser
import os

from PyQt4 import QtCore
from PyQt4 import QtGui

from view import window, properties_zotero, properties_pubmed
from model import main


class CurrentQt(QtGui.QMainWindow, window.Ui_MainWindow):
    def __init__(self, parent=None):
        QtGui.QMainWindow.__init__(self, parent)
        self.gui = window.Ui_MainWindow()
        self.gui.setupUi(self)

        self.query_model = main.Query_Table()
        self.search_model = main.PubMed_search('')
        self.zotero_model = main.ZoteroQt()

        self.gui.tableView.setModel(self.query_model)

        self.query_model.dataChanged.connect(self.refresh_generated_term)
        self.search_model.changed.connect(self.refresh_search_info)



        # ----------BUTTONS----------------------------------
        self.gui.pushButton_2.clicked.connect(self.search)
        self.gui.action_Zotero.triggered.connect(self.open_zotero_preferences)
        self.gui.action_PubMed.triggered.connect(self.open_pubmed_preferences)
        self.gui.pushButton.clicked.connect(self.send_to_zotero)
        self.gui.pushButton_4.clicked.connect(self.add_search_condition)

        #----------KEYBOARD---------------------------------------

        # ----------DEFAULTS----------------------------------
        self.load_defaults()


    def keyPressEvent(self, QKeyEvent):
        if QKeyEvent.key() == QtCore.Qt.Key_Delete:
            self.delete_conditions()
        else:
            QKeyEvent.accept()

    def closeEvent(self, QCloseEvent):
        self.save_defaults()

        QCloseEvent.accept()


    def save_defaults(self):
        cfg = ConfigParser.RawConfigParser()
        cfg.add_section('PubMed')
        cfg.set('PubMed','email',self.search_model.email)
        cfg.add_section('Zotero')
        cfg.set('Zotero','lib_id', self.zotero_model.lib_id)
        cfg.set('Zotero','lib_api', self.zotero_model.lib_api)
        cfg.set('Zotero','lib_type', self.zotero_model.lib_type)
        cfg.set('Zotero','collection', self.zotero_model.collection_choose)

        with open('default.cfg','wb') as configfile:
            cfg.write(configfile)

    def load_defaults(self):
        if os.path.isfile('default.cfg'):
            cfg = ConfigParser.RawConfigParser()
            cfg.read('default.cfg')
            self.search_model.add_email(cfg.get('PubMed','email'))
            self.zotero_model.lib_id = cfg.get('Zotero','lib_id')
            self.zotero_model.lib_api = cfg.get('Zotero','lib_api')
            self.zotero_model.lib_type = cfg.get('Zotero','lib_type')
            self.zotero_model.collection_choose = cfg.get('Zotero','collection')


    def delete_conditions(self):
        for i in sorted(self.gui.tableView.selectedIndexes(), reverse=True):
            print i
            self.query_model.removeRow(i.row())

    def add_search_condition(self):
        print str(self.gui.comboBox_2.currentText())
        condition = dict(condition=str(self.gui.lineEdit_2.text()),
                         field=str(self.gui.comboBox_2.currentText()),
                         logic=str(self.gui.comboBox.currentText()))
        self.query_model.insertRow(**condition)


    def open_zotero_preferences(self):
        zotpref = PreferencesZotero(self)
        zotpref.show()

    def open_pubmed_preferences(self):
        pubmed_pref = PreferencesPubmed(self)
        pubmed_pref.show()

    def _create_zotero_items(self,items):
        prepared_dicts = self.zotero_model.items_preparation(items)
        response = self.zotero_model.send_items(prepared_dicts)
        print response


    def send_to_zotero(self):
        print isinstance(self.zotero_model, main.ZoteroQt)
        if isinstance(self.zotero_model, main.ZoteroQt):
            self.search_model.get_results()

            list_of_items = []
            counter = 0
            for i in self.search_model.items:

                if self.search_model.isArticle(i):
                    zot_dic = self.search_model.medline2zotero(i)
                    list_of_items.append(zot_dic)
                    counter += 1

                if counter==49:
                    counter = 0
                    self._create_zotero_items(list_of_items)
                    list_of_items = []
            self._create_zotero_items(list_of_items)


        else:
            error_dialog = QtGui.QErrorMessage(self)
            error_dialog.showMessage(QtCore.QString(u'Настройте соединение с Zotero'))
            error_dialog.exec_()

    def refresh_generated_term(self):
        print 111
        self.gui.plainTextEdit.setPlainText(self.query_model.get_query())

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
        self.zot_model = parent.zotero_model
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
        self.gui.lineEdit.setText( QtCore.QString( self.parent.zotero_model.lib_id or '' ))
        self.gui.lineEdit_2.setText( QtCore.QString(self.parent.zotero_model.lib_api or ''))

        if self.parent.zotero_model.lib_type == 'user':
            self.gui.radioButton.toggle()
        elif self.parent.zotero_model.lib_type == 'group':
            self.gui.radioButton_2.toggle()
        self.set_library_type()


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

class PreferencesPubmed(QtGui.QDialog, properties_pubmed.Ui_Dialog):

    def __init__(self, parent=None):
        super(PreferencesPubmed, self).__init__(parent)
        self.gui = properties_pubmed.Ui_Dialog()
        self.gui.setupUi(self)

        self.parent = parent

        # -------BUTTONS-------------------------
        self.gui.pushButton_2.clicked.connect(self.close)
        self.gui.pushButton.clicked.connect(self.save_connection)
        #-------DEFAULTS--------------------------
        self.gui.lineEdit.setText(QtCore.QString(self.parent.search_model.email))

    def save_connection(self):
        self.parent.search_model.add_email(str(self.gui.lineEdit.text()))
        self.close()
