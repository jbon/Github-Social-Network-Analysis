# branch_network_mining_utils.py
# provides functions for extracting commit networks of repositories
#
# LICENSE INFORMATION:
#---------------------
# Version: 0.1 - First draft
# Authors: Kerstin Carola Schmidt, Jérémy Bonvoisin
# Homepage: http://opensourcedesign.cc
# License: GPL v.3
# Based on previous work of
# Author: Massimo Menichinelli
# Homepage: http://www.openp2pdesign.org

# REQUISITES:
#------------ 
# - Libraries to be installed (with pip install)
#   . pyGithub
#   . pygithub3
#   . NetworkX
#   . Requests
#   . Json
# - sub-directory called 'Results'

from github import Github
from github import Commit
from xml.etree.ElementTree import Element, SubElement, Comment, ElementTree

import pygithub3
import networkx as nx
import getpass
import random
import os
import sys
import csv
import requests
import json
import traceback 
import datetime

from datetime import timedelta

# GLOBAL VARIABLES
##################
# dictionary containing all information about all commits formatted as follows
# {sha:{
#   'branch':branch, 
#   'committer':committer, 
#   'url':url, 
#   'message':message, 
#   'date':date
#   'parents':[parent1, parent2, ...]}}
commitsData = {}

###################################################################################################################
# get_all_forks_branches
###################################################################################################################
# Returns all branches of all forks of a repository
# stored in a dictionary as follows: {forkOwner:{branchName:shaOfLastCommit}}
# Branches are characterized by their name (key) and the sha of the last commit (value)
def get_forks_and_branches(repository):
    # Initializing the dictionary containing all branches to be discovered 
    forkList = {}
    
    # get all commits in the forks of the given repository
    for fork in repository.get_forks():
        print ("  - branches of " + fork.owner.login + "'s fork")
        # Gets all branches of the current fork in json format thanks to the GitHub API (GET query)
        # the JSON parsing returns a list of collections, where each branch is characterized a name and by the last commit performed on this branch
        branchesInJsonFormat = requests.get("https://api.github.com/repos/{}/{}/branches".format(fork.owner.login,fork.name))
        parsedBranches = json.loads(branchesInJsonFormat.text)

        # Save all branches of the current fork in the dictionary "branchList"
        branchList = {}
        # BoJ Reminder - to be improved 
        for branch in parsedBranches:
            try: 
                print ("    . " + branch['name'])
                branchList[branch['name']] = branch['commit']['sha']
            except :
                print ("error : " + branch)
        # Adds the current fork and its branches in the dictionary "forkList"
        forkList[fork.owner.login] = branchList
    
        # Gets through recursive processing the eventual forks of the current fork
        forkList.update(get_forks_and_branches(fork))

    return forkList

###################################################################################################################
# get_predecessors
###################################################################################################################
# Discovers all predecessors of a given commit,
# extracts information of each new discovered commit and 
# stores it in the global variable commitsData
def get_predecessors(commit, branchName) :
    if commit.sha not in commitsData.keys():
        print ("   . extracting commit "+commit.sha)
        commitDict = {}
        
        # Gets basic data
        commitDict['branch'] = branchName
        commitDict['url'] = commit.url
        commitDict['message'] = str(commit.commit.message)
        commitDict['date'] = commit.commit.committer.date.strftime('%d-%m-%Y')

        # Gets committer's name
        # here we make no difference between the roles of the committer and those of the author
        try:
            commitDict['committer'] = commit.committer.login
        except :
            try:
                commitDict['committer'] = commit.author.login
            except:
                commmitInJsonFormat = requests.get(commit.url)
                parsedCommit = json.loads(commmitInJsonFormat.text)
                commitDict['committer'] = parsedCommit['commit']['committer']['name']
        
        # Gets the list of predecessors' shas
        parents = []
        for predecessor in commit.parents:
            parents.append(predecessor.sha)
        commitDict['parents'] = parents

        # Adds the dictionary in the global variable commitsData
        commitsData[commit.sha] = commitDict
        
        # recurrence 
        for parent in commit.parents:
            get_predecessors(parent, branchName)
            
