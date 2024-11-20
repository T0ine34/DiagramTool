import argparse
import time
import traceback

from gamuLogger import Logger, LEVELS
Logger.setModule("DiagramTool.")

from .main import fromSource


class Chronometer:
    def __init__(self):
        self.__delta = 0.0
        
    def __enter__(self):
        self.__start = time.time()
        return self
    
    def __exit__(self, exc_type, exc_value, traceback) -> None:
        self.__delta = time.time() - self.__start
        
    def get(self) -> float:
        return self.__delta

def buildArgParser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description='create a class diagram from source code')
    parser.add_argument('source', type=str, help='source code main file')
    parser.add_argument('output', type=str, help='output file')
    parser.add_argument('--debug', action='store_true', help='print debug information', default=False)
    parser.add_argument('--dump', action='store_true', help='dump parsed data to stdout', default=False)
    parser.add_argument('--save-ast', action='store_true', help='save ast to file', default=False)
    parser.add_argument('--show-border', action='store_true', help='show border around the image', default=False)
    return parser


def getArgs() -> argparse.Namespace:
    parser = buildArgParser()
    return parser.parse_args()

def main():
    args = getArgs()
    if args.debug:
        Logger.setLevel('stdout', LEVELS.DEBUG)
    
    chrono = Chronometer()
    try:
        with chrono:
            fromSource(args.source, args.output, args.save_ast, args.dump, args.show_border)
    except Exception as e:
        Logger.critical(f"An error occured: {e}\n{traceback.format_exc()}")
        exit(1)
    else:
        Logger.info(f"Diagram created in {round(chrono.get(), 2)}s")
    
if __name__ == "__main__":
    main()