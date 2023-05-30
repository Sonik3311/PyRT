import re

from coloredText import bcolors as colors


class PYRTParser:
    rowIDX = 0
    colIDX = 0

    converted = {}

    keywords = {
        "COMMENT" : "#",
        "OBJECTS" : {
            "SPHERE" : "sphere",
            "CUBE" : "cube",
            "CYLINDER" : "cylinder",
            "QUAD" : "quad",
        }
    }

    objectProperties = {
        "SPHERE" :   [4, [4, 3,3,4]],
        "CUBE" :     [5, [3,3, 3,3,4]],
        "CYLINDER" : [5, [3,4, 3,3,4]],
        "QUAD" :     [7, [3,3,3,3, 3,3,4]],
    }

    def tokenize(self, file):
        lines = ""
        try:
            with open(file, "r") as f:
                lines = f.readlines()
        except FileNotFoundError:
            print( f"{colors.HEADER}PYRTParser - {colors.WARNING}FileNotFoundError:{colors.ENDC} file {colors.OKBLUE}[{file}]{colors.ENDC} doesn't exist!")
        
        tokens = []

        for line in lines:
            #print(line)
            self.rowIDX += 1
            commentMatch = line.find(self.keywords["COMMENT"])
            if commentMatch != -1 :
                line = line[0:commentMatch]
            
            if line.strip() == "": #empty line
                continue
            matchedObject = None
            for obj in self.keywords["OBJECTS"]:
                searchResult = re.findall(self.keywords["OBJECTS"][obj], line.lower())
                matchedObject = obj
                if len(searchResult) == 0 or len(searchResult) > 1: # no matches for object keywords or too much keywords on one line
                    continue
                    #raise Exception("PYRTParser.py", f"Invalid Syntax at line {self.rowIDX}")
                
                vectors = [] # get all vectors
                for match in re.finditer(r"\([ \t]*-?(\d,|\d)[^)]*\)", line):
                    #print(match.group())
                    span = match.span()
                    vectors.append(eval(line[span[0]:span[1]])) #convert to tuple
                #print(vectors)
                if len(vectors) != self.objectProperties[matchedObject][0]: # not enough or more vectors than needed
                    raise Exception("PYRTParser.py", f"Invalid syntax at line {self.rowIDX}: expected {self.objectProperties[matchedObject][0]} arguments, but got {len(vectors)}")

                # parse vectors
                for index, vector in enumerate(vectors):
                    #print(vector)
                    if len(vector) != self.objectProperties[matchedObject][1][index]:
                        raise Exception("PYRTParser.py", f"Invalid syntax at line {self.rowIDX}: vector at index {index} expected {self.objectProperties[matchedObject][1][index]} arguments, but got {len(vector)}")
                
                # At this stage we have valid geometry type and it's property vectors,
                # that means we can pack everything up into tokens.
                tokens.append([matchedObject.lower(), vectors])


                

            
        return tokens