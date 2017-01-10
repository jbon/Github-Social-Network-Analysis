# getMassRepoId.py
# Get the IDs of repositories given in an input CSV file
# saves the result in another CSV file in the same directory
# Version: 0.1 - First draft
# Authors: Kerstin Carola Schmidt, Jérémy Bonvoisin
# Homepage: http://opensourcedesign.cc
# License: GPL v.3

# REQUISITES: 
# - install pyGithub with pip install PyGithub
# - install pygithub3 with pip install pygithub3
# - The URL of an input CSV file given as parameter of the script
# - the CSV file is formatted as follows
#   . it contains 2 columns: userID and Repository
#   . column separator is comma
#   . line separator is carriage return

from github import Github
from os.path import basename
from os.path import dirname
from os.path import splitext
import pygithub3
import getpass
import csv
import sys

# get credentials
userlogin = input("Enter your GitHub login: ")
password = getpass.getpass("Enter your GitHub password: ")
g = pygithub3.Github( userlogin, password )

# Gets the reference of the CSV file given as parameter to the script
CSVFileReference = sys.argv[1]
print("look at file: "+CSVFileReference)
users = []
repos = []
Ids = []
with open(CSVFileReference, newline='') as csvInput:
    CSVReader = csv.reader(csvInput)
    with open(dirname(CSVFileReference)+"\\"+splitext(basename(CSVFileReference))[0]+"output"+".csv", 'w', newline='') as csvOutput:
        CSVWriter = csv.writer(csvOutput)
        for row in CSVReader:
            if len(row)==2 :
                repo = g.get_repo(row[0] + "/" + row[1])
                CSVWriter.writerow([row[0], row[1], repo.id])
                print([row[0], row[1], repo.id])
            else :
                print ("WARINING - wrong line format, should be 'username' ',' 'repository' - line ignored")