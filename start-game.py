import sqlite3
import argparse
import trueskill
import subprocess

##############
# Parameters #
##############

pathToGame = r"./test-game.sh"
pathToDB = r"./mathecamp-games.sqlite"
pathForOutputs = r"./output/"

################################
# Parse command line arguments #
################################

###############
# Main method #
###############

#####################################################
# Adding, removing and changing players in database #
#####################################################

class player:
    def __init__(self, ID, name, grade, gender, mean, variance, rank, history_means, history_variances):
        self.ID = ID
        self.name = name
        self.grade = grade
        self.gender = gender
        self.rank = rank
        self.skill = trueskill.Rating(mean,variance)
        self.history = [(history_means(i),history_variances(i)) for i in history_means.keys()]
        self.teams = []

    def updateInDatabase(self,connection):
        with connection:
            connection.execute("UPDATE mathecamp-games.players SET (mean = ?, variance = ?, rank = ?) WHERE ID = ?", (self.mean, self.variance, self.rank, self.ID,))

class team:
    def __init__(self, ID, name, activeTeamFilePath, mean, variance, rank, teamMembers):
        self.ID = ID
        self.name = name
        self.activeTeamFilePath = activeTeamFilePath
        self.skill = trueskill.Rating(mean, variance)
        self.rank = rank
        self.teamMembers = teamMembers

dictOfAllTeams = {}
dictOfAllPlayers = {}

########################
# Exporting statistics #
########################

############################
# Playing a round of games #
############################

def PlayerVsPlayer(player1, player2, n, pathtogame):
    r1 = player1.skill
    r2 = player2.skill
    for i in range(n):
        winnerID = subprocess.call([pathtogame] + " " + str(player1.ID) + " " + str(player2.ID))
        if winnerID == player1.ID:
            r1, r2 = trueskill.rate_1vs1(r1, r2)
        else:
            r2, r1 = trueskill.rate_1vs1(r2, r1)
    player1.skill = r1
    player2.skill = r2


##################
# Database tools #
##################

def readFromDB(localPathToDB):
    connectionDB = sqlite3.connect(localPathToDB)
    connectionDB.row_factory = sqlite3.Row

    with connectionDB:
        cursorPlayers = connectionDB.cursor()
        cursorPlayers.execute("SELECT * FROM mathecamp-games.players")
        cursorHistory = connectionDB.cursor()
        for row in cursorPlayers:
            cursorHistory.execute("SELECT ? FROM mathecamp-games.history", (str(row["ID"]),))
            dictOfAllPlayers[row["ID"]] = player(row["ID"], row["playerName"], row["playerGrade"],
                                                 row["playerGender"], row["mean"], row["variance"],
                                                 row["rank"],
                                                 {entry["modelID"]: int(entry.split(",")[0]) for entry in cursorHistory if entry is not ""},
                                                 {entry["modelID"]: int(entry.split(",")[1]) for entry in cursorHistory if entry is not ""})

        cursorTeams = connectionDB.cursor()
        cursorTeams.execute("SELECT * FROM mathecamp-games.teams")
        cursorPlayerTeamRelations = connectionDB.cursor()
        for row in cursorTeams:
            cursorPlayerTeamRelations.execute("SELECT * FROM mathecamp-games.playerInTeams WHERE teamID=?", (row["ID"],))
            teamMembers = [playerID for playerID in cursorPlayerTeamRelations]
            dictOfAllTeams[row["ID"]] = team(row["ID"], row["teamName"], row["activeTeamFile"], row["teamMean"], row["teamVariance"], row["teamRank"], teamMembers)
