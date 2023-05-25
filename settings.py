import toml
import re
from termcolor import colored

class TOMLParser():
    tomlFiles = {}

    def loadConfig( self, pathToFile:str, name="None" ):
        if name == "None":
            filename = re.split( pattern=r"[/\|/.//]", string=pathToFile )[-2]
        with open( pathToFile, "r" ) as f:
            self.tomlFiles[filename] = toml.load(f)

    def getValue( self, filename:str, name:list ):
        folders = name.split("/")
        value = self.tomlFiles[filename]
        for folder in folders:
            try:
                value = value[folder]
            except KeyError:
                print( f"TOMLParser KeyError: path [{name}] doesn't exist!")
                return None
        #print('\x1b[6;30;42m' + 'Success!' + '\x1b[0m')
        return value