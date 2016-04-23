import pycosat

'''
This file contains two classes for turning lands and manaCosts into boolean values corresponding to whether the lands can cast the mana
As far as I can tell, the SAT reduction is much faster for reasonable inputs.
'''

class HelperMethods():
	#makes a 2d array that lines up mana with the lands that can tap for that mana type.	
	def buildCastsArray(self, lands, cost):
		arr = []
		for land in lands:
			line = []
			for c in cost:
				if tapsFor(land, c):
					line.append(1)
				else:
					line.append(0)
			arr.append(line)
		return arr
		
'''
I wanted to try another way to compute it, this one turns the array into sets and builds a tree structure in a list.
Uses the following logic:
An array like:
1 1 0
1 0 1
1 0 1
can be broken down into 3 sets, depending on where the 1s in the rows of each column are located:
[0, 1, 2], [0], [1,2]

The tree yields:
            
						  ROOT
						/   |	\
					/		|		\
				/			|			\
			/				|				\
			
			0				1				2
			
			|				|				|
			
			0				0				0
		
		/		\		/		\		/		\
		
		1		2		1		2		1		2
		
We can prune off any branches of the tree where the value of the current node is equal to one of the previously visited nodes, which gives us 2 viable leaves, 102, and 201.
'''
class ManaToSetSolver(HelperMethods):
	def __init__(self, lands, cost):
		arr = self.buildCastsArray(lands,cost)
		self.sets = self.getSets(arr)
		self.sol = self.getResult(self.sets, len(cost))
	#breaks the array into the sets described in the above comment.	
	def getSets(self, arr):
		columns = []
		for col in range(len(arr[0])):
			columnSet = [] #The mana symbol index
			for row in range(len(arr)):
				if arr[row][col] == 1:
					columnSet.append(row) 
			columns.append(columnSet)
		return columns
	#returns true if the set can cast the mana.
	#false if otherwise.
	def getResult(self, sets, costTotal):
		solutions = [str(x) for x in sets[0]]
		for layer in sets[1:]:
			solCpy = solutions[:]
			for i in layer:
				for thing in solCpy:
					if str(i) not in str(thing):
						solutions.append(str(thing) + str(i))

		for thing in solutions:
			if len(str(thing)) == costTotal:
				return True
		return False
			
'''
currlands in nested lists of mana symbols:
[[1, 'W', 'B'], ['W', 'R'], [1], ['W']]
Mana cost is a single list of mana symbols:
[1, 1, W, W]
currently works for up to 10 mana.

Reduces the problem to a SAT instance and solves.
Solution is stored in self.sol.
SAT clauses are stored in self.SAT.
'''		
class ManaToSAT(HelperMethods):
	def __init__(self, lands, cost):
		arr = self.buildCastsArray(lands,cost)
		self.SAT = self.buildSATInstance(arr)	
		self.sol = pycosat.solve(self.SAT)
			
	def buildSATInstance(self, arr):
		clauses = []
		clauses += self.constraintA(arr)
		clauses += self.constraintB(arr)
		clauses += self.buildCustomConstraints(arr)
		return clauses
		
	#constraints that specify which lands can tap for which symbols.
	def buildCustomConstraints(self, arr):
		clauses = []
		for land in range(len(arr)):
			clause = []
			for mana in range(len(arr[0])):
				if arr[land][mana] == 1:
					clause += [int("1{}{}".format(land, mana))]
			if clause != []:
				clauses.append(clause)
		return clauses
		
	#each mana symbol must be accounted for
	#these clauses specify that for each mana symbol, there is at least one land that can tap for that symbol.
	#the format of these clauses is 1LM, where L is the index of the land, and M is the index of the mana symbol. 1 is simply there so the zeroes aren't truncated off when casting to ints, and 10 mana is plenty for my current uses of this system.
	def constraintA(self, arr):
		clauses = []
		for col in range(len(arr[0])): #for each mana symbol
			clause = []
			for land in range(len(arr)):
				clause += [int("1{}{}".format(land, col))]
			clauses.append(clause)
		return clauses
		
	#if a land is tapping for one type of mana, it cannot tap for another.
	#this yields the boolean expression if LxMw -> !(LxMy | LxMz ...)
	#which simplifies down to (!LxMw | !LxMy) & (!LxMw | !LxMz) ...
	#clauses are generated for each of those, ensuring no functionally duplicate clauses
	#!LxMy | !LxMz is logically equal to !LxMz | !LxMy, so we account for that and don't include the second
	def constraintB(self, arr):
		clauses = []
		for land in range(len(arr)):
			for mana in range(len(arr[0])):
				for i in range(mana+1, len(arr[0])):
					if i != mana:
						clause = [int("-1{}{}".format(land, mana)), int("-1{}{}".format(land, i))]
						clauses.append(clause)
		return clauses

#Determines whether a land taps for a given mana symbol
def tapsFor(land, mana):
	if mana in land:
		return True
	elif mana == '1':
		return True
		
#Given a sat solution, returns a dictionary of indexes corresponding to a land:mana pair.	
def deriveLands(lands, cost, sol):
	retDict = {}
	selectedClauses = []
	for item in sol:
		if item > 0:
			selectedClauses.append(item)
	
	for clause in selectedClauses:
		land = int(str(clause)[1])
		mana = int(str(clause)[2])
		retDict[land] = mana
		
	return retDict
	
#returns true if the lands can cast all of the symbols in the cost at the same time.	
def isCastable(lands, cost):
	mts = ManaToSAT(lands, cost)
	#for thing in mts.SAT:
		#print thing
	if mts.sol != "UNSAT":
		return True
	else:
		return False
		
if __name__ == "__main__":
	lands = [['B','R'], ['R'], ['B'], ['W'], ['W'], ['R']]
	cost = ['W','R','W', 'R', 'B']
	import time
	ssat = time.time()
	print isCastable(lands, cost)
	print "TIME FOR SAT SOLVER:"
	print time.time() - ssat
	sset = time.time()
	osol = ManaToSetSolver(lands, cost)
	print osol.sol
	print "TIME FOR SET SOLVER:"
	print time.time() - sset