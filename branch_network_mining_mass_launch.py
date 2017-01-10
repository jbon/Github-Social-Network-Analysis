# branch_network_mining_mass_launch.py
# Extracts the commit network of the repositories
# given in an input CSV file
# Version: 0.1 - First draft
# Authors: Kerstin Carola Schmidt, Jérémy Bonvoisin
# Homepage: http://opensourcedesign.cc
# License: GPL v.3

# REQUISITES: 
# - install pyGithub with pip install PyGithub
# - install pygithub3 with pip install pygithub3
# - sub-directory called 'Results'

# PARAMETERS :
#-------------
# - The URL of an input CSV file given as parameter of the script
# - the CSV file is formatted as follows
#   . it contains 2 columns: userID and Repository_name
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
import os
import branch_network_mining_utils

# Clear screen
os.system('cls' if os.name=='nt' else 'clear')

# User login
userlogin = input("Login: \n  Enter your username: ")
password = getpass.getpass("  Enter your password: ")
g = pygithub3.Github( userlogin, password )

# Gets the reference of the CSV file given as parameter to the script
CSVFileReference = sys.argv[1]
print("\nopening CSV file: "+CSVFileReference)

with open(CSVFileReference, newline='') as csvInput:
    CSVReader = csv.reader(csvInput)
    for row in CSVReader:
        if len(row)==2 :
            repo = g.get_repo(row[0] + "/" + row[1])
            print("\n__________________________________________________________")
            print("launch analysis of "+row[0]+"/"+row[1]+"(ID:"+str(repo.id)+")")
            branch_network_mining_utils.mine_repo(repo)
        else :
            print ("WARINING - wrong line format, should be 'username' ',' 'repository' - line ignored")