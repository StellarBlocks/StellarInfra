# -*- coding: utf-8 -*-
"""
Created on Wed Jun 17 12:11:13 2020

@author: Jin Dou
"""

import os
import warnings
from configparser import ConfigParser,BasicInterpolation
import yaml
import re

def getUpperDir(path:str):
    out = os.path.split(path)
    if isinstance(path, CPath):
        return CPath(out[0]),out[1]
    else:
        return os.path.split(path)

def isFolderOrFile(path:str):
    '''
    not exist 0
    dir 1
    file 2
    others -1
    '''
    out = -1
    if checkExists(path):
        if os.path.isdir(path):
            out = 1
        elif os.path.isfile(path):
            out = 2
    else:
        out = 0
    return out

def checkExists(path):
    return os.path.exists(path)

def checkFolder(folderPath):
#    print(folderPath)
#    if not isinstance(folderPath,str):
#        return
    if not os.path.isdir(folderPath) and not os.path.isfile(folderPath):
        warnings.warn("path: " + folderPath + " doesn't exist, and it is created")
        os.makedirs(folderPath)

def getFileList(folder_path,extension):
    ans = [os.path.join(folder_path,file) for file in os.listdir(folder_path) if file.endswith(extension)]
    if(len(ans)==0):
        warnings.warn("getFileList's error: folder: '" + str(folder_path) + "'is empty with '" + str(extension) + "' kind of file")
        return None
    else:
        return ans
    
def getFileListAll_iter(folder_path,ext = ''):
    for dirpath, dirnames, filenames in os.walk(folder_path):
        for f in filenames:
            file_path = os.path.join(dirpath, f)
            if f.endswith(ext):
                yield file_path
            
def getFileListAll(folder_path,ext = ''):
    return list(getFileListAll_iter(folder_path,ext))
    
def getFileName(path):
    dataSetName, extension = os.path.splitext(os.path.basename(path))    
    return dataSetName,extension

def getSubFolderName(folder):
    subfolders = [f.name for f in os.scandir(folder) if f.is_dir() ]
    return subfolders


class CDirectoryConfig:
    
    def __init__(self,dir_List, confFile):
        self._dir_dict = dict()
        self._confFile = confFile
        for i in dir_List:
            self._dir_dict[i] = ''
        self._load_conf()
        self._addAttr()
        self._checkFolders()
            
    def _load_conf(self):
        conf_file = self._confFile
        config = ConfigParser(interpolation=BasicInterpolation())
        config.read(conf_file,encoding = 'utf-8')
        conf_name, ext = getFileName(conf_file)
        for dir_1 in self._dir_dict:
            self._dir_dict[dir_1] = config.get(conf_name, dir_1)
#            print(dir_1,config.get(conf_name, dir_1))
    
    def __getitem__(self,keyName):
        return self._dir_dict[keyName]
    
    def _checkFolders(self,foldersList = None):
        if foldersList != None:
            pass
        else:
            foldersList = self._dir_dict.keys()
        
        for folder in foldersList:
                checkFolder(self._dir_dict[folder])
    
    def _addAttr(self):
        for name in self._dir_dict:
            setattr(CDirectoryConfig,name,self._dir_dict[name])

#%% New Path Config Module
class CPathSection:
    def __init__(self,dicts):
        for i in dicts:
            if isinstance(dicts[i],dict):
                setattr(self,i, CPathSection(dicts[i]))
            elif isinstance(dicts[i],str):
                setattr(self,i, CPath(dicts[i]))
            else:
                setattr(self,i, dicts[i])
    
    def __getitem__(self,keyName):
        return getattr(self, keyName)

class CPath(str):
    
    def __add__(self,newPath:str):
        return CPath(super().__add__(newPath))
    
    def __truediv__(self,newPath:str):
        return CPath(super().__add__(f'/{newPath}'))
      
    
class CPathConfig:
    
    def __new__(cls,confFile:str,**kwargs):
        if confFile.endswith('.conf'):
            return super().__new__(CPathConfigPyConfig)
        elif confFile.endswith('.yaml') or confFile.endswith('.yml'):
            return super().__new__(CPathConfigYaml)
        else:
            raise ValueError("endswith .conf | .yml | .yaml")
    
    def __getitem__(self,keyName):
        return getattr(self, keyName)
    
class CYamlTagMixin:
    def __getitem__(self,keyName):
#        print(keyName)
        return self.__dict__[keyName]
    
    def __setitem__(self,keyName,val):
        self.__dict__[keyName] = val
    
    def keys(self):
        if self.__dict__.get('_cur'):
            temp = list(self.__dict__.keys())
            temp.remove('_cur')
            return temp 
        else:
            return self.__dict__.keys()
    
    def __iter__(self):
        self._cur = 0
        return self
    
    def __next__(self):
        if self._cur >= len(self.keys()):
            raise StopIteration
        else:
            temp = list(self.keys())[self._cur]
            self._cur+=1
            return temp

class CYamlFolder(yaml.YAMLObject,CYamlTagMixin):
    yaml_tag = u'!Folder'
    
    def __init__(self, value):
        self.value = value
        assert isinstance(value,str)
    
    @classmethod
    def from_yaml(cls, loader, node):
        return CYamlFolder(node.value)

    @classmethod
    def to_yaml(cls, dumper, data):
        return dumper.represent_scalar(cls.yaml_tag, data.env_var)

