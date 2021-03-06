#!/usr/bin/env python

# use boost(get from train module) to search and get a rank of documents
import sys
import os
curDir = os.path.dirname(__file__)
parentDir = os.path.dirname(curDir)
sys.path.append(parentDir)
from preprocess import topics,docs, rankingDataset
from elasticsearch import Elasticsearch
import requests
from train import mp, word2vec
import math, numpy

curDir = os.path.dirname(os.path.abspath(__file__)) #this way, right
parentDir = os.path.dirname(curDir)
dataDir = os.path.join(parentDir, 'data')

# connect to es ser ver
es = Elasticsearch([{'host':'localhost', 'port' : 9200}])
# test connection
if requests.get(r'http://localhost:9200').status_code != 200:
    raise RuntimeError('connection failure')

bm25Index = "clinicaltrials_bm25"
tfidfIndex = "clinicaltrials_tfidf"
rawtopics = topics.loadRawTopics()

def baseBody(queryTopicId):
    disease = ','.join(rawtopics[queryTopicId].getDiseaseList())
    gene = ','.join(rawtopics[queryTopicId].getGeneList())
    other = rawtopics[queryTopicId].getOther()
    bBody = {
            "query" : {
                "bool" : {
                    "must" : [
                        {
                            "multi_match" : {
                                "query" : disease,
                                "fields" : ["brief_title^2", 
                                            "official_title", 
                                            "textblock", "mesh_term", "condition", "keyword"],
                                "tie_breaker" : 0.3,
                                "boost" : 1.8
                            }
                        },
                        {
                            "multi_match" : {
                            "query" : gene,
                            "fields" : ["brief_title^2", 
                                            "official_title", 
                                            "textblock", "mesh_term", "condition", "keyword"],
                            "tie_breaker" : 0.3,
                            # "boost" : 1.5
                            }
                        }
                    ],
                    "should" : [
                        {
                            "term" : {
                                "textblock" : disease
                            }
                        },
                        {
                             "term" : {
                                "keyword" : disease
                            }
                        }
                    ]
                }
            }
        }
    return bBody

def queryBody(queryTopicId, topicBoostList, docBoostList):
    disease = ','.join(rawtopics[queryTopicId].getDiseaseList())
    gene = ','.join(rawtopics[queryTopicId].getGeneList())
    other = rawtopics[queryTopicId].getOther()
    body = {
        "query" : {
            "bool" : {
                "should" : [
                    {
                        "multi_match" : {
                            "query" : disease,
                            "fields" : ["brief_title"+"^"+str(docBoostList[0]), 
                                        "official_title"+"^"+str(docBoostList[1]), 
                                        "textblock"+"^"+str(docBoostList[2]),
                                        "mesh_term"+"^"+str(docBoostList[3]),
                                        "condition"+"^"+str(docBoostList[4]),
                                        "keyword"+"^"+str(docBoostList[5])],
                            # "tie_breaker" : 0.3,
                            "boost" : topicBoostList[0]
                        }
                    },
                    {
                            "multi_match" : {
                            "query" : gene,
                            "fields" : ["brief_title"+"^"+str(docBoostList[6]), 
                                        "official_title"+"^"+str(docBoostList[7]), 
                                        "textblock"+"^"+str(docBoostList[8]),
                                        "mesh_term"+"^"+str(docBoostList[9]),
                                        "condition"+"^"+str(docBoostList[10]),
                                        "keyword"+"^"+str(docBoostList[11])],
                            # "tie_breaker" : 0.3,
                            "boost" : topicBoostList[1]
                        }
                    }
                ]
            }
        }
    }
    return body

# return a dict, can get id in "_id", and get score in "_score"
def mySearch(index, topicId, topicBoostList, docBoostList):
    result = es.search(index = index, doc_type='trial', body=baseBody(topicId), size=500)['hits']['hits']
    return result

# for a query topicId, get all result :{docID：sorce}
def getResultList(topicId, method, topicBoostList, docBoostList, methodBoost):
    resDic = {}
    Results = mySearch(method, topicId, topicBoostList, docBoostList)
    for hit in Results:
        res = {hit["_id"] : hit["_score"]*methodBoost}
        resDic.update(res)
    return resDic

