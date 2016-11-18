# branch-network-mining.py
# Extract branch networks of a repository in a GraphML file
# Version: 0.1 - First draft
# Authors: Kerstin Carola Schmidt, Jérémy Bonvoisin
# Homepage: http://opensourcedesign.cc
# License: GPL v.3
#
# Based on previous work of
# Author: Massimo Menichinelli
# Homepage: http://www.openp2pdesign.org
#
# Requisite: 

# install pyGithub with pip install PyGithub
# install pygithub3 with pip install pygithub3
# install NetworkX with pip install networkx
# sub-directory called Results
#
# Parameter :
# Id of the repository to analyse
#
# PyGitHub documentation can be found here: 
# https://github.com/jacquev6/PyGithub
# http://pygithub.readthedocs.io/en/latest/reference.html

from github import Github
from github import Commit

import pygithub3

import networkx as nx
import getpass
import random
import os
import sys
import requests



# Clear screen
os.system('cls' if os.name=='nt' else 'clear')

# Remove CLS Client from system path
if os.environ['PATH'].find("iCLS Client")>=0:
    os.environ['PATH'] = "".join([it for it in os.environ['PATH'].split(";") if not it.find("iCLS Client")>0])

from lxml import etree
from xml.etree.ElementTree import Element, SubElement, Comment, ElementTree


# https://pygithub.readthedocs.io/en/latest/github_objects/Commit.html?

def analyse_repo(repository):
    index = 0;

    # creating graphml header
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

    # initialize color dictionary
    # each user is associated with a node color
    colorDictionary = {}
    
    # generate network
    j = 0
    for i in repository.get_branches():
        j += 1
        print("branch #", j)
        print("name: ", i.name)
        print("commit sha: ", i.commit.sha)
        print("commit url: ", i.commit.url)
        print("")
        


    k = 0
    for i in repository.get_forks():
        k += 1
        print ("fork #", k)

        print ("ID: ", i.id)
        print ("owner: ", i.owner.login)
        print("name: ", i.name)
        print("default branch: ", i.default_branch)

        print ("description: ", i.description)
        print ("url: ", i.url)
        print("#forks :", i.forks_count)
        print("# open issues: ", i.open_issues_count)
        print("pushed at: ", i.pushed_at.date())
        print("created at: ", i.created_at.date())


        print(i.branches_url) #url kopieren, statt "{/branch}" den branch name eingeben,
        # wenn im network nach branches gesucht wird können alle angezeigt werden
        # >> wie bekommt man die automatisch angezeigt?
        #https://api.github.com/repos/iloveopensource123/currentopen123/branches
        #https://api.github.com/repos/{user name}/{repo name}/branches
        #user name: i.owner.login, repo name: i.name


        # link = "https://api.github.com/repos/'{username}'/'{reponame}'/branches".format('i.owner.login','i.name')
        # link = "https://api.github.com/repos/username/reponame/branches", username= {'i.owner.login'}, reponame={'i.name'}
        
        # f = requests.get("https://api.github.com/repos/username/reponame/branches", username= {'i.owner.login'}, reponame={'i.name'})
       
        # params = {"username": i.owner.login, "reponame":i.name}
        # f = requests.get("https://api.github.com/repos/username/reponame/branches", params= params)




        import json
        from lxml import html
        r = requests.get("https://api.github.com/repos/iloveopensource123/currentopen123/branches")

        j = json.loads(r.text)

        print (j[0]['name'])
        print (j[0]['commit']['sha'])
            
        # funktioniert bei mir noch nicht wegen lxml-Problemen, sobald ich das zum Laufen bekommen hab gucke ich, wie das sinnvoll in den bisherigen
        # Code integriert werden kann


        
        print(i.commits_url)
        print("")


    for i in repository.get_commits():
        currentCommitSha = i.sha
        currentCommitCommitter = i.author.login
        currentCommitUrl = i.url

        for k in i.get_comments():
            currentCommitCommentBody = k.body
            currentCommitCommentDate = k.created_at.date()
            currentCommitCommentCreator = k.user.login




        

        index += 1
        print ("commit ", index, " : ", currentCommitSha)

        # for k in i.get_comments():
        #     print (k.body)
        #     print (k.created_at.date())
        #     print (k.user.login)

 
        # update color dictionary
        # if there is no color associated with the user, insert a new random HTML color in the dictionary
        if currentCommitCommitter not in colorDictionary.keys():
            r = lambda: random.randint(0,255) 
            g = lambda: random.randint(0,255)
            b = lambda: random.randint(0,255)
            colorDictionary[currentCommitCommitter]='#%02X%02X%02X' % (r(),g(),b())
     
        # create a new node
        node = SubElement(graph, "node", {"id" : currentCommitSha})
 
        # edit node style
        nodeStyleData = SubElement(node, "data", {"key":"nodeStyle"})
        shapeNode = SubElement(nodeStyleData, "y:ShapeNode")
        NodeLabel = SubElement(shapeNode, "y:NodeLabel")
        Shape= SubElement(shapeNode, "y:Shape", {"type":"retangle"})
        Geometry= SubElement(shapeNode, "y:Geometry", {"height":"15.0", "width":"60"})
        Fill = SubElement(shapeNode, "y:Fill", {"color":colorDictionary[currentCommitCommitter], "transparent":"false"})
        BorderStyle = SubElement(shapeNode, "y:BorderStyle", {"color":"#ffffff", "type":"line", "width":"1.0"})
        NodeLabel.text = str(currentCommitSha[:7])

        # add node attributes
        attributeData = SubElement(node, "data", {"key":"attrAuthor"})
        attributeData.text = str(i.author.login)
        attributeData = SubElement(node, "data", {"key":"attrComment"})
        attributeData.text = str(i.commit.message)
        attributeData = SubElement(node, "data", {"key":"attrUrl"})
        attributeData.text = str(i.url)
        for k in i.get_comments():
            attributeData = SubElement(node, "data", {"key":"attrCommitCommentBody"})
            attributeData.text = str(k.body)
            attributeData = SubElement(node, "data", {"key":"attrCommitCommentDate"})
            attributeData.text = str(k.created_at.date())
            attributeData = SubElement(node, "data", {"key":"attrCommitCommentCreator"})
            attributeData.text = str(k.user.login)




        index2 = 0
        for k in i.parents:
            index2 += 1
            childCommitSha = k.sha
            edge = SubElement(graphml, "edge", {
                "id":str(index)+"_"+str(index2),
                "directed":"true",
                "source":childCommitSha,
                "target":currentCommitSha})

    # write the xml file

    #change because it doesn`t work for me 
    # ElementTree(graphml).write("./Results/"+repository.name + "_commit_structure.graphml")
    ElementTree(graphml).write("commit_structure.graphml")



if __name__ == "__main__":
    # get the repository ID given as parameter to the script
    repoId = sys.argv[1]

    # login
    userlogin = input("Login: Enter your username: ")
    password = getpass.getpass("Login: Enter your password: ")
    g = pygithub3.Github( userlogin, password )
    
    # get the repository object and call analysis function 
    repo = g.get_repo(int(repoId))
    print ("Analysis of repository ",repo.name)
analyse_repo(repo)