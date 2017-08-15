import sqlite3
import argparse
import trueskill
import subprocess
import pdb
import os


##############
# Parameters #
##############

class GlobalParameters:
    def __init__(self, localPathToGame=r"/test-game.sh", localPathToDB=r"./mathecamp-games.sqlite",
                 localPathForOutputs=r"/output/"):
        self.pathToGame = localPathToGame
        self.pathToDB = localPathToDB
        self.pathForOutputs = localPathForOutputs
        self.dictOfAllTeams = {}
        self.dictOfAllPlayers = {}
        self.roundsPlayedSoFar = 0


################################
# Parse command line arguments #
################################

# TODO Parse and forward CLI arguments

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
        self.skill = trueskill.Rating(mean, variance)
        self.history = [[history_means[i], history_variances[i]] for i in range(len(history_means))]
        self.teams = []

class team:
    def __init__(self, ID, name, activeTeamFilePath, mean, variance, rank, teamMembers, history_means,
                 history_variances):
        self.ID = ID
        self.name = name
        self.activeTeamFilePath = activeTeamFilePath
        self.skill = trueskill.Rating(mean, variance)
        self.rank = rank
        self.teamMembers = teamMembers
        self.history = [[history_means[i], history_variances[i]] for i in range(len(history_means))]


########################
# Exporting statistics #
########################

def WriteOutputToConsole(globalParameters):
    pass
    # TODO Write some output to console


############################
# Playing a round of games #
############################

def PlayerVsPlayer(player1, player2, n, localPathToGame):
    r1 = player1.skill
    r2 = player2.skill
    for i in range(n):
        winnerID = int(subprocess.check_output([os.path.dirname(os.path.realpath(__file__)) + localPathToGame, str(player1.ID), str(player2.ID)]).decode("utf8").strip()) # TODO Forward CLI arguments and allow for bot files
        if winnerID == player1.ID:
            r1, r2 = trueskill.rate_1vs1(r1, r2)
        else:
            r2, r1 = trueskill.rate_1vs1(r2, r1)

    # Update Trueskill level
    player1.skill = r1
    player2.skill = r2
    player1.rank = player1.skill.mu - 3 * player1.skill.sigma
    player2.rank = player2.skill.mu - 3 * player2.skill.sigma

    # Update History
    player1.history.append([player1.skill.mu, player1.skill.sigma])
    player2.history.append([player2.skill.mu, player2.skill.sigma])


def CreateListOfAllGames(localDictOfAllPlayersOrTeams):
    localListOfAllGames = []
    for id1 in localDictOfAllPlayersOrTeams.keys():
        for id2 in localDictOfAllPlayersOrTeams.keys():
            if id1 != id2:
                localListOfAllGames.append([id1, id2])
    return localListOfAllGames


def PlayAllGamesBetweenPlayersInList(localListOfGamesToPlay, n, dictOfAllPlayers, pathToGame):
    for pairOfPlayers in localListOfGamesToPlay:
        PlayerVsPlayer(dictOfAllPlayers[pairOfPlayers[0]], dictOfAllPlayers[pairOfPlayers[1]], n, pathToGame)


# TODO Write team games

##################
# Database tools #
##################