def getBaseResultList(topicId, whichIndex):
    resDic = []
    Results = es.search(index = whichIndex, doc_type='trial', body=baseBody(topicId), size=500)['hits']['hits']
    for hit in Results:
        res = [hit["_id"] , hit["_score"]]
        resDic.append(res)
    return resDic

def relu(num):
    n = 0
    if num < 0:
        n = 0
    else:
        n = num
    return n

def sigmoid(num):
    return 1/(1+math.pow(math.e, -num))

def resultToFile(moduleId, topicList, methodBoostList, topicBoostList, docBoostList, t):
    bm25Boost = methodBoostList[0]
    tfidfBoost = methodBoostList[1]

    bm25TopicBoostList = topicBoostList[:3]
    tfidfTopicBoostList = topicBoostList[3:]

    bm25DocBoostList = docBoostList[:18]
    tfidfDocBoostList = docBoostList[18:]

    bm25Result = {}
    tfidfResult = {}

    returnResult = {}
    #f = open(os.path.join(dataDir, 'res{}.txt'.format(moduleId)),'w')
    for topicId in topicList:
        finalResult = {}
        topicID = topicId
        topicID -= 1
        bm25Result =  getResultList(topicID, bm25Index, bm25TopicBoostList, bm25DocBoostList, bm25Boost)
        tfidfResult = getResultList(topicID, tfidfIndex, tfidfTopicBoostList, tfidfDocBoostList, tfidfBoost)
        for docId in tfidfResult.keys():
            if docId in bm25Result.keys():
                finalScore = bm25Result[docId] + tfidfResult[docId]
            else:
                finalScore = tfidfResult[docId]
            s = word2vec.similarity(topicID, docId)
            finalScore = sigmoid(finalScore)*math.log(3 + relu(t*s))
            bm25Result.update({docId : finalScore})
        finalResult = bm25Result
        finalResult= sorted(finalResult.items(), key=lambda d:d[1], reverse = True)   # sort by score, 排完顺后就不再是dict类型了
        #r = 0  # ranking number
        #for res in finalResult:
            #f.write(' '.join([str(topicID+1), "Q0", res[0], str(r), str(res[1]), "SZIR"]) + '\n')
            #r += 1
        returnResult.update({topicID+1 : bm25Result})
    #f.close()
    return returnResult

def baseResultToFile(moduleId, topicList):
    returnResult = {}
    bm25_result = []

    #bm25File = open(os.path.join(dataDir, 'baseResBM25{}.txt'.format(moduleId)),'w')

    for topicId in topicList:
        topicID = topicId
        topicID -= 1
        bm25_result =  getBaseResultList(topicID, bm25Index)

        bm25Result = {}

        for r in bm25_result:
            bm25Result.update({r[0]:r[1]})
        
        returnResult.update({topicID+1 : bm25Result})

        #r1 = 0
        #for res in bm25_result:
        #    bm25File.write(' '.join([str(topicID+1), "Q0", res[0], str(r1), str(res[1]), "SZIR"]) + '\n')
        #    r1 += 1
        
    #bm25File.close()
    return returnResult
    
def getFinalResult(moduleId, topicList, res1, res2, p):
    finalFile = open(os.path.join(dataDir, 'res{}.txt'.format(moduleId)),'w')

    for j in topicList:
        res1Value = res1[j]
        res2Value = res2[j]
        for docId in res2Value.keys():
            if docId in res1Value.keys():
                finalScore = p*res1Value[docId] + (1-p)*res2Value[docId]
            else:
                finalScore = res2Value[docId]
            res1Value.update({docId : finalScore})
            finalResult = res1Value
            finalResult= sorted(finalResult.items(), key=lambda d:d[1], reverse = True)   # sort by score
            x = 0  # ranking number
        for res in finalResult:
            finalFile.write(' '.join([str(j), "Q0", res[0], str(x), str(res[1]), "SZIR"]) + '\n')
            x += 1
    finalFile.close()


