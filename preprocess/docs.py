#!/usr/bin/env python

import sys
import os
import xml.dom.minidom

curDir = os.path.dirname(__file__)
dataDir = os.path.join(os.path.dirname(curDir), 'data')
__rawDocFile = 'NCT03106012.xml'

# the class for document datatype (document in PM)
class Document(object):
    def __init__(self, *args, **kwargs):
        self.nct_id = kwargs['nct_id']
        self.brief_title = kwargs['brief_title']
        self.official_title = kwargs['official_title']
        self.brief_summary = kwargs['brief_summary']
        self.study_type = kwargs['study_type']
        self.primary_purpose = kwargs['primary_purpose']
        self.gender = kwargs['gender']
        self.minimum_age = kwargs['minimum_age']
        self.maximum_age = kwargs['maximum_age']
        self.healthy_volunteers = kwargs['healthy_volunteers']
        self.textblock = kwargs['textblock']
        self.mesh_term = kwargs['mesh_term']
        self.condition = kwargs['condition']
        self.keyword = kwargs['keyword']
        
    def toJsonObj(self):
        '''
            Return the json object (python dict) of this topic instance which may be used in elasticsearch module.
        '''
        jsonObj = {"nct_id": self.nct_id, "brief_title": self.brief_title, "official_title": self.official_title,
                "brief_summary":self.brief_summary, "study_type":self.study_type,
                "primary_purpose":self.primary_purpose, "gender":self.gender, "minimum_age":self.minimum_age,
                "maximum_age":self.maximum_age, "healthy_volunteers":self.healthy_volunteers, "textblock" : self.textblock,
                "mesh_term" : self.mesh_term, "condition" : self.condition, "keyword":self.keyword}
        # jsonObj = {"nct_id": self.nct_id, "brief_title": self.brief_title, "official_title": self.official_title,
        #         "brief_summary":self.brief_summary}
        return jsonObj
    
    def getDocId(self):
        return self.nct_id

def loadDoc(loadFile=__rawDocFile):
    loadPath = os.path.join(dataDir, loadFile)
    DOMTree = xml.dom.minidom.parse(loadPath)
    rootNode = DOMTree.documentElement
    # rank = rootNode.getAttribute('rank')
    # get important doc node
    nct_id = str(rootNode.getElementsByTagName('nct_id')[0].firstChild.nodeValue)
    
    # get brief_title
    if len(rootNode.getElementsByTagName('brief_title')) == 0:
        brief_title = ''
    else:
        brief_title = str(rootNode.getElementsByTagName('brief_title')[0].firstChild.nodeValue)
    # get official_title
    if len(rootNode.getElementsByTagName('official_title')) == 0:
        official_title = ''
    else:
        official_title = str(rootNode.getElementsByTagName('official_title')[0].firstChild.nodeValue)
    
    # brief_summary
    if len(rootNode.getElementsByTagName('brief_summary')) == 0:
        brief_summary = ''
    else:
        brief_summary = str(rootNode.getElementsByTagName('textblock')[0].firstChild.nodeValue)
    
    if len(rootNode.getElementsByTagName('study_type')) == 0:
        study_type = ''
    else:
        study_type = str(rootNode.getElementsByTagName('study_type')[0].firstChild.nodeValue) #Interventional or others
    
    if len(rootNode.getElementsByTagName('primary_purpose')) == 0:
        primary_purpose = ''
    else:
        primary_purpose = str(rootNode.getElementsByTagName('primary_purpose')[0].firstChild.nodeValue)
    
    if len(rootNode.getElementsByTagName('gender')) == 0:
        gender = ''
    else:
        gender = str(rootNode.getElementsByTagName('gender')[0].firstChild.nodeValue)
    
    if len(rootNode.getElementsByTagName('minimum_age')) == 0:
        minimum_age = 0
    elif str(rootNode.getElementsByTagName('minimum_age')[0].firstChild.nodeValue).split(' ')[0].isdigit():
        minimum_age = int(str(rootNode.getElementsByTagName('minimum_age')[0].firstChild.nodeValue).split(' ')[0])
    else:
        minimum_age = 0
    
    if len(rootNode.getElementsByTagName('maximum_age')) == 0:
        maximum_age = 0
    elif str(rootNode.getElementsByTagName('maximum_age')[0].firstChild.nodeValue).split(' ')[0].isdigit():
        maximum_age = int(str(rootNode.getElementsByTagName('maximum_age')[0].firstChild.nodeValue).split(' ')[0])
    else:
        maximum_age = 0
    
    if len(rootNode.getElementsByTagName('healthy_volunteers')) == 0:
        healthy_volunteers = ''
    else:
        healthy_volunteers = str(rootNode.getElementsByTagName('healthy_volunteers')[0].firstChild.nodeValue)
    # mesh_term = str(rootNode.getElementsByTagName('mesh_term')[0].firstChild)
    
    # textblock consist of detail_description,brifsummry, critira
    textblockList = rootNode.getElementsByTagName('textblock')
    text = []
    for t in textblockList:
        text.append(t.childNodes[0].data)
    textblock = str('\n'.join(text))
    # detailed_description = str(rootNode.getElementsByTagName('detailed_description')[0].getElementsByTagName('textblock')[0].childNodes[0].data)


    # mesh_term
    mesh_term_list = rootNode.getElementsByTagName('mesh_term')
    meshTerm = []
    for meshterm in mesh_term_list:
        meshTerm.append(meshterm.childNodes[0].data)
    mesh_term = str(','.join(meshTerm))

    # # condition
    condition_list = rootNode.getElementsByTagName('condition')
    cond = []
    for con in condition_list:
        cond.append(con.childNodes[0].data)
    condition = str(','.join(cond))

    # keyword ,some document may contain this field
    keywordList = rootNode.getElementsByTagName('keyword')
    key = []
    for k in keywordList:
        key.append(k.childNodes[0].data)
    keyword = str(','.join(key))

    docs = Document(nct_id=nct_id, brief_title=brief_title, official_title=official_title, brief_summary=brief_summary, study_type=study_type, 
                    primary_purpose=primary_purpose, gender=gender, minimum_age=minimum_age, maximum_age=maximum_age,
                    healthy_volunteers=healthy_volunteers, textblock=textblock, mesh_term=mesh_term, condition=condition, keyword=keyword)
    return docs