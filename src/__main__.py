import argparse
import sys
from enum import Enum
from typing import Callable

from . import parse_python
from . import SVG, createDiagram

from gamuLogger import Logger, LEVELS

def buildArgParser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description='create a class diagram from source code')
    parser.add_argument('source', type=str, help='source code main file')
    parser.add_argument('output', type=str, help='output file')
    parser.add_argument('--debug', action='store_true', help='print debug information', default=False)
    parser.add_argument('--dump', action='store_true', help='dump parsed data to stdout', default=False)
    parser.add_argument('--save-ast', action='store_true', help='save ast to file', default=False)
    return parser


def getArgs() -> argparse.Namespace:
    parser = buildArgParser()
    args = parser.parse_args()
    return args


class LANGUAGES(Enum):
    PYTHON = 0
    JAVASCRIPT = 1
    TYPESCRIPT = 2
    
    def __str__(self):
        return self.name.lower()


def getFileLanguage(filename : str) -> LANGUAGES:
    if filename.endswith('.py'):
        return LANGUAGES.PYTHON
    elif filename.endswith('.js'):
        return LANGUAGES.JAVASCRIPT
    elif filename.endswith('.ts'):
        return LANGUAGES.TYPESCRIPT
    else:
        Logger.error(f"unknown file extension for {filename}")
        sys.exit(1)
        

def getParser(language : LANGUAGES) -> Callable[[str, bool, bool], dict[str, str]]:
    match language:
        case LANGUAGES.PYTHON:
            return parse_python
        case LANGUAGES.JAVASCRIPT:
            Logger.error(f"no parser for {language}")
            raise NotImplementedError
        case LANGUAGES.TYPESCRIPT:
            Logger.error(f"no parser for {language}")
            raise NotImplementedError
        case _:
            Logger.error(f"no parser for {language}")
            raise ValueError



def main():
    args = getArgs()
    
    if args.debug:
        Logger.setLevel('stdout', LEVELS.DEBUG)
        
    Logger.setModule("main")
    
    language = getFileLanguage(args.source)
    parser = getParser(language)
    
    data = parser(args.source, True, args.dump)
    
    if args.save_ast:
        with open("ast.json", 'w') as f:
            import json
            json.dump(data, f, indent=4)
        Logger.info("saved ast to ast.json")
    
    Logger.debug(f"parsed data: {data.keys()}")

    svg = createDiagram(data)
    if args.debug:
        svg.save(args.output, showBorder=True)
    else:
        svg.save(args.output)
    
    Logger.info(f"saved diagram to {args.output}")
        
        
        
if __name__ == "__main__":
    main()