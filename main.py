#!/usr/bin/env python3
import math
import random
import sqlite3 as sql


planetType = [
    "Ice",
    "Desert",
    "Terran",
    "Desert",
    "Inferno",
    "Gas giant",
]

MAXPLANETSIZE = 10


class Planet(object):
    def __init__(self, kind=None):
        if kind == None:
            r = random.randrange(len(planetType))
            self.kind = planetType[r]
        else:
            self.kind = kind
        self.size = random.randrange(MAXPLANETSIZE) + 1

    def __repr__(self):
        return "Planet: Size {0} {1} world".format(self.size, self.kind)

starType = [
    "Brown dwarf",
    "Red dwarf",
    "Orange dwarf",
    "Yellow dwarf",
    "Blue giant",
    "White giant",
    "White supergiant",
    "White dwarf",
    "Neutron",
    "Black hole",
    "Nebula"
]

HASHADDRESS = 0

class Star(object):
    def __init__(self, x, y, hash=-1, planets=None, kind=None):
        if hash == -1:
            global HASHADDRESS
            self.hash = HASHADDRESS
            HASHADDRESS += 1
        else:
            self.hash = hash
        if planets == None:
            self.generatePlanets()
        else:
            self.planets = planets
            
        self.x = x
        self.y = y
        if kind == None:
            r = random.randrange(len(starType))
            self.kind = starType[r]
        else:
            self.kind = kind

    def generatePlanets(self):
        self.planets = []
        count = max(0, int(random.gauss(7, 5)))
        for i in range(count):
            self.planets.append(Planet())        

    def __repr__(self):
        return "{0} star at <{1:.1f},{2:.1f}>".format(self.kind, self.x, self.y)

    def distance(self, star):
        return math.sqrt(self.distance2(star))

    def distance2(self, star):
        """Returns distance squared"""
        xdist = star.x - self.x
        ydist = star.y - self.y

        return (xdist ** 2) + (ydist ** 2)

# Functions to create the universe.
def initDB(dbFile):
    conn = sql.connect(dbFile)
    c = conn.cursor()
    c.execute("create table stars (hash INTEGER UNIQUE, x REAL, y REAL, kind TEXT);")
    # XXX: Oops, we don't store planet size.  :-P
    c.execute("create table planets (star INTEGER, position INTEGER, kind TEXT);")
    # INTEGER UNIQUE basically acts as an index anyway.
    # Might want indices for planet's star, star's x and y coords...
    c.close()
    conn.commit()

def indexDB(dbFile):
    conn = sql.connect(dbFile)
    c = conn.cursor()
    c.execute('create index if not exists starcoords on stars(x,y)')
    c.execute('create index if not exists planetstars on planets(star)')
    c.close()
    conn.commit()

def generateUniverse(conn, starcount, universeSize):
    for i in range(starcount):
        if i % 100 == 0: print("Generating star ", i)
        sx = random.random() * universeSize
        sy = random.random() * universeSize
        star = Star(sx, sy)
        insertStarIntoDB(conn, star)
    conn.commit()


def insertStarIntoDB(conn, star):
    c = conn.cursor()
    for i in range(len(star.planets)):
        planet = star.planets[i]
        c.execute("insert into planets values (?, ?, ?)", (star.hash, i+1, planet.kind))
    c.execute("insert into stars values (?, ?, ?, ?);", (star.hash, star.x, star.y, star.kind))
    c.close()

#initDB('test2.db')
conn = sql.connect('tenmillion.db')


class Gamestate(object):
    def __init__(self, db, universesize=1000, starcount=10000):
        self.universeSize = universesize
        self.starCount = starcount
        self.dbFile = db
        self.dbConn = sql.connect(db)


    def getStarsWithin(self, x, y, d):
        c = self.dbConn.cursor()
        xmin = x - d
        xmax = x + d
        ymin = y - d
        ymax = y + d
        hashes = c.execute("select hash from stars where x > ? and x < ? and y > ? and y < ?;",
                           (xmin, xmax, ymin, ymax)).fetchall()
        c.close()
        stars = [self.getStar(h[0]) for h in hashes]
        return stars
        
    def getStar(self, starhash):
        c = self.dbConn.cursor()
        # This should only ever return one record...
        (h, x, y, kind) = c.execute("select * from stars where hash = ?;", (starhash,)).fetchone()
        c.close()
        p = self.getPlanetsForStar(starhash)
        return Star(x, y, hash=h, kind=kind, planets=p)
    
    def getPlanetsForStar(self, starhash):
        c = self.dbConn.cursor()
        p = c.execute("select kind from planets where star = ? order by position asc;", (starhash,)).fetchall()
        c.close()
        planets = [Planet(kind) for kind in p]
        return planets        


    def getStarAt(self, x, y):
        delta = 0.1
        s = self.getStarsWithin(x, y, delta)
        if len(s) > 0:
            return s[0]
        else:
            return False

def printStatus(gs, loc):
        star = gs.getStar(loc)
        print("You are at address {0}".format(loc))
        print(star)
        print("Planets:")
        for p in star.planets:
            print(p)
        print()
        print("Nearby stars:")
        for i in gs.getStarsWithin(star.x, star.y, 40):
            print(i)

def doCommandTravel(gs):
    print("Enter coordinates to travel to, separated by a comma:")
    while True:
        s = input("> ")
        splitted = s.split(',')
        print(splitted)
        if len(splitted) < 2:
            print("Please enter 2 numbers separated by a comma!")
        else:
            try:
                x = float(splitted[0])
                y = float(splitted[1])
                star = gs.getStarAt(x, y)
                if star:
                    print("Going to {0} ({1}) at {2}, {3}".format(star, star.hash, x, y))
                    return star.hash
                else:
                    print("There is no star there!")
            except ValueError:
                print("Not understood input")

def doCommandWarp(gs):
    print("Enter index to warp to:")
    while True:
        s = input("> ")
        try:
            r = int(s)
            if r < 0 or r >= gs.starCount:
                print("Please enter a number in range")
            else:
                return r
        except ValueError:
            print("Not understood input")


def doCommand(gs):
    while True:
        print("Enter command: (w)arp, (t)ravel, (q)uit")
        s = input("> ")
        if s[0] == 'w':
            return doCommandWarp(gs)
        elif s[0] == 't':
            return doCommandTravel(gs)
        elif s[0] == 'q':
            return -1
        else:
            print("Not understood input")

def runGame(gs):
    loc = 0
    while True:
        printStatus(gs, loc)
        loc = doCommand(gs)
        if loc == -1:
            print("Quitting")
            return

def main():
    g = Gamestate('tenthousand.db')
    runGame(g)

if __name__ == '__main__':
    main()
