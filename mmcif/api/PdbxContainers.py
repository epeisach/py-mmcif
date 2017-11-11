##
#
# File:     PdbxContainers.py
# Original: 02-Feb-2009   jdw
#
# Update:
#   23-Mar-2011   jdw Added method to rename attributes in category containers.
#   05-Apr-2011   jdw Change cif writer to select double quoting as preferred
#                     quoting style where possible.
#   16-Jan-2012   jdw Create base class for DataCategory class
#   22-Mar-2012   jdw when append attributes to existing categories update
#                     existing rows with placeholder null values.
#    2-Sep-2012   jdw add option to avoid embedded quoting that might
#                     confuse simple parsers.
#    4-Nov-2012   jdw extend static methods in CifName class
#   14-Nov-2012   jdw refactoring
#   28-Jun-2013   jdw expose remove method
#   01-Aug-2017   jdw migrate portions to public repo
##
"""

A collection of container classes supporting the PDBx/mmCIF storage model.

A base container class is defined which supports common features of
data and definition containers.   PDBx data files are organized in
sections called data blocks which are mapped to data containers.
PDBx dictionaries contain definition sections and data sections
which are mapped to definition and data containes respectively.

Data in both PDBx data files and dictionaries are organized in
data categories. In the PDBx syntax individual items or data
identified by labels of the form '_categoryName.attributeName'.
The terms category and attribute in PDBx jargon are analogous
table and column in relational data model, or class and attribute
in an object oriented data model.

The DataCategory class provides base storage container for instance
data and definition meta data.

"""
from __future__ import absolute_import

__docformat__ = "restructuredtext en"
__author__ = "John Westbrook"
__email__ = "john.westbrook@rcsb.org"
__license__ = "Apache 2.0"



import sys

class CifName(object):
    ''' Class of utilities for CIF-style data names -
    '''

    def __init__(self):
        pass

    @staticmethod
    def categoryPart(name):
        tname = ""
        try:
            if name.startswith("_"):
                tname = name[1:]
            else:
                tname = name

            i = tname.find(".")
            if i == -1:
                return tname
            else:
                return tname[:i]
        except:
            return tname

    @staticmethod
    def attributePart(name):
        try:
            i = name.find(".")
            if i == -1:
                return None
            else:
                return name[i + 1:]
        except:
            return None

    @staticmethod
    def itemName(categoryName, attributeName):
        try:
            return '_' + str(categoryName) + '.' + str(attributeName)
        except:
            return None


class ContainerBase(object):
    ''' Container base class for data and definition objects.
    '''

    def __init__(self, name):
        # The enclosing scope of the data container (e.g. data_/save_)
        self.__name = name
        # List of category names within this container -
        self.__objNameList = []
        # dictionary of DataCategory objects keyed by category name.
        self.__objCatalog = {}
        self.__type = None

    def getType(self):
        return self.__type

    def setType(self, type):
        self.__type = type

    def getName(self):
        return self.__name

    def setName(self, name):
        self.__name = name

    def exists(self, name):
        if name in self.__objCatalog:
            return True
        else:
            return False

    def getObj(self, name):
        if name in self.__objCatalog:
            return self.__objCatalog[name]
        else:
            return None

    def getObjNameList(self):
        return self.__objNameList

    def append(self, obj):
        """ Add the input object to the current object catalog. An existing object
            of the same name will be overwritten.
        """
        if obj.getName() is not None:
            if obj.getName() not in self.__objCatalog:
                # self.__objNameList is keeping track of object order here --
                self.__objNameList.append(obj.getName())
            self.__objCatalog[obj.getName()] = obj

    def replace(self, obj):
        """ Replace an existing object with the input object
        """
        if ((obj.getName() is not None) and (obj.getName() in self.__objCatalog)):
            self.__objCatalog[obj.getName()] = obj

    def printIt(self, fh=sys.stdout, type="brief"):
        fh.write("+ %s container: %30s contains %4d categories\n" %
                 (self.getType(), self.getName(), len(self.__objNameList)))
        for nm in self.__objNameList:
            fh.write("--------------------------------------------\n")
            fh.write("Data category: %s\n" % nm)
            if type == 'brief':
                self.__objCatalog[nm].printIt(fh)
            else:
                self.__objCatalog[nm].dumpIt(fh)

    def rename(self, curName, newName):
        """ Change the name of an object in place -
        """
        try:
            i = self.__objNameList.index(curName)
            self.__objNameList[i] = newName
            self.__objCatalog[newName] = self.__objCatalog[curName]
            self.__objCatalog[newName].setName(newName)
            return True
        except:
            return False

    def remove(self, curName):
        """ Revmove object by name.  Return True on success or False otherwise.
        """
        try:
            if curName in self.__objCatalog:
                del self.__objCatalog[curName]
                i = self.__objNameList.index(curName)
                del self.__objNameList[i]
                return True
            else:
                return False
        except:
            pass

        return False


class DefinitionContainer(ContainerBase):

    def __init__(self, name):
        super(DefinitionContainer, self).__init__(name)
        self.setType('definition')
        self.__globalFlag = False

    def isCategory(self):
        if self.exists('category'):
            return True
        return False

    def isAttribute(self):
        if self.exists('item'):
            return True
        return False

    def getGlobal(self):
        return self.__globalFlag

    def printIt(self, fh=sys.stdout, type="brief"):
        fh.write("Definition container: %30s contains %4d categories\n" %
                 (self.getName(), len(self.getObjNameList())))
        if self.isCategory():
            fh.write("Definition type: category\n")
        elif self.isAttribute():
            fh.write("Definition type: item\n")
        else:
            fh.write("Definition type: undefined\n")

        for nm in self.getObjNameList():
            fh.write("--------------------------------------------\n")
            fh.write("Definition category: %s\n" % nm)
            if type == 'brief':
                self.getObj(nm).printIt(fh)
            else:
                self.getObj(nm).dumpId(fh)


class DataContainer(ContainerBase):
    ''' Container class for DataCategory objects.
    '''

    def __init__(self, name):
        super(DataContainer, self).__init__(name)
        self.setType('data')
        self.__globalFlag = False

    def invokeDataBlockMethod(self, type, method, db):
        self.__currentRow = 1
        exec(method.getInline(), globals(), locals())

    def setGlobal(self):
        self.__globalFlag = True

    def getGlobal(self):
        return self.__globalFlag


class SaveFameContainer(ContainerBase):

    def __init__(self, name):
        super(DefinitionContainer, self).__init__(name)
        self.setType('definition')