###################################################################################################################
# exportCSV
###################################################################################################################
# Exports the contents of commitsData in a CSV file
def exportCSV(repoName):
    with open("./Results/"+repoName+"commit_structure.csv", 'w', newline='') as csvOutput:
        CSVWriter = csv.writer(csvOutput)
        for sha, commitDict in commitsData.items():
            CSVWriter.writerow([
                sha,
                commitDict['branch'],
                commitDict['committer'],
                commitDict['date'],
                str(commitDict['parents']).replace("[", "").replace("]", "").replace("'", "").replace('"', "")
                ])

###################################################################################################################
# exportGraphML
###################################################################################################################
# Exports the contents of commitsData in a CSV file
def exportGraphML(repoName):

    # Initializes the GraphML structure
    graphml = Element('graphml', {
        "xmlns":"http://graphml.graphdrawing.org/xmlns",
        "xmlns:xsi":"http://www.w3.org/2001/XMLSchema-instance",
        "xmlns:y":"http://www.yworks.com/xml/graphml",
        "xmlns:yed":"http://www.yworks.com/xml/yed/3",
        "xsi:schemaLocation":"http://graphml.graphdrawing.org/xmlns http://www.yworks.com/xml/schema/graphml/1.1/ygraphml.xsd"})
    SubElement(graphml, 'key', { "for":"node", "id":"nodeStyle", "yfiles.type":"nodegraphics"})
    SubElement(graphml, 'key', { "for":"edge", "id":"edgeStyle", "yfiles.type":"edgegraphics"})
    SubElement(graphml, 'key', { "for":"node", "id":"attrAuthor", "attr.name":"author", "attr.type":"string"})
    SubElement(graphml, 'key', { "for":"node", "id":"attrComment", "attr.name":"comment", "attr.type":"string"})
    SubElement(graphml, 'key', { "for":"node", "id":"attrUrl", "attr.name":"url", "attr.type":"string"})
    SubElement(graphml, 'key', { "for":"node", "id":"attrBranch", "attr.name":"branch", "attr.type":"string"})
    SubElement(graphml, 'key', { "for":"node", "id":"attrTimestamp", "attr.name":"timestamp", "attr.type":"string"})
    # SubElement(graphml, 'key', { "for":"node", "id":"attrCommitCommentBody", "attr.name":"commentBody", "attr.type":"string"})
    # SubElement(graphml, 'key', { "for":"node", "id":"attrCommitCommentDate", "attr.name":"commentDate", "attr.type":"string"})
    # SubElement(graphml, 'key', { "for":"node", "id":"attrCommitCommentCreator", "attr.name":"commentCreator", "attr.type":"string"})
    graph = SubElement(graphml, 'graph', {"edgedefault":"directed"})

    # Initializes the color dictionaries
    # Each user is associated with a node fill color
    # Each branch is associated with a node border color
    userColorDictionary = {}
    branchColorDictionary = {}
    
    for sha, commitDict in commitsData.items():
        
        # Updates branch/user color dictionary
        # if there is no color associated with the branch/user, insert a new random HTML color in the dictionary
        if commitDict['branch'] not in branchColorDictionary.keys():
            branchColorDictionary[commitDict['branch']]=getRandomColor()
        if commitDict['committer'] not in userColorDictionary.keys():
            userColorDictionary[commitDict['committer']]=getRandomColor()
     
        # create a new node
        node = SubElement(graph, "node", {"id" : sha})

        # edit node style
        nodeStyleData = SubElement(node, "data", {"key":"nodeStyle"})
        shapeNode = SubElement(nodeStyleData, "y:ShapeNode")
        NodeLabel = SubElement(shapeNode, "y:NodeLabel")
        Shape= SubElement(shapeNode, "y:Shape", {"type":"retangle"})
        Geometry= SubElement(shapeNode, "y:Geometry", {"height":"15.0", "width":"60"})
        Fill = SubElement(shapeNode, "y:Fill", {"color":userColorDictionary[commitDict['committer']], "transparent":"false"})
        BorderStyle = SubElement(shapeNode, "y:BorderStyle", {"color":branchColorDictionary[commitDict['branch']], "type":"line", "width":"3.0"})
        NodeLabel.text = str(sha[:7])

        # add node attributes
        attributeData = SubElement(node, "data", {"key":"attrAuthor"})
        attributeData.text = commitDict['committer']
        attributeData = SubElement(node, "data", {"key":"attrUrl"})
        attributeData.text = commitDict['url']
        attributeData = SubElement(node, "data", {"key":"attrBranch"})
        attributeData.text = commitDict['branch']
        attributeData = SubElement(node, "data", {"key":"attrTimestamp"})
        attributeData.text = commitDict['date']
        attributeData = SubElement(node, "data", {"key":"attrComment"})
        attributeData.text = commitDict['message']
        
        # BoJ@ScK : this is not working
        # for k in currentCommit.get_comments():
            # attributeData = SubElement(node, "data", {"key":"attrCommitCommentBody"})
            # attributeData.text = str(k.body)
            # attributeData = SubElement(node, "data", {"key":"attrCommitCommentDate"})
            # attributeData.text = str(k.created_at.date())
            # attributeData = SubElement(node, "data", {"key":"attrCommitCommentCreator"})
            # attributeData.text = str(k.user.login)

        for predecessorSha in commitDict['parents']:
            edge = SubElement(graph, "edge", {
            "id":sha[:7]+"_"+predecessorSha[:7],
            "directed":"true",
            "source":predecessorSha,
            "target":sha})
            edgeStyleData = SubElement(edge, "data", {"key":"edgeStyle"})
            shapeEdge = SubElement(edgeStyleData, "y:PolyLineEdge")
            SubElement(shapeEdge, "y:LineStyle", {"color":branchColorDictionary[commitDict['branch']], "type":"line", "width":"2.0"})
            SubElement(shapeEdge, "y:Arrows", {"source":"none", "target":"standard"})

    # write the GraphML file in the subdirectory "/results"
    ElementTree(graphml).write("./Results/"+repoName +"commit_structure.graphml")
    
