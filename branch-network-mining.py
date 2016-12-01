# branch-network-mining.py
# Extract branch networks of a repository in a GraphML file
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
#
# REQUISITES:
#------------ 
# - Libraries to be installed (with pip install)
#   . pyGithub
#   . pygithub3
#   . NetworkX
#   . Requests
#   . Json
# - sub-directory called Results
#
# PARAMETERS :
#-------------
# ID of the repository to analyse
# Attention this should be the original repository
# if it is the fork of another repository
# the forked repository won't be considered
# only forking repositories are considered, not the forked repositories

# NOTES:
#-------
# - the script is not able to connect one commit to two predecessors
# - viewing a repository from different users leads to a different allocation of commits in branches
#   see network view of repo GitHub-Social-Network-Analysis from the perspective of jbon and kerstinopen     
# - repositories for tests:
#    . small one: kerstinopen/animaluni, ID 68228196
#    . medium one: openp2pdesign / Github-Social-Network-Analysis, ID 8126643
#    . large one: poppy-project/poppy-humanoid, ID 29011745
# - PyGitHub documentation can be found here: 
#    . https://github.com/jacquev6/PyGithub
#    . http://pygithub.readthedocs.io/en/latest/reference.html

from github import Github
from github import Commit
from xml.etree.ElementTree import Element, SubElement, Comment, ElementTree

import pygithub3
import networkx as nx
import getpass
import random
import os
import sys
import requests
import json
import traceback 

# GLOBAL VARIABLES
# Enables tracing in the terminal
debug = True
# list of commit shas used as a global reference in function get_predecessors
knownCommits = []

# Clear screen
os.system('cls' if os.name=='nt' else 'clear')
# Remove CLS Client from system path
if os.environ['PATH'].find("iCLS Client")>=0:
    os.environ['PATH'] = "".join([it for it in os.environ['PATH'].split(";") if not it.find("iCLS Client")>0])

###################################################################################################################
# get_all_forks_branches
###################################################################################################################
# Returns all branches of all forks of a repository
# Branches are characterized by their name (key) and the sha of the last commit (value)
def get_all_forks_branches(repository):
    # Initializing the dictionary containing all branches to be discovered 
    branchList = {}
    
    # get all commits in the forks of the given repository
    for fork in repository.get_forks():
        print ("  - branches of " + fork.owner.login + "'s fork")
        # Gets all branches of the current fork in json format thanks to the GitHub API (GET query)
        # the JSON parsing returns a list of collections, where each branch is characterized a name and by the last commit performed on this branch
        branchesInJsonFormat = requests.get("https://api.github.com/repos/{}/{}/branches".format(fork.owner.login,fork.name))
        parsedBranches = json.loads(branchesInJsonFormat.text)

        for branch in parsedBranches:
            print ("    . "+ branch['name'])
            branchList[branch['name']] = branch['commit']['sha']
    
        # Gets through recursiveness the branches eventually created in the forks of the current fork
        forksCommitsList = get_all_forks_branches(fork)
        for name,sha in forksCommitsList.items():
            branchList[name] = sha

    return branchList

###################################################################################################################
# get_predecessors
###################################################################################################################
# Returns all predecessors of a given commit 
# These are stored in a list containing commit shas
# Predecessors that are already known globally are excluded
# The returned list starts with the given commit followed by its predecessors until:
# - there is no predecessor any more
# - the predecessor is globally known (the globally known predecessor is then the last element of the list)
def get_predecessors(commit) :
    index = 0
    parentList = commit.parents
    parentListLenght = len(parentList)
    if parentListLenght==0:
        return [commit.sha]
    elif parentListLenght==1:
        parentSha = parentList[0].sha
        if parentSha in knownCommits:
            return [commit.sha, parentSha]
        else:
            knownCommits.append(parentList[0].sha)
            returnList = [commit.sha]
            returnList.extend(get_predecessors(parentList[0]))
            return returnList
    else:
        print ("ERROR: more than one parent")

###################################################################################################################
# getRandomColor
###################################################################################################################
def getRandomColor():
    r = lambda: random.randint(0,255) 
    g = lambda: random.randint(0,255)
    b = lambda: random.randint(0,255)
    return '#%02X%02X%02X' % (r(),g(),b())    
       