class CYamlConfig(yaml.YAMLObject,CYamlTagMixin):
    yaml_tag = u'!StDM'
    
class CYamlFolders(yaml.YAMLObject,CYamlTagMixin):
    yaml_tag = u'!Folders'
    
    """ Folders can only have str childs """
    
def cat(loader, node):
    seq = loader.construct_sequence(node)
    return ''.join([str(i) if not isinstance(i,CYamlFolder) else str(i.value) for i in seq ])

yaml.add_constructor('!cat', cat)

class CPathConfigYaml(CPathConfig):
    def __init__(self,confFile,checkFolders = True):
        self._doc = self._load(confFile)
        assert isinstance(self._doc, CYamlConfig)
        self.YamlNodes = {}
        self.YamlNodes.update(self._doc.__dict__)
        
        self.processFolder(self.YamlNodes)
        self.parseRef(self.YamlNodes)
        self.setAttr(self.YamlNodes)
        
        if checkFolder:
            self.checkFolders(self.YamlNodes)
#        self.__dict__.update(self.YamlNodes)
#        self.__dict__.update(self.YamlNodes) 
    
    def _load(self,file):
        with open(file, 'r') as stream:
            try:
                return yaml.load(stream,Loader=yaml.FullLoader)
            except yaml.YAMLError as exc:
                raise
                
    def checkFolders(self,Dict):
        for idx,i in enumerate(Dict):
            if isinstance(Dict[i],CYamlFolders):
#                print(Dict[i].__dict__)
                for j in Dict[i].keys():
                    checkFolder(Dict[i][j])
            else:
                if getattr(Dict[i],'__dict__',None):
                    self.checkFolders(Dict[i].__dict__)
        
                
    def processFolder(self,Dict):
#        print(Dict)
        for idx,i in enumerate(Dict):
            if isinstance(Dict[i],CYamlFolder):
                Dict[i] = Dict[i].value
                checkFolder(Dict[i])
            else:
                if getattr(Dict[i],'keys',None):
                    self.processFolder(Dict[i])
    
        
    def setAttr(self,dicts):
        for i in dicts:
            if isinstance(dicts[i],dict):
                setattr(self,i, CPathSection(dicts[i]))
            elif isinstance(dicts[i],str):
                setattr(self,i, CPath(dicts[i]))
            else:
                setattr(self,i, dicts[i])
    
    def replFunc(self,a):
        matched = a.groups()[0]
        attrs = matched.split('.')
        oAttr = self.YamlNodes
        for i in attrs:
#            print(oAttr)
            oAttr = oAttr[i]
#        print(oAttr)
        return oAttr    
       
    def parseRef(self,dicts):
#        print(dicts)
        for i in dicts:
            if isinstance(dicts[i],str):
#                print(dicts[i])
                temp = re.sub(r"\${([^}]*)}", self.replFunc,dicts[i] , count=0, flags=0)
                dicts[i] = temp
#                print(dicts[i],temp)
            else:
                self.parseRef(dicts[i])
        

class CPathConfigPyConfig(CPathConfig):
    def __init__(self,confFile,sectionList:list = None, checkFolders = True):
        self._dict = dict()
        self._confFile = confFile
        if not checkExists(confFile):
            raise ValueError("config file doesn't exist")
        self._load_conf()
        self._addAttr()
        if checkFolders:
            self._checkFolders()
            
    def _load_conf(self):
        conf_file = self._confFile
        config = ConfigParser(interpolation=BasicInterpolation())
        config.optionxform = str #disable the default changing to lowercase
        config.read(conf_file,encoding = 'utf-8')
        sections = config.sections()
        for sec in sections:
            self._dict[sec] = dict()
        for sec in sections:
            for item in config[sec]:
                self._dict[sec][item] = config.get(sec,item)
                # print(config.get(sec,item))
    
    
    def _checkFolders(self):

        for sec in self._dict:
            foldersList = self._dict[sec].keys()
            for folder in foldersList:
                path = self._dict[sec][folder]
                _,ext = getFileName(path)
                flag = isFolderOrFile(path)
                if flag == 1:
                    checkFolder(path)
                elif flag == 0:
                    if ext == '':
                        checkFolder(path)
                    else:
                        folder,ext = getUpperDir(path)
                        checkFolder(folder)
                else:
                    assert flag != -1
    
    def _addAttr(self):
        for sec in self._dict:
            setattr(self,sec,CPathSection({}))
            for item in self._dict[sec]:
                setattr(getattr(self, sec),item,CPath(self._dict[sec][item]))
                
    def checkSectionFolders(self,secName):
        sec = secName
        foldersList = self._dict[sec].keys()
        for folder in foldersList:
            path = self._dict[sec][folder]
            _,ext = getFileName(path)
            flag = isFolderOrFile(path)
            if flag == 1:
                checkFolder(path)
            elif flag == 0:
                if ext == '':
                    checkFolder(path)
                else:
                    folder,ext = getUpperDir(path)
                    checkFolder(folder)
            else:
                assert flag != -1