def ReadFromDB(globalParameters):
    connectionDB = sqlite3.connect(globalParameters.pathToDB)
    connectionDB.row_factory = sqlite3.Row

    with connectionDB:
        cursorPlayers = connectionDB.cursor()
        cursorPlayers.execute("SELECT * FROM 'players'")
        cursorHistoryPlayers = connectionDB.cursor()
        for row in cursorPlayers:
            cursorHistoryPlayers.execute("SELECT * FROM 'history_players' WHERE playerID = ?", (str(row["ID"]),))
            rowHistory = cursorHistoryPlayers.fetchone()
            globalParameters.dictOfAllPlayers[row["ID"]] = player(row["ID"], row["playerName"], row["playerGrade"],
                                                                  row["playerGender"], row["mean"], row["variance"],
                                                                  row["rank"],
                                                                  [entry for entry in rowHistory[1].split(",")],
                                                                  [entry for entry in rowHistory[2].split(",")])

        cursorTeams = connectionDB.cursor()
        cursorTeams.execute("SELECT * FROM 'teams'")
        cursorPlayerTeamRelations = connectionDB.cursor()
        cursorHistoryTeams = connectionDB.cursor()
        for row in cursorTeams:
            cursorPlayerTeamRelations.execute("SELECT * FROM 'playerInTeams' WHERE teamID = ?", (row["ID"],))
            teamMembersFromTable = cursorPlayerTeamRelations.fetchall()
            cursorHistoryTeams.execute("SELECT * FROM 'history_teams' WHERE teamID = ?",
                                       (str(row["ID"]),))
            rowHistory = cursorHistoryTeams.fetchone()
            teamMembers = [playerID for playerID in teamMembersFromTable]
            globalParameters.dictOfAllTeams[row["ID"]] = team(row["ID"], row["teamName"], row["activeTeamFile"],
                                                              row["teamMean"], row["teamVariance"], row["teamRank"],
                                                              teamMembers,
                                                              [entry for entry in rowHistory[1].split(",")],
                                                              [entry for entry in rowHistory[2].split(",")])

        cursorRounds = connectionDB.cursor()
        cursorRounds.execute("SELECT * FROM 'tournament'")
        rounds = cursorRounds.fetchone()
        globalParameters.roundsPlayedSoFar = int(rounds[0])


def WriteToDB(globalParameters):
    connectionDB = sqlite3.connect(globalParameters.pathToDB)
    connectionDB.row_factory = sqlite3.Row

    with connectionDB:
        cursorPlayers = connectionDB.cursor()
        cursorHistoryPlayers = connectionDB.cursor()
        for playerId, player in globalParameters.dictOfAllPlayers.items():
            cursorPlayers.execute("UPDATE 'players' set mean = ?, variance = ?, rank = ? WHERE ID = ? ",
                                  (player.skill.mu, player.skill.sigma, player.rank, player.ID))
            playerHistoryStringMeans = ','.join(map(str, list(zip(*player.history))[0]))
            playerHistoryStringVariances = ','.join(map(str, list(zip(*player.history))[1]))
            playerHistoryStringRanks = ','.join(map(str, [float(x) - 3 * float(y) for x, y in player.history]))
            cursorHistoryPlayers.execute(
                "UPDATE 'history_players' set mean = ?, variance = ?, rank = ? WHERE playerID = ?",
                (playerHistoryStringMeans, playerHistoryStringVariances, playerHistoryStringRanks, player.ID,))

        cursorTeams = connectionDB.cursor()
        cursorHistoryTeams = connectionDB.cursor()
        for teamId, team in globalParameters.dictOfAllTeams.items():
            cursorTeams.execute("UPDATE 'teams' set teamMean = ?, teamVariance = ?, teamRank = ? WHERE ID = ? ",
                                (team.skill.mu, team.skill.sigma, team.rank, team.ID))
            teamHistoryStringMeans = ','.join(map(str, list(zip(*team.history))[0]))
            teamHistoryStringVariances = ','.join(map(str, list(zip(*team.history))[1]))
            teamHistoryStringRanks = ','.join(map(str, [float(x) - 3 * float(y) for x, y in team.history]))
            cursorHistoryTeams.execute("UPDATE 'history_teams' set mean = ?, variance = ?, rank = ? WHERE teamID = ?", (
            teamHistoryStringMeans, teamHistoryStringVariances, teamHistoryStringRanks, team.ID,))

        cursorRounds = connectionDB.cursor()
        cursorRounds.execute("UPDATE 'tournament' set rounds = ?", (globalParameters.roundsPlayedSoFar + 1,))


###############
# Main method #
###############

def PlayOneRoundForAll(n):
    """
    This function initializes global parameters, reads the database, plays games between all (ordered pairs of) players
    and teams, respectively, and then writes the results to the DB. It is the main function of the whole program.
    :param n: Amount of games between two players per round
    :type n: int
    :return: void
    """
    globalParameters = GlobalParameters()
    ReadFromDB(globalParameters)
    PlayAllGamesBetweenPlayersInList(CreateListOfAllGames(globalParameters.dictOfAllPlayers), n,
                                     globalParameters.dictOfAllPlayers, globalParameters.pathToGame)
    WriteToDB(globalParameters)
    WriteOutputToConsole(globalParameters)


PlayOneRoundForAll(1)
