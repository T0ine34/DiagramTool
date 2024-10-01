import ast
from pathlib import Path
import os

from gamuLogger import Logger, LEVELS

Logger.setModule("PythonParser")


def getTree(file) -> ast.Module:
    with open(file) as file:
        return ast.parse(file.read())
    

def getreturnStringAttr(node : ast.Attribute) -> str:
    if isinstance(node.value, ast.Attribute):
        return getreturnStringAttr(node.value) + "." + node.attr
    return node.value.id + "." + node.attr

def getReturnStringConst(node : ast.Constant) -> str:
    return str(node.value)


def getreturnString(node : ast.AST) -> str:
    if isinstance(node, ast.Attribute):
        return getreturnStringAttr(node)
    elif isinstance(node, ast.Constant):
        return getReturnStringConst(node)
    elif isinstance(node, ast.Name):
        return node.id
    
    
def getTypeComment(filepath : str, lineno : int) -> str:
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"File {filepath} not found")
    with open(filepath) as file:
        lines = file.readlines()
    if len(lines) > lineno:
        line = lines[lineno]
        for t in ["# type: ", "#type:"]:
            if t in line:
                return line.split(t)[1].strip()
    else:
        raise IndexError(f"Line number {lineno} not found in file {filepath}")
    return "Unknown"


def merge(d1 : dict, d2 : dict) -> dict:
    for key, value in d2.items():
        if key in d1:
            if isinstance(value, dict):
                d1[key] = merge(d1[key], value)
            elif isinstance(value, list):
                d1[key] = mergeList(d1[key], value)
            else:
                d1[key] = value
        else:
            d1[key] = value
    return d1

def mergeList(l1 : list, l2 : list) -> list:
    for value in l2:
        if value not in l1:
            l1.append(value)
    return l1