###################################################################################################################
# createGraphML
###################################################################################################################
def createGraphML(branchesContents, repository):
    # Creates the GraphML header
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
    SubElement(graphml, 'key', { "for":"node", "id":"attrCommitCommentBody", "attr.name":"commentBody", "attr.type":"string"})
    SubElement(graphml, 'key', { "for":"node", "id":"attrCommitCommentDate", "attr.name":"commentDate", "attr.type":"string"})
    SubElement(graphml, 'key', { "for":"node", "id":"attrCommitCommentCreator", "attr.name":"commentCreator", "attr.type":"string"})
    graph = SubElement(graphml, 'graph', {"edgedefault":"directed"})

    # Initializes the color dictionaries
    # Each user is associated with a node fill color
    # Each branch is associated with a node border color
    userColorDictionary = {}
    branchColorDictionary = {}
    
    for branchName,commitsList in branchesContents.items():
        
        print (" - creating branch "+branchName)
        # Updates branch color dictionary
        branchColorDictionary[branchName]=getRandomColor()
    
        # remember last processed commit in order to create links between subsequent commits
        lastProcessedCommit = None
    
        for currentCommitSha in commitsList:
        
            print ("   . creating node "+currentCommitSha)
            # Gets the commit object out of its sha
            currentCommit = repo.get_commit(currentCommitSha)
            
            # Gets committer's name
            try:
                currentCommitCommitter = currentCommit.author.login
            except :
                try:
                    currentCommitCommitter = currentCommit.author.name
                except :
                    currentCommitCommitter = "none"
         
            # Gets commit's URL
            currentCommitUrl = currentCommit.url
         
            # update color dictionary
            # if there is no color associated with the user, insert a new random HTML color in the dictionary
            if currentCommitCommitter not in userColorDictionary.keys():
                userColorDictionary[currentCommitCommitter]=getRandomColor()
         
            # create a new node
            node = SubElement(graph, "node", {"id" : currentCommitSha})

            # edit node style
            nodeStyleData = SubElement(node, "data", {"key":"nodeStyle"})
            shapeNode = SubElement(nodeStyleData, "y:ShapeNode")
            NodeLabel = SubElement(shapeNode, "y:NodeLabel")
            Shape= SubElement(shapeNode, "y:Shape", {"type":"retangle"})
            Geometry= SubElement(shapeNode, "y:Geometry", {"height":"15.0", "width":"60"})
            Fill = SubElement(shapeNode, "y:Fill", {"color":userColorDictionary[currentCommitCommitter], "transparent":"false"})
            BorderStyle = SubElement(shapeNode, "y:BorderStyle", {"color":branchColorDictionary[branchName], "type":"line", "width":"3.0"})
            NodeLabel.text = str(currentCommitSha[:7])

            # add node attributes
            attributeData = SubElement(node, "data", {"key":"attrAuthor"})
            try: 
                attributeData.text = str(currentCommit.author.login)
            except AttributeError:
                try: 
                    attributeData.text = str(currentCommit.author.name)
                except AttributeError:
                    attributeData.text = str("none")

            attributeData = SubElement(node, "data", {"key":"attrComment"})
            attributeData.text = str(currentCommit.commit.message)

            attributeData = SubElement(node, "data", {"key":"attrUrl"})
            attributeData.text = str(currentCommit.url)

            for k in currentCommit.get_comments():
                attributeData = SubElement(node, "data", {"key":"attrCommitCommentBody"})
                attributeData.text = str(k.body)
                attributeData = SubElement(node, "data", {"key":"attrCommitCommentDate"})
                attributeData.text = str(k.created_at.date())
                attributeData = SubElement(node, "data", {"key":"attrCommitCommentCreator"})
                attributeData.text = str(k.user.login)

            if lastProcessedCommit != None:
                edge = SubElement(graph, "edge", {
                "id":currentCommitSha[:7]+"_"+lastProcessedCommit[:7],
                "directed":"true",
                "source":currentCommitSha,
                "target":lastProcessedCommit,
                "color": "#99ccff"})

            lastProcessedCommit = currentCommitSha
                
    # write the GraphML file in the subdirectory "/results"
    ElementTree(graphml).write("./Results/"+repository.name +"commit_structure.graphml")
    
    
###################################################################################################################
# main function
###################################################################################################################
if __name__ == "__main__":
    # Gets the repository ID given as parameter to the script
    repoId = sys.argv[1]

    # User login
    userlogin = input("Login: Enter your username: ")
    password = getpass.getpass("Login: Enter your password: ")
    g = pygithub3.Github( userlogin, password )
    
    # Gets the repository object from the given ID
    repo = g.get_repo(int(repoId))
    print ("\nAnalysis of repository " + repo.name)

    # Initializes the dictionary used to store all commits of all branches
    # Commits are stored in a dictionary containing lists of commits shas (values) referred by the branch names (key)
    branchesContents = {}
    
    # Gets all commits of the main branch of the original repository
    for commit in repo.get_commits():
       knownCommits.append(commit.sha)
    print ("\n" + str(len(knownCommits)) + " commits found in the master branch")
    branchesContents['OriginalMaster']= knownCommits
    
    # Gets all branches of the forks of the given repository
    print ("\nLooking for other branches ")
    branchReferences = get_all_forks_branches(repo)
    print (str(len(branchReferences)) + " branches found")
    
    # Gets all commits of all branches
    print ("\nParsing branches")
    for name, sha in branchReferences.items():
        print ("  - parsing branch " + name + " starting from commit " + sha)
        predecessors = get_predecessors(repo.get_commit(sha))
        branchesContents[name] = predecessors
        print ("    . " + str(len(predecessors)) + " predecessors found")

    # Generate the GraphML file out of the branches commits
    print ("\nBuiding GraphML ")
    createGraphML(branchesContents, repo)
    
    print ("\ndone. \n")
    
    
    
    