###################################################################################################################
# getRandomColor
###################################################################################################################
def getRandomColor():
    r = lambda: random.randint(0,255) 
    g = lambda: random.randint(0,255)
    b = lambda: random.randint(0,255)
    return '#%02X%02X%02X' % (r(),g(),b())    

###################################################################################################################
# mine_repo
###################################################################################################################
# extract all commit network information of a repository given as parameter
def mine_repo(repo):

    # clears the global variable in case it has already been used
    commitsData.clear()

    # getting time for calculating processing time
    startTime = datetime.datetime.now()
    print ("\nProcessing starts at "+ startTime.strftime('%H:%M:%S'))

    # Gets the last commit of the master branch of the original repository and looks for predecessors
    print ("\nGetting all commits of the root repository " + repo.name)
    commitsMasterBranch = []
    for commit in repo.get_commits():
       commitsMasterBranch.append(commit)
    get_predecessors(commitsMasterBranch[0], 'master')
    numberKnownCommits = len(commitsData)
    print ("\n" + str(numberKnownCommits) + " commits found in the master branch")
    
    # Gets all branches of the forks of the given repository
    print ("\nLooking for branches in forked repositories")
    forksAndBranches = get_forks_and_branches(repo)
    print ("\n" + str(len(forksAndBranches)) + " forks found")
    
    # Gets all commits of all branches
    print ("\nLooking for commits in all branches of all forks")
    for forkName, branchList in forksAndBranches.items():
        print ("  - branches of " + forkName + "'s fork")
        for branchName, sha in branchList.items():
            print ("    . parsing branch " + branchName + " starting from commit " + sha)
            get_predecessors(repo.get_commit(sha), branchName)
            newNumberKnownCommits = len(commitsData)
            print ("      - " + str(newNumberKnownCommits-numberKnownCommits) + " new commits found")
            numberKnownCommits = newNumberKnownCommits

    # Generates the CSV and GraphML output files
    print ("\nextract CSV file")
    exportCSV(repo.name)
    print ("extract GraphML file")
    exportGraphML(repo.name)
    
    # Displays processing time
    endTime = datetime.datetime.now()
    processingTime = endTime - startTime
    print ("Analysis processed in "+ str(processingTime))
    
    
    