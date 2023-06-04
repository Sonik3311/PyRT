import re

import toml

from coloredText import bcolors as colors


class TOMLParser():
    tomlFiles = {}

    def loadConfig( self, pathToFile:str, name="None" ):
        if name == "None":
            filename = re.split( pattern=r"[/\|/.//]", string=pathToFile )[-2]
        try:
            with open( pathToFile, "r" ) as f:
                self.tomlFiles[filename] = toml.load(f)
        except FileNotFoundError:
            print( f"{colors.HEADER}TOMLParser - {colors.FAIL}FileNotFoundError:{colors.ENDC} file {colors.OKBLUE}[{pathToFile}]{colors.ENDC} doesn't exist!")
            exit()
    def getValue( self, filename:str, name:list ):
        folders = name.split("/")
        value = self.tomlFiles[filename]
        for folder in folders:
            try:
                value = value[folder]
            except KeyError:
                print( f"{colors.HEADER}TOMLParser - {colors.WARNING}KeyError:{colors.ENDC} path {colors.OKBLUE}[{filename}]{colors.OKCYAN}[{name}]{colors.ENDC} doesn't exist!")
                return None
        return value