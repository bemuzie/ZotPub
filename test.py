__author__ = 'denest'
import os
import sys
from PyQt4 import QtGui,uic

newwindow=os.path.join('./view/window.py')
for p,d,f in os.walk('./view/'):
    for i in f:
        extension = i.split('.')[-1]
        if extension == 'py' and i != '__init__.py':
            os.remove(os.path.join(p,i))

for p,d,f in os.walk('./view/'):
    for i in f:
        extension = i.split('.')[-1]
        print extension
        fname = i[:-len(extension)-1]
        if extension == 'ui':
            uic.compileUi(os.path.join(p,i),
                          file(os.path.join(p,fname+'.py'),'w'))


