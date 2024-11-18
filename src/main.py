import sys
from enum import Enum
from typing import Callable

from .python import parse as parse_python
from .svg import createDiagram

from gamuLogger import Logger

Logger.setModule("DiagramTool.main")


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



def fromSource(source : str, output : str, save_ast : bool = False, dump : bool = False, showBorder : bool = False):
    """entry point for the module"""
    
    language = getFileLanguage(source)
    Logger.debug(f"detected language: {language}")
    parser = getParser(language)
    
    data = parser(source, True, dump)
    
    if save_ast:
        with open("ast.json", 'w') as f:
            import json
            json.dump(data, f, indent=4)
        Logger.info("saved ast to ast.json")
    
    Logger.debug(f"parsed data: {data.keys()}")

    svg = createDiagram(data)
    svg.save(output, showBorder=showBorder)
    
    Logger.info(f"saved diagram to {output}")
        