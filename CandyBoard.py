#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Model for storing Candy information here

# Candy cells

import sys
import copy
import math
import os.path
import pickle

"""
Todo:
combos!!!!!!
striped candy hitting bomb
two stripes...
overcounting jelly removal for background jellies?
falling around barriers! and just dropping through holes e.g. level 32
!!!!!!! level 35 has both types
new types of empty... regular falling (drop, already mostly implemented),
    hole that hides the candy, hole that the candy can't fall into (hardest, figure out pattern)
rework entire code from Cell class... this is too dirty
mongodb
"""

class Cell(object):
    def __init__(self,jellyLevel=0):
        self.jellyLevel = int(jellyLevel)
    def __repr__(self):
        return "x" #undefined
    def __str__(self):
        return str(self.jellyLevel)+"c"
    def getJellyLevel(self):
        return self.jellyLevel
    def decJellyLevel(self):
        self.jellyLevel -= 1
    def setJellyLevel(self,level):
        self.jellyLevel = int(level)

class NonEmpty(Cell):
    pass

class Empty(Cell):
    def __init__(self,etype,contained=None,jellyLevel=0):
        self.etype = etype
        self.contained = contained #Empty(AnyCandy) to store candies... then Empty.contained <3
        super(Empty, self).__init__(jellyLevel)
    def __repr__(self):
        if self.etype == "x": return "x"
        if self.etype == "u": return "?"
    def __str__(self):
        return str(self.jellyLevel)+"e"+str(self.contained)
    def getJellyLevel(self):
        return 0
    def setContained(self,contained):
        self.contained = contained
    def getContained(self):
        return self.contained
    def isUnknown(self):
        return self.etype == "u"

class Drop(NonEmpty):
    def __repr__(self):
        return " "

class Dud(NonEmpty):
    def __repr__(self):
        return "d"
    def __str__(self):
        return str(self.jellyLevel)+"d"

class Whipped(NonEmpty):
    def __init__(self,jellyLevel=0):
        self.jellyLevel = jellyLevel #by definition
    def __repr__(self):
        return "J"
    def __str__(self):
        return str(self.jellyLevel)+"j"

class Candy(NonEmpty):
    def __init__(self,color,jellyLevel=0):
        self.color = color
        super(Candy, self).__init__(jellyLevel)
    def __str__(self):
        return str(self.jellyLevel)+self.color
    def getSpecialType(self):
        return "n" #normal
    def getColor(self):
        return self.color
    def __repr__(self):
        return self.color

class Locked(Candy):
    def __str__(self):
        return str(self.jellyLevel)+"l"+self.color

class Special(Candy):
    @classmethod
    def getSpecial(cls,prefix,color,jellyLevel=0):
        if prefix == "m": return Bomb(jellyLevel)
        elif prefix == "w": return Wrapped(color,jellyLevel)
        else:
            assert prefix == "h" or prefix == "v"
            return Striped(prefix,color,jellyLevel)

class Bomb(Special):
    def __init__(self,jellyLevel=0):
        self.jellyLevel = jellyLevel
    def __repr__(self):
        return "m"
    def __str__(self):
        return str(self.jellyLevel)+"m"

class Striped(Special):
    def __init__(self,stripeDirection,color,jellyLevel=0):
        self.stripeDirection = stripeDirection
        super(Striped, self).__init__(color,jellyLevel)
    def getStripeDirection(self):
        return self.stripeDirection
    def __str__(self):
        return str(self.jellyLevel)+self.stripeDirection+self.color

class Wrapped(Special):
    def __init__(self,color,jellyLevel=0):
        self.exploded = False
        super(Wrapped, self).__init__(color,jellyLevel)
    def __str__(self):
        return str(self.jellyLevel)+"w"+self.color
    def hasExploded(self):
        return self.exploded
    def setExploded(self):
        self.exploded = True

class CandyBoard(object):
    def __init__(self,goal,test=False,maxDepth=-1):
        self.empty = ["x"]
        self.dropName = [" "]
        self.candyNames = ["g","b","r","p","y","o","m"]
        self.bigJelly = ["J"] #any name for bigJelly
        self.dudName = ["d"]
        self.pieceNames = self.candyNames + self.bigJelly + self.empty + self.dudName + self.dropName
        self.specialNames = ["h","v","w"]
        self.jellyNames = ["1","2"]
        self.lockedName = ["l"]
        self.prefixes = self.specialNames + self.jellyNames + self.lockedName
        self.goals = ["score","jel","ing","jeling"]
        assert(goal in self.goals)
        self.goal = goal
        self.horizontalBound = 9 #property of the game's design
        self.verticalBound = 9
        self.checks = 0
        self.maxDepth = maxDepth
        if test:
            #initialize board here?
            self.runTests() #is this a dirty way of testing?
        self.printInstructions()

    def getPiece(self,row,col,board=None):
        if board == None:
            #print "Default getPiece..."
            board = self.boardTable
        return board[row][col]

    def printLines(self,board=None):
        if board == None:
            board = self.boardTable
        assert(self.verifyBoard()) ## remove in production
        print ""
        rowmarker = 0
        t = " |"
        for i in xrange(len(self.boardTable[0])):
            t += str(i)+"|"
        print t
        for row in board:
            s = str(rowmarker)+"|"
            for cell in row:
                s += (repr(cell) + "|")
            print s
            rowmarker += 1

    def isValidLocation(self,row,col):
        if not (0 <= row and row < self.verticalBound): return False
        if not (0 <= col and col < self.horizontalBound): return False
        return True

    def checkMatchInDirection(self,piece,row,col,drow,dcol,board=None):
        if board == None:
            print "Default checkMatchInDirection..."
            board = self.boardTable
        assert(drow in [-1,0,1] and dcol in [-1,0,1] and (abs(drow) != abs(dcol)))
        assert(self.isValidLocation(row,col))
        if isinstance(piece, Bomb): return 0
        pieceColor = piece.getColor()
        matches = 0
        while(self.isValidLocation(row,col) and self.isValidLocation(row+drow,col+dcol)):
            nextPiece = self.getPiece(row+drow,col+dcol,board)
            if not isinstance(nextPiece, Candy) or isinstance(nextPiece,Bomb): break
            if nextPiece.getColor() == pieceColor: matches += 1
            else: break
            row = row+drow
            col = col+dcol
        return matches

    def checkMatchFromPiece(self,row,col,board=None):
        if board == None:
            print "Default checkMatchFromPiece..."
            board = self.boardTable
        assert(self.isValidLocation(row,col))
        piece = self.getPiece(row,col,board)
        if not isinstance(piece, Candy):
            print "We're checking matches for a non-candy piece."
            return (0,0,0,0) #no matches possible
        l = self.checkMatchInDirection(piece,row,col,0,-1,board)
        r = self.checkMatchInDirection(piece,row,col,0,1,board)
        u = self.checkMatchInDirection(piece,row,col,-1,0,board)
        d = self.checkMatchInDirection(piece,row,col,1,0,board)
        return (l,r,u,d)

    def markToRemoveInDirection(self,row,col,drow,dcol,count):
        assert(drow in [-1,0,1] and dcol in [-1,0,1] and (abs(drow) != abs(dcol)))
        assert(self.isValidLocation(row,col))
        if count == 0: return []
        toRemove = []
        for i in xrange(1,count+1):
            assert(self.isValidLocation(row+i*drow,col+i*dcol))
            toRemove += [(row+i*drow,col+i*dcol)]
        assert(len(toRemove) == count)
        return toRemove

    def drop(self,board=None):
        if board == None:
            print "Default drop..."
            board = self.boardTable
        dropped = []
        dudsRemoved = 0
        for col in xrange(self.horizontalBound):
            if isinstance(board[self.verticalBound-1][col],Dud):
                dudsRemoved += 1
                jelly = board[self.verticalBound-1][col].getJellyLevel()
                board[self.verticalBound-1][col] = Drop(jelly)
            for row in xrange(self.verticalBound-1,0,-1):
                assert self.isValidLocation(row,col) and self.isValidLocation(row-1,col)
                piece = self.getPiece(row,col,board)
                upiece = self.getPiece(row-1,col,board)
                if isinstance(piece,Drop) and not (isinstance(upiece,Drop) or isinstance(upiece,Whipped) or isinstance(upiece,Locked)): ###locked candies?
                    if isinstance(upiece, Empty):
                        temp = upiece.getContained()
                        if temp == None: continue
                        upiece.setContained(None)
                        upiece = temp
                    jelly = piece.getJellyLevel()
                    if isinstance(piece,Empty):
                        piece.setContained = upiece #removed copy.deepcopy(upiece)
                    else:
                        board[row][col] = upiece #removed copy.deepcopy(upiece)
                        board[row][col].setJellyLevel(jelly)
                        dropped += [(row,col)] #moved dropped here from bottom of big if statement
                    if not isinstance(upiece, Empty):
                        ujelly = upiece.getJellyLevel()
                        board[row-1][col] = Drop(jelly)
        return (dropped,dudsRemoved)

    def markToRemove(self,toRemove,board=None):
        if board == None:
            print "Default markToRemove..."
            board = self.boardTable
        piecesRemoved = 0
        jellyRemoved = 0
        for item in toRemove:
            row,col = item[0],item[1]
            assert self.isValidLocation(row,col)
            piece = self.getPiece(row,col,board)
            if not isinstance(piece,Drop):
                jelly = piece.getJellyLevel()
                if jelly > 0:
                    jellyRemoved += 1
                    piece.setJellyLevel(jelly - 1)
                board[row][col] = Drop(jelly)
                piecesRemoved += 1
        return (piecesRemoved,jellyRemoved)

    def remove(self,toRemove,color=None,board=None):
        if board == None:
            print "Default remove..."
            board = self.boardTable
        piecesRemoved = 0
        jellyRemoved = 0
        specialCheck = copy.copy(toRemove)
        while specialCheck: #treat like a stack
            location = specialCheck.pop()
            row,col = location[0],location[1]
            assert self.isValidLocation(row,col)
            piece = self.getPiece(row,col,board)
            extra = []
            if isinstance(piece,Bomb):
                for _row in xrange(self.verticalBound):
                    for _col in xrange(self.horizontalBound):
                        assert self.isValidLocation(_row,_col)
                        _piece = self.getPiece(_row,_col,board)
                        if isinstance(_piece,Candy) and not isinstance(_piece,Bomb):
                            if _piece.getColor() == color:
                                extra += [(_row,_col)]
            elif isinstance(piece,Striped):
                d = piece.getStripeDirection()
                if d == "h":
                    for _col in xrange(self.horizontalBound):
                        extra += [(row,_col)]
                else:
                    assert d == "v"
                    for _row in xrange(self.verticalBound):
                        extra += [(_row,col)]
            elif isinstance(piece,Wrapped):
                for drow in [-1,0,1]:
                    for dcol in [-1,0,1]:
                        if not (piece.hasExploded() and drow == 0 and dcol == 0):
                            extra += [(row+drow,col+dcol)]
                if not piece.hasExploded: piece.setExploded()
            for pair in extra:
                if self.isValidLocation(pair[0],pair[1]):
                    if pair not in toRemove:
                        toRemove += [pair]
                        specialCheck += [pair]
        (piecesRemoved,jellyRemoved) = self.markToRemove(toRemove,board)
        (toCheck,dudsRemoved) = self.drop(board)
        return (toCheck,dudsRemoved,jellyRemoved,piecesRemoved)

    def processMatches(self,matches,board=None):
        if board == None:
            print "Default processMatches..."
            board = self.boardTable
        piecesRemoved = 0
        jellyRemoved = 0
        dudsRemoved = 0
        toRemove = []
        #assert(self.boardTable != copyTable) #they were deep copied
        #if not matches:
            #add all locations on board to matches
            #pass
        while matches: #while matches is not empty #matches is a list of tuples (row,col)
            match = matches.pop() #safe by loop guard
            (row,col) = match
            piece = self.getPiece(row,col,board)
            if not isinstance(piece, Candy): continue
            result = self.checkMatchFromPiece(row,col,board)
            if not result: continue
            (l,r,u,d) = result
            if not (l + r + 1 > 2 or u + d + 1 > 2): continue
            if (l + r + 1 > 4 or u + d + 1 > 4):
                board[row][col] = Bomb(piece.getJellyLevel())
            elif (l + r + 1 > 2 and u + d + 1 > 2):
                board[row][col] = Wrapped(piece.getColor(),piece.getJellyLevel())
            elif (l + r + 1 > 3 or u + d + 1 > 3):
                if (l + r + 1 > 3):
                    board[row][col] = Striped("v",piece.getColor(),piece.getJellyLevel())
                else:
                    assert(u + d + 1 > 3)
                    board[row][col] = Striped("h",piece.getColor(),piece.getJellyLevel())
            elif (l + r + 1 > 2 or u + d + 1 > 2):
                toRemove.append((row,col))
                pass #remove the piece
            if (l + r + 1 > 2): #remove pieces along horizontal line
                toRemove += self.markToRemoveInDirection(row,col,0,-1,l) #l
                toRemove += self.markToRemoveInDirection(row,col,0,1,r) #r
            if (u + d + 1 > 2): #remove pieces along vertical line
                toRemove += self.markToRemoveInDirection(row,col,-1,0,u) #u
                toRemove += self.markToRemoveInDirection(row,col,1,0,d) #d
        jellyRemoval = []
        for location in toRemove:
            (row,col) = location
            adj = [(-1,0),(1,0),(0,-1),(0,1)]
            for dloc in adj:
                drow,dcol = dloc[0],dloc[1]
                if self.isValidLocation(row+drow,col+dcol):
                    _piece = self.getPiece(row+drow,col+dcol,board)
                    if not isinstance(_piece,Drop) and isinstance(_piece,Whipped) and (row+drow,col+dcol) not in toRemove:
                        board[row+drow][col+dcol] = Drop(int(_piece.getJellyLevel())+1)
                        #jellyLevel + 1 above because it's going to get decremented
                        #jellyRemoved += 1
                        jellyRemoval += [(row+drow,col+dcol)]
                        #removeCopy += [(row+drow,col+dcol)]
        toRemove += jellyRemoval
        #for col in xrange(self.horizontalBound):
        #    row = self.verticalBound - 1
        #    if isinstance(self.getPiece(row,col,board),Dud):
        #        toRemove += [(row,col)]
        #        dudsRemoved += 1
        result = self.remove(toRemove,board=board) #no bomb so no color needed
        matches = result[0]
        dudsRemoved += result[1]
        jellyRemoved += result[2]
        piecesRemoved += result[3]
        if matches:
            newResult = self.processMatches(matches,board)
            dudsRemoved += newResult[0]
            jellyRemoved += newResult[1]
            piecesRemoved += newResult[2]
        #print (dudsRemoved,jellyRemoved,piecesRemoved)
        return (dudsRemoved,jellyRemoved,piecesRemoved)

    def physicalSwap(self,row1,col1,row2,col2,board=None):
        if board == None:
            board = self.boardTable
        assert(self.isValidLocation(row1,col1) and self.isValidLocation(row2,col2))
        piece1 = self.getPiece(row1,col1,board)
        piece2 = self.getPiece(row2,col2,board)
        assert(isinstance(piece1,Candy) and isinstance(piece2,Candy))
        jelly1 = piece1.getJellyLevel()
        jelly2 = piece2.getJellyLevel()
        temp = copy.deepcopy(piece1)
        board[row1][col1] = piece2
        board[row2][col2] = temp
        board[row1][col1].setJellyLevel(jelly1)
        board[row2][col2].setJellyLevel(jelly2)

    def swap(self,row1,col1,row2,col2,board=None):
        #dudsRemoved = 0
        #jellyRemoved = 0
        #piecesRemoved = 0
        if board == None:
            print "Default swap..."
            board = self.boardTable
        assert(self.isValidLocation(row1,col1) and self.isValidLocation(row2,col2))
        distance = math.sqrt(float(abs(row2 - row1))**2+(float(abs(col2-col1)))**2)
        if distance != 1:
            print "Non adjacent pieces swapped."
            return False #try to exit cleanly?
            #sys.exit()
        piece1 = self.getPiece(row1,col1,board)
        piece2 = self.getPiece(row2,col2,board)
        adj = [(-1,0),(1,0),(0,-1),(0,1)]
        for dloc in adj:
            drow,dcol = dloc[0],dloc[1]
            if self.isValidLocation(row1+drow,col1+dcol):
                _piece = self.getPiece(row1+drow,col1+dcol,board)
                if isinstance(_piece,Drop):
                    return False
            if self.isValidLocation(row2+drow,col2+dcol):
                _piece = self.getPiece(row2+drow,col2+dcol,board)
                if isinstance(_piece,Drop):
                    return False
        if isinstance(piece1,Drop) or isinstance(piece2,Drop):
            return False
        if not isinstance(piece1,Candy) or not isinstance(piece2,Candy):
            #print "Non candy pieces given to swap function."
            return False
        if isinstance(piece1,Dud) or isinstance(piece2,Dud):
            return False
        if isinstance(piece1,Locked) or isinstance(piece2,Locked):
            #print "Can't swap locked candy."
            return False
        if isinstance(piece1,Special) and isinstance(piece2,Special):
            #print "Two special candies swapped... not yet implemented."
            types = (str(type(piece1)),str(type(piece2)))
            if ("Stripe" in types and "Wrapper" in types):
                print "Stripe/Wrapper"
                #pass # 3 wide, 3 tall sweep across board
            if (types == ("Stripe","Stripe")):
                print "Stripe/Stripe"
            if ((isinstance(piece1,Bomb) and isinstance(piece2,Striped)) or (isinstance(piece2,Bomb) and isinstance(piece1,Striped))):
                if isinstance(piece1,Bomb): color = piece2.getColor()
                else: color = piece1.getColor
                jelly1 = piece1.getJellyLevel()
                board[row1][col1] = Drop(jelly1)
                jelly2 = piece2.getJellyLevel()
                board[row2][col2] = Drop(jelly2)
                removal = []
                directions = ["h","v"]
                i = 0
                for row in xrange(self.verticalBound):
                    for col in xrange(self.horizontalBound):
                        if (row,col) == (row1,col1) or (row,col) == (row2,col2): continue
                        piece = self.getPiece(row,col,board)
                        if isinstance(piece,Bomb): continue
                        if isinstance(piece,Candy) and piece.getColor() == color:
                            jelly = self.getPiece(row,col,board).getJellyLevel()
                            board[row][col] = Striped(directions[i],color,jelly)
                            removal += [(row,col)]
                            i = 1 - i
                (matches,dudsRemoved,jellyRemoved,piecesRemoved) = self.remove(removal,board=board)
                if matches:
                    newResult = self.processMatches(matches,board)
                    dudsRemoved += newResult[0]
                    jellyRemoved += newResult[1]
                    piecesRemoved += newResult[2]
                return (dudsRemoved,jellyRemoved,piecesRemoved)
            if ("Bomb" in types and "Wrapper" in types):
                print "Bomb/Wrapper"
                pass
            if (isinstance(piece1,Bomb) and isinstance(piece2,Bomb)):
                print "Double bomb found!!!"
                #sys.exit()
                removal = []
                for row in xrange(self.verticalBound):
                    for col in xrange(self.horizontalBound):
                        removal += [(row,col)]
                (toCheck,dudsRemoved,jellyRemoved,piecesRemoved) = self.remove(removal,board=board)
                return (dudsRemoved,jellyRemoved,piecesRemoved)
            if (types == ("Wrapper","Wrapper")):
                print "Wrapper/Wrapper"
        if isinstance(piece1,Bomb) or isinstance(piece2,Bomb): #elif instead?
            if isinstance(piece1,Bomb):
                color = piece2.getColor()
                (matches,dudsRemoved,jellyRemoved,piecesRemoved) = self.remove([(row1,col1)],color=color,board=board)
            else:
                assert isinstance(piece2,Bomb)
                color = piece1.getColor()
                (matches,dudsRemoved,jellyRemoved,piecesRemoved) = self.remove([(row2,col2)],color=color,board=board)
            if matches:
                newResult = self.processMatches(matches,board)
                dudsRemoved += newResult[0]
                jellyRemoved += newResult[1]
                piecesRemoved += newResult[2]
            return (dudsRemoved,jellyRemoved,piecesRemoved)
        self.physicalSwap(row1,col1,row2,col2,board)
        (dudsRemoved,jellyRemoved,piecesRemoved) = self.processMatches([(row1,col1),(row2,col2)],board)
        if (dudsRemoved,jellyRemoved,piecesRemoved) == (0,0,0):
            self.physicalSwap(row1,col1,row2,col2,board)
            return False
        return (dudsRemoved,jellyRemoved,piecesRemoved)

    def board2string(self,board=None):
        s = ""
        if board == None:
            board = self.boardTable
        for row in xrange(self.verticalBound):
            for col in xrange(self.horizontalBound):
                s += str(self.getPiece(row,col,board))
        return s

    def solve(self,copyTable,moveSequence,depth=1):
        #self.printLines()
        #copyTable = copy.deepcopy(copyTable)
        s = self.board2string(copyTable)
        if s in self.solveDictionary:
            #print "Found result in s!"
            self.found += 1
            return self.solveDictionary.get(s)
        else:
            self.original += 1
            #print "Not in s."
        if self.maxDepth != -1 and depth > self.maxDepth: return ((0,0,0),[])
        #print moveSequence
        currentMax = (0,0,0)
        currentMaxAve = (0,0,0)
        bestMoveSequence = []
        toVisit = []
        moveSequence = copy.deepcopy(moveSequence)
        for row in xrange(self.verticalBound):
            for col in xrange(self.horizontalBound):
                if self.isValidLocation(row+1, col):
                    toVisit += [(row,col,row+1,col)]
                if self.isValidLocation(row,col+1):
                    toVisit += [(row,col,row,col+1)]
        #print len(toVisit)
        tempTable = copy.deepcopy(copyTable)
        while toVisit:
            if (depth == 1 and len(toVisit) % 2 == 0): print "="*(len(toVisit)/2)
            (row1,col1,row2,col2) = toVisit.pop()
            check = self.swap(row1,col1,row2,col2,tempTable) #or something similar
            #if (self.checks % 100000 == 0): print "Check %d" % (self.checks)
            if check and check != (0,0,0):
                self.checks += 1
                #print "Check %d" % (self.checks)
                tempMove = (row1,col1,row2,col2)
                moveSequence.append(tempMove)
                (recScore,recMoveSequence) = self.solve(tempTable,moveSequence,depth+1)
                recScore = tuple(map(lambda x, y: x + y, recScore, check))
                moveSequence.pop()
                size = len(recMoveSequence) + 1
                aveScore = (float(recScore[0])/size,float(recScore[1])/size,float(recScore[2])/size) #make prettier?
                assert size != 0
                if aveScore > currentMaxAve:
                    currentMaxAve = aveScore
                    currentMax = recScore
                    bestMoveSequence = [tempMove] + recMoveSequence
                tempTable = copy.deepcopy(copyTable)
        #maxScore = tuple(map(lambda x, y: x + y, maxScore, currentMax))
        self.solveDictionary[s] = (currentMax,bestMoveSequence)
        return (currentMax,bestMoveSequence)

    def solveWrapped(self,printing=True):
        #visited = []
        if os.path.isfile("database.pkl"):
            self.solveDictionary = pickle.load( open( "database.pkl", "rb" ) )
        else: self.solveDictionary = dict()
        self.found = 0
        self.original = 0
        copyTable = copy.copy(self.boardTable)
        moveSequence = []
        #print "="*(144/2)
        (maxScore,moveSequence) = self.solve(copyTable,moveSequence)
        if self.maxDepth == -1: pickle.dump( self.solveDictionary, open( "database.pkl", "wb" ) )
        self.printLines()
        if printing:
            print "From all the information available, the best score possible is %s. (removal of (duds,jelly,pieces))." % str(maxScore)
            print "You can do that with the following moves:"
            print moveSequence
            print "It took %d trials to find out that information. :)" % (self.checks)
            print "%d percent of solve calls were found in the database!" % (100 * float(self.found) / (self.original+self.found))
            if self.maxDepth == -1:
                print "We now have %d entries in our database. Thanks for the sample!" % (len(self.solveDictionary))
        return moveSequence

    def getMatches(self): #blindly check everything
        #print "getMatches not yet implemented... returns True for now"
        return [] #implement later when doing swappable pieces and stuff

    def verifyChunkLine(self, line):
        if not (len(line) == 9):
            print "Invalid line length %d in verifyChunkLine." % len(line)
            return False
        for chunk in line:
            if not isinstance(chunk, Cell):
                print "Chunk does not contain a cell in verifyChunkLine."
                return False
        return True

    def verifyBoard(self,initial=False):
        #check if all input is valid
        if not (len(self.boardTable) == 9):
            print "Board does not have 9 rows."
            return False
        for line in self.boardTable:
            if not self.verifyChunkLine(line):
                print "Invalid cell line in verifyBoard:"
                print line
                return False
        #if initial: return (self.getMatches() == [])
        return True

    def chunkToPiece(self,chunk):
        assert(isinstance(chunk, str))
        size = len(chunk)
        if (size == 1):
            pieceName = chunk
            if pieceName not in self.pieceNames:
                print "Invalid candy letter: %c" % pieceName
                return False
            elif pieceName == "m": cell = Bomb()
            elif pieceName in self.dropName: cell = Drop()
            elif pieceName in self.bigJelly: cell = Whipped()
            elif pieceName in self.empty: cell = Empty("x")
            elif pieceName in self.dudName: cell = Dud()
            else: cell = Candy(pieceName)
        elif (size == 2):
            prefix = chunk[0]
            pieceName = chunk[1]
            if prefix not in self.prefixes:
                print "Invalid prefix: %c" % prefix
                return False
            if pieceName not in self.pieceNames:
                print "Invalid piece name: %c" % pieceName
                return False
            if pieceName in self.candyNames:
                if prefix in self.lockedName: cell = Locked(pieceName)
                elif prefix in self.jellyNames: cell = Candy(pieceName,prefix)
                else:
                    assert(prefix in self.specialNames)
                    cell = Special.getSpecial(prefix,pieceName)
            else:
                if prefix in self.lockedName: cell = Locked(pieceName)
                assert(prefix not in self.lockedName) #no locked duds
                assert(prefix not in self.specialNames) #no special duds
                assert(prefix in self.jellyNames) #only possible dud
        elif (size == 3):
            jellySize = chunk[0]
            prefix = chunk[1]
            pieceName = chunk[2]
            if jellySize not in self.jellyNames:
                print "Not a valid jelly size: %c" % jellySize
                return False
            if prefix not in self.prefixes:
                print "Invalid prefix: %c" % prefixes
                return False
            elif prefix in self.jellyNames:
                print "You can't have two prefixes for a lock/jelly size."
                return False
            if pieceName not in self.pieceNames:
                print "Invalid piece name: %c" % pieceName
                return False
            cell = Special.getSpecial(prefix,pieceName,jellySize)
        else:
            print "Chunk of invalid size passed to chunkToPiece."
            return False
        return cell

    def rawLineToCellLine(self,line):
        #turn a line into a list of cell objects
        size = len(line)
        i = 0
        chunkLine = []
        while i < size:
            if line[i] in self.prefixes: #prefixes = special, jelly, locked
                if not (i + 1 < size):
                    print "Prefix at end of line."
                    return False
                if (line[i+1] in self.prefixes):
                    if not (i + 2 < size):
                        print "Two prefixes at the end of the line."
                        return False
                    if not (line[i+2] in self.pieceNames):
                        print "Invalid piece \"%c\" at index %d." % (line[i+2],i+2)
                        return False
                    #print "3Passing piece %s to rawLine..." % line[i:i+2+1] ###
                    chunk = self.chunkToPiece(line[i:i+2+1])
                    i += 3
                else:
                    if not (line[i+1] in self.pieceNames):
                        print "Invalid piece \"%c\" at index %d." % (line[i+1],i+1)
                        return False
                    #print "2Passing piece %s to rawLine..." % line[i:i+1+1] ###
                    chunk = self.chunkToPiece(line[i:i+1+1])
                    i += 2
            else:
                if not (line[i] in self.pieceNames):
                    print "Invalid piece \"%c\" at index %d." % (line[i],i)
                    return False
                #print "1Passing piece %s to rawLine..." % line[i] ###
                chunk = self.chunkToPiece(line[i])
                i += 1
            if not chunk: return False
            chunkLine.append(chunk)
        assert(len(chunkLine) == 9)
        return chunkLine

    def getBoardTable(self,sample=[]):
        #data = ["2b2g2b2r2p2p2y2o2b","2r2g2o2o2g2b2g2y2y","2y2r2o2y2g2p2r2r2g",
        #"xypoygbrx","xrpgxyoox","xbbgpmbbx","3332y2g2b333","3332y2p2y333",
        #"3332b2b2o333"] #board from example.png
        self.boardTable = []
        i = 0
        if not sample:
            print "Enter line ((jellyLevel/locked,)special,)piece (q to exit)."
            #print "Enter anything for the candy color for a bomb."
            print "Enter m for a bomb."
        while (i < self.verticalBound):
            line = sample[i] if sample else raw_input()
            if (line == "q"):
                print "Quitting..."
                sys.exit(0)
            chunkLine = self.rawLineToCellLine(line)
            if chunkLine:
                self.boardTable.append(chunkLine)
                i += 1
            elif sample: sys.exit()
            else: print "That line was invalid. Try again."
        self.verifyBoard()

    def processUnknowns(self,board=None):
        if board == None:
            board = self.boardTable
        unknownPieces = []
        for row in xrange(self.verticalBound):
            for col in xrange(self.horizontalBound):
                piece = self.getPiece(row,col,board)
                if (isinstance(piece,Empty) and piece.isUnknown) or isinstance(piece,Drop):
                    #print "Added unknown piece (%d,%d)." % (row,col)
                    unknownPieces.append((row,col))
        if not unknownPieces: return
        checkPieces = copy.copy(unknownPieces)
        self.printLines()
        while unknownPieces:
            (row,col) = unknownPieces.pop(0) #get from front of list
            print "We need to know the piece at location (%d,%d). (0-7 indexed)" % (row,col)
            newChunk = raw_input("Enter the \"piece chunk\" here:")
            if newChunk == "q":
                print "Quitting..."
                sys.exit(0)
            piece = self.chunkToPiece(newChunk)
            if not piece:
                print "Something went wrong. Try again."
                unknownPieces.insert(0,(row,col)) #put back on front of list
            else:
                self.boardTable[row][col] = piece
        (duds,jelly,pieces) = self.processMatches(checkPieces)
        if (duds,jelly,pieces) != (0,0,0): self.processUnknowns(board) #repeat

    def autoInput(self): #computer assisted
        while True:
            self.getBoardTable()
            board = self.boardTable
            self.printLines()
            moves = self.solveWrapped()
            if not moves:
                print "Uh oh... it looks like the algorithm failed! :( Try restarting the program."
                return
            coords = raw_input("Are you ready to type in the new board? (n/q to quit)")
            if (coords == "q" or coords == "n"):
                print "Quitting..."
                sys.exit(0)
            self.checks = 0
            #for move in moves:
            #    (row1,row2,col1,col2) = move
            #    self.swap(row1,col1,row2,col2)
            #self.processUnknowns(board)

    def liveInput(self): #manual, for debugging?
        self.getBoardTable()
        board = self.boardTable
        while True:
            self.printLines()
            coords = raw_input("Enter row1,col1,row2,col2 for swap or q to quit.")
            if (coords == "q"):
                print "Quitting..."
                sys.exit(0)
            coordsList = coords.split(',')
            if len(coordsList) != 4:
                print "You need to enter 4 coordinates. Try again."
                continue
            for i in xrange(len(coordsList)):
                coordsList[i] = int(coordsList[i])
            (row1,col1,row2,col2) = coordsList
            if not (self.isValidLocation(row1,col1) and self.isValidLocation(row2,col2)):
                print "Invalid coordinates entered. Try again."
                continue
            result = self.swap(row1,col1,row2,col2)
            if not result:
                print "Failed to swap the given coordinates. Try again."
                continue
            (duds,jelly,pieces) = result
            print "(duds,jelly,pieces)"
            print (duds,jelly,pieces)
            #self.processUnknowns(board)

        ###parse user data, do the swap
        ###search for all isUnknowns in the map, prompt for what they now are one at a time

    def printInstructions(self):
        print "Instructions..."

    def runTests(self):
        sample = ["rbdgpbgrr","godyryppb","bbdyvgpror","rpdrrpbyo","brdoJyryd",
            "rgdbJrrpr","bbdJJJpyo","oJJJJJJJb","JJJJJJJJJ"]
        self.getBoardTable(sample)
        self.boardTable[7][2] = Drop()
        self.boardTable[8][2] = Drop()
        self.printLines()
        #swap 2 that don't do anything
        #swap 2 that have a match
        #self.printLines()
        pass