PARSED_FILES = []
def parseTree(node : ast.AST, file : str, parseIncludedFiles : bool = False, dump : bool = False) -> dict[str, str]:
    """return a dict like:
    ```python
    {
        "classes": {
            "ClassName": {
                "methods": {
                    "MethodName": {
                        "args": ["arg1", "arg2"],
                        "return_type": "str",
                        "isStatic": False,
                        "visibility": "public" # public, private, protected
                    }
                },
                "attributes": {
                    "AttributeName": {
                        "type": "str"
                        "visibility": "public"
                    }
                },
                "properties": {
                    "PropertyName": {
                        "type": "str",
                        "visibility": "public"
                    }
                },
                "inheritFrom": ["ParentClass"],
            }
            "ClassName2": {
                ...
            }
            "ClassName2.ClassName3": { # nested class
                ...
            }
        },
        "enums": {
            "EnumName": {
                "values": ["value1", "value2"],
                "methods": {
                    ... # same as class methods
                }
            }
        },
        "functions": {
            "FunctionName": {
                "args": ["arg1", "arg2"],
                "return_type": "str"
            },
            "FunctionName.FunctionName2": { # nested function
                ...
            }
        },
        "globalVariables": {
            "VariableName": "str"
        }
    }
    ```
    
    will recursively parse the given ast node and return a dict with the structure above
    """
    
    if dump:
        dumpFilePath = f"{os.path.basename(file)}.dump"
        with open(dumpFilePath, "w") as f:
            f.write(ast.dump(node, indent=4))
            Logger.info(f"Dumped file '{file}' to '{dumpFilePath}'")
    
    if file in PARSED_FILES:
        raise ValueError(f"File {file} already parsed")
    PARSED_FILES.append(file)
    
    Logger.info(f"Parsing file '{file}'")
    
    result = {
        "classes": {},
        "enums": {},
        "functions": {},
        "globalVariables": {}
    }
    
    importedFiles = []
    
    def getType(lineno : int) -> str:
        if file:
            return getTypeComment(file, lineno)
        return "Unknown"
    
    def parseFunction(node : ast.FunctionDef, parentStack : list[str] = []) -> None:
        for element in node.body:
            if isinstance(element, ast.FunctionDef):
                parseFunction(element, parentStack + [str(node.name)])
            elif isinstance(element, ast.ClassDef):
                parseClassOrEnum(element, parentStack + [str(node.name)])
        result["functions"][".".join(parentStack + [str(node.name)])] = {
            "args": [arg.arg for arg in node.args.args],
            "return_type": getreturnString(node.returns) if node.returns else getType(node.lineno-1),
        }
        
    def parseEnum(node : ast.ClassDef, parentStack : list[str] = []) -> None:
        values = []
        methods = {}
        properties = {}
        for element in node.body:
            if isinstance(element, ast.FunctionDef):
                # if the method has the decorator @property, then it's a property
                if "property" in [decorator.id for decorator in element.decorator_list]:
                    properties[".".join(parentStack + [str(node.name), str(element.name)])] = {
                        "type": getreturnString(node.returns) if element.returns else getType(element.lineno-1),
                        "visibility": "private" if element.name.startswith("__") else "protected" if element.name.startswith("_") else "public"
                    }
                else:
                    #it's a method
                    methods[".".join(parentStack + [str(node.name), str(element.name)])] = {
                        "args": [arg.arg for arg in element.args.args],
                        "return_type": getreturnString(node.returns) if element.returns else getType(element.lineno-1),
                        "isStatic": "staticmethod" in [decorator.id for decorator in node.decorator_list],
                        "visibility": "private" if element.name.startswith("__") else "protected" if element.name.startswith("_") else "public"
                    }
            elif isinstance(element, ast.Assign):
                for target in element.targets:
                    if isinstance(target, ast.Name):
                        values.append(target.id)
            elif isinstance(element, ast.ClassDef):
                parseEnum(element, parentStack + [str(node.name)])
        result["enums"][".".join(parentStack + [str(node.name)])] = {
            "values": values,
            "methods": methods,
            "properties": properties
        }
        
    def parseClass(node : ast.ClassDef, parentStack : list[str] = []) -> None:
        methods = {}
        attributes = {}
        properties = {}
        for element in node.body:
            if isinstance(element, ast.FunctionDef):
                # if the method has the decorator @property, then it's a property
                if "property" in [decorator.id for decorator in element.decorator_list]:
                    properties[".".join(parentStack + [str(node.name), str(element.name)])] = {
                        "type": getreturnString(node.returns) if element.returns else getType(element.lineno-1),
                        "visibility": "private" if element.name.startswith("__") else "protected" if element.name.startswith("_") else "public"
                    }
                else:
                    #it's a method
                    methods[".".join(parentStack + [str(node.name), str(element.name)])] = {
                        "args": [arg.arg for arg in element.args.args],
                        "return_type": getreturnString(element.returns) if element.returns else getType(element.lineno-1),
                        "isStatic": "staticmethod" in [decorator.id for decorator in element.decorator_list],
                        "visibility": "private" if element.name.startswith("__") else "protected" if element.name.startswith("_") else "public"
                    }
            elif isinstance(element, ast.ClassDef):
                parseClassOrEnum(element, parentStack + [str(node.name)])
            elif isinstance(element, ast.Assign):
                for target in element.targets:
                    if isinstance(target, ast.Name):
                        attributes[target.id] = {
                            "type": getType(target.lineno-1),
                            "visibility": "private" if target.id.startswith("__") else "protected" if target.id.startswith("_") else "public"
                        }
        result["classes"][".".join(parentStack + [str(node.name)])] = {
            "methods": methods,
            "attributes": attributes,
            "inheritFrom": [base.id for base in node.bases],
            "properties": properties
        }
        
    def parseClassOrEnum(node : ast.ClassDef, parentStack : list[str] = []) -> None:
        #if the class inherits from Enum, then it's an enum
        for base in node.bases:
            if isinstance(base, ast.Name) and base.id == "Enum":
                parseEnum(node, parentStack)
                return
        parseClass(node, parentStack)
        
    def parseGlobalVariables(node : ast.Assign) -> None:
        for target in node.targets:
            if isinstance(target, ast.Name):
                result["globalVariables"][target.id] = getType(target.lineno-1)
                
    def parseImport(node : ast.ImportFrom) -> None:
        moduleName = node.module
        backTimes = node.level
        if backTimes == 0:
            # the module is in the same directory, or it's a built-in module
            path = Path(file).parent / f"{moduleName}.py"
            Logger.debug("optional : " + str(path))
            if path.exists():
                importedFiles.append(str(path))
        else:
            # the module is in a parent directory
            path = Path(file).parent
            for _ in range(backTimes-1):
                path = path.parent
            path = path / f"{moduleName.replace('.', '/')}.py"
            Logger.debug("required : " + str(path))
            if not path.exists():
                raise FileNotFoundError(f"File {path} not found")
            importedFiles.append(str(path))
                
    for element in node.body:
        if isinstance(element, ast.ImportFrom):
            parseImport(element)
        elif isinstance(element, ast.FunctionDef):
            parseFunction(element)
        elif isinstance(element, ast.ClassDef):
            parseClassOrEnum(element)
        elif isinstance(element, ast.Assign):
            parseGlobalVariables(element)
            
            
    if parseIncludedFiles:
        for file in importedFiles:
            if file in PARSED_FILES:
                continue
            tree = getTree(file)
            parsed = parseTree(tree, file, True, dump)
            result = merge(result, parsed)
            
    return result
    
        
def parse(filename : str, parseIncludedFiles : bool = False, dump : bool = False) -> dict[str, str]:
    tree = getTree(filename)
    return parseTree(tree, filename, parseIncludedFiles, dump)


if __name__ == "__main__":
    import json
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("file", type=str)
    parser.add_argument("--dump", action="store_true")
    parser.add_argument("--debug", action="store_true")
    args = parser.parse_args()
    
    if args.debug:
        Logger.setLevel('stdout', LEVELS.DEBUG)
    
    parsed = parse(args.file, True, args.dump)
    
    with open("out.json", "w") as file:
        file.write(json.dumps(parsed, indent=4))
    
