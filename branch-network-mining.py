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
import datetime

from datetime import timedelta

# GLOBAL VARIABLES
# Enables tracing in the terminal
debug = True
# list of commit shas used as a global reference in function get_predecessors
# and list of the references to their respective branch
knownCommits = []
knownCommitsBranches = []

# Clear screen
os.system('cls' if os.name=='nt' else 'clear')
# Remove CLS Client from system path
if os.environ['PATH'].find("iCLS Client")>=0:
    os.environ['PATH'] = "".join([it for it in os.environ['PATH'].split(";") if not it.find("iCLS Client")>0])

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
# Discovers all predecessors of a given commit and store them in the global variable known commits
def get_predecessors(commit, branchName) :
    currentCommitSha = commit.sha
    if currentCommitSha not in knownCommits:
        knownCommits.append(currentCommitSha)
        knownCommitsBranches.append(branchName)
        for parent in commit.parents:
            get_predecessors(parent, branchName)
            
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
def createGraphML(repository):
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
    SubElement(graphml, 'key', { "for":"node", "id":"attrBranch", "attr.name":"branch", "attr.type":"string"})

    graph = SubElement(graphml, 'graph', {"edgedefault":"directed"})

    # Initializes the color dictionaries
    # Each user is associated with a node fill color
    # Each branch is associated with a node border color
    userColorDictionary = {}
    branchColorDictionary = {}
    
    for index in range(0,len(knownCommits)):
        
        # getting input information for the current commit
        currentCommitSha = knownCommits[index]
        currentCommitBranchName = knownCommitsBranches[index]
        currentCommit = repo.get_commit(currentCommitSha)
        print ("   . creating node "+currentCommitSha)
        
        # Updates branch color dictionary
        if currentCommitBranchName not in branchColorDictionary.keys():
            branchColorDictionary[currentCommitBranchName]=getRandomColor()
         
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
        BorderStyle = SubElement(shapeNode, "y:BorderStyle", {"color":branchColorDictionary[currentCommitBranchName], "type":"line", "width":"3.0"})
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

        attributeData = SubElement(node, "data", {"key":"attrBranch"})
        attributeData.text = str(currentCommitBranchName)

        # BoJ@ScK : this is not working
        for k in currentCommit.get_comments():
            attributeData = SubElement(node, "data", {"key":"attrCommitCommentBody"})
            attributeData.text = str(k.body)
            attributeData = SubElement(node, "data", {"key":"attrCommitCommentDate"})
            attributeData.text = str(k.created_at.date())
            attributeData = SubElement(node, "data", {"key":"attrCommitCommentCreator"})
            attributeData.text = str(k.user.login)

        for predecessor in currentCommit.parents:
            edge = SubElement(graph, "edge", {
            "id":currentCommitSha[:7]+"_"+predecessor.sha[:7],
            "directed":"true",
            "source":predecessor.sha,
            "target":currentCommitSha})
            edgeStyleData = SubElement(edge, "data", {"key":"edgeStyle"})
            shapeEdge = SubElement(edgeStyleData, "y:PolyLineEdge")
            SubElement(shapeEdge, "y:LineStyle", {"color":branchColorDictionary[currentCommitBranchName], "type":"line", "width":"2.0"})
            SubElement(shapeEdge, "y:Arrows", {"source":"none", "target":"standard"})

    # write the GraphML file in the subdirectory "/results"
    ElementTree(graphml).write("./Results/"+repository.name +"commit_structure.graphml")
    
    
###################################################################################################################
# main function
###################################################################################################################
if __name__ == "__main__":
    # Gets the repository ID given as parameter to the script
    repoId = sys.argv[1]

    # User login
    userlogin = input("Login: \n  Enter your username: ")
    password = getpass.getpass("  Enter your password: ")
    g = pygithub3.Github( userlogin, password )

    # getting time for calculating processing time
    startTime = datetime.datetime.now()
    print ("\nProcessing starts at "+ startTime.strftime('%H:%M:%S'))
    
    # Gets the repository object from the given ID
    repo = g.get_repo(int(repoId))
    print ("\nGetting all commits of the root repository " + repo.name)

    # Gets the last commit of the master branch of the original repository and looks for predecessors
    commitsMasterBranch = []
    for commit in repo.get_commits():
       commitsMasterBranch.append(commit)
    get_predecessors(commitsMasterBranch[0], 'origin')
    numberKnownCommits = len(knownCommits)
    print ("\n" + str(numberKnownCommits) + " commits found in the master branch (last commit: " + knownCommits[0] + ")")
    
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
            newNumberKnownCommits = len(knownCommits)
            print ("      -> " + str(newNumberKnownCommits-numberKnownCommits) + " new predecessors found")
            numberKnownCommits = newNumberKnownCommits

    # Generate the GraphML file out of the branches commits
    print ("\nBuiding GraphML ")
    createGraphML(repo)
    
    # Displays processing time
    endTime = datetime.datetime.now()
    processingTime = endTime - startTime
    print ("\ndone. \n")
    print ("Analysis processed in "+ str(processingTime))
    
    
    