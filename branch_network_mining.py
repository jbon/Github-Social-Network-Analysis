# branch_network_mining.py
# Extracts the commit network of a repository whose ID is given as parameter
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
# ID of the repository to analyse
# Attention: 
#   this should be the original repository
#   if it is the fork of another repository
#   the forked repository won't be considered
#   only forking repositories are considered, not the forked repositories

# NOTES:
#-------
# - repositories for tests:
#    . small one: kerstinopen/animaluni, ID 68228196
#    . medium one: openp2pdesign / Github-Social-Network-Analysis, ID 8126643
#    . large one: poppy-project/poppy-humanoid, ID 29011745
# - PyGitHub documentation can be found here: 
#    . https://github.com/jacquev6/PyGithub
#    . http://pygithub.readthedocs.io/en/latest/reference.html

from github import Github
import pygithub3
import getpass
import sys
import os
import branch_network_mining_utils

# Clear screen
os.system('cls' if os.name=='nt' else 'clear')

# User login
userlogin = input("Login: \n  Enter your username: ")
password = getpass.getpass("  Enter your password: ")
g = pygithub3.Github( userlogin, password )

# Gets the repository ID given as parameter to the script
repoId = sys.argv[1]

# Gets the repository object
repo = g.get_repo(int(repoId))

# Calls the mining function
branch_network_mining_utils.mine_repo(repo)