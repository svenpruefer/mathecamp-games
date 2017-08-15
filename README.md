# mathecamp-games

## What is it about?

This is a wrapper for executing games in batch in order to simplify testing and execution of contests between AIs for some generic game.
It is intended to be used in the Mathecamp 2017 of the Matheschülerzirkel Augsburg.
The AIs are written by the participants and this tool is used in between sessions to compare the AIs against each other.

## Features

* Executes games which can be run by a shell command needing at least four arguments, namely the names of the two players as well as the two locations for the AI files of each of the teams
* Ranks the participants according to [Trueskill](http://trueskill.org/)
* Allows for teams of players with different skills writing an AI together and compete as a team
* Persistence in a SQLite3 database

## How to use it?

### Prerequisites

* Python 3
* SQLite 3
* Trueskill

### Execution

* Clone the repository
* Set the variables correctly, at the moment within the file `start-game.py`
* Run `python3 start-game.py`

## TODOs

* Incorporate team contests
* Add support for leagues/contests
* Use CLI arguments for configuration
* Add visualization tools
* Write documentation
* Write schema for database
* Add GUI
* Add reasonable way to add, delete or update players (At the moment this can be only done in the SQLite database directly.)

## How to contribute?

Send me an email if you want to help or do a Pull Request.
