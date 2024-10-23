import ast
from pathlib import Path
import os
from typing import Any, Union

from gamuLogger import Logger, LEVELS

Logger.setModule("PythonParser")

UNKNOWN = "unknown"

def dumpOnException(func):
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            Logger.error(f"An error occurred in function {func.__name__} : {e}")
            try:
                Logger.info(ast.dump(args[0], indent=4))
            except Exception as le:
                Logger.error(f"Could not dump the ast node : {le}")
            raise e
    return wrapper


def getTree(file) -> ast.Module:
    with open(file) as file:
        return ast.parse(file.read())
    


@dumpOnException
def getreturnString(node : ast.AST) -> str:
    if isinstance(node, ast.Attribute):
        return f"{getreturnString(node.value)}.{node.attr}"
    
    elif isinstance(node, ast.Constant):
        return str(node.value)
    elif isinstance(node, ast.Name):
        return node.id
    elif isinstance(node, ast.Subscript):
        return f"{getreturnString(node.value)}[{getreturnString(node.slice)}]"
        
    elif isinstance(node, ast.List):
        return f"[{', '.join(getreturnString(elt) for elt in node.elts)}]"
    elif isinstance(node, ast.Tuple):
        return f"({', '.join(getreturnString(elt) for elt in node.elts)})"
    else:
        return UNKNOWN
    
    
def getTypeComment(filepath : str, lineno : int) -> str:
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"File {filepath} not found")
    with open(filepath) as file:
        lines = file.readlines()
    if len(lines) <= lineno:
        raise IndexError(f"Line number {lineno} not found in file {filepath}")
    line = lines[lineno]
    return next(
        (
            line.split(t)[1].strip()
            for t in ["# type: ", "#type:"]
            if t in line
        ),
        UNKNOWN,
    )
    
def getTypeFromName(funcName : str) -> str:
    match funcName:
        case "__init__":
            return ""
        case "__str__":
            return "str"
        case "__repr__":
            return "str"
        case "__len__":
            return "int"
        case "__new__":
            return ""
        case "__del__":
            return ""
        case "__eq__":
            return "bool"
        case "__ne__":
            return "bool"
        case "__lt__":
            return "bool"
        case "__le__":
            return "bool"
        case "__gt__":
            return "bool"
        case "__ge__":
            return "bool"
        case _:
            return UNKNOWN

def getTypeFromConstant(node : ast.Constant) -> str:
    if isinstance(node.value, str):
        return "str"
    elif isinstance(node.value, int):
        return "int"
    elif isinstance(node.value, float):
        return "float"
    elif isinstance(node.value, bool):
        return "bool"
    else:
        return UNKNOWN
    

@dumpOnException
def parseFunctionArgs(node : ast.FunctionDef) -> list[dict[str, str]]:
    result = [] #type: list[dict[str, str]]
    for arg in node.args.args:
        argDict = {
            "name": arg.arg,
            "type": UNKNOWN
        }
        if arg.annotation:
            argDict["type"] = getreturnString(arg.annotation)
        result.append(argDict)
    return result


def PropertyType(node : ast.AST) -> str:
    if not isinstance(node, ast.FunctionDef):
        return ""
    for decorator in node.decorator_list:
        if isinstance(decorator, ast.Name) and decorator.id == "property":
            return "r"
        elif isinstance(decorator, ast.Attribute) and decorator.attr == "setter":
            return "w"
    return ""


def merge(d1 : dict, d2 : dict) -> dict:
    for key, value in d2.items():
        if key in d1 and isinstance(value, dict):
            d1[key] = merge(d1[key], value)
        elif key in d1 and isinstance(value, list):
            d1[key] = mergeList(d1[key], value)
        else:
            d1[key] = value
    return d1

def mergeList(l1 : list, l2 : list) -> list:
    for value in l2:
        if value not in l1:
            l1.append(value)
    return l1


PARSED_FILES = [] #type: list[str]



def getAllClasses(node : ast.AST, file : str, parseIncludedFiles : bool = False) -> list[str]:
    classes = []
    importedFiles = []
    
    if file in PARSED_FILES:
        raise ValueError(f"File {file} already parsed")
    PARSED_FILES.append(file)
    
    Logger.debug(f"Getting all classes in file '{file}'")    
    
    def parseNode(node : ast.AST, parents : str = "") -> None:
        if isinstance(node, ast.ImportFrom):
            parseImportFrom(node)
            return
        if isinstance(node, ast.ClassDef):
            classes.append(f"{parents}.{node.name}" if parents else node.name)
        
        if "body" in dir(node):
            for element in node.body: # type: ignore
                parseNode(element, f"{parents}.{node.name}" if isinstance(node, ast.ClassDef) else parents)

    def parseImportFrom(node : ast.ImportFrom) -> None:
        moduleName = node.module or ""
        backTimes = node.level
        if backTimes == 0:
            # the module is in the same directory, or it's a built-in module
            path = Path(file).parent / f"{moduleName}.py"
            if path.exists():
                importedFiles.append(str(path))
        else:
            # the module is in a parent directory
            path = Path(file).parent
            for _ in range(backTimes-1):
                path = path.parent

            moduleName = moduleName.replace('.', '/')
            if moduleName == "":
                moduleName = "."

            filepath = path / f"{moduleName}.py"
            if not filepath.exists():
                filepath = path / f"{moduleName}/__init__.py"
            if not filepath.exists():
                raise FileNotFoundError(
                    f"""files '{str(path / f"{moduleName}.py")}' and '{str(path / f"{moduleName}/__init__.py")}' not found"""
                )
            importedFiles.append(str(filepath))


    for element in node.body: # type: ignore
        parseNode(element)

    if parseIncludedFiles:
        for file in importedFiles:
            if file in PARSED_FILES:
                continue
            tree = getTree(file)
            parsed = getAllClasses(tree, file, True)
            classes += parsed

    return classes



def parseTree(node : ast.AST, file : str, classes : list[str], parseIncludedFiles : bool = False, dump : bool = False) -> dict[str, Any]:
    """return a dict like:
    ```python
    {
        "classes": {
            "ClassName": {
                "methods": {
                    "MethodName": {
                        "args": [
                            {"name": "arg1", "type": "str"},
                            {"name": "arg2", "type": "int"}
                            ],
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
                        "visibility": "public",
                        "mode": "r" # r, w, rw
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
                "args": [
                    {"name": "arg1", "type": "str"},
                    {"name": "arg2", "type": "int"}
                    ],
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
    # module name is each subdirectory of the file path, and the file name
    moduleName = ".".join(file.split("/")[:-1] + [file.split("/")[-1].split(".")[0]])
    
    Logger.debug(f"Parsing file '{file}'")
    if dump:
        dumpFilePath = f"dump/{moduleName}.ast"
        os.makedirs(os.path.dirname(dumpFilePath), exist_ok=True)
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
        return getTypeComment(file, lineno) if file else UNKNOWN

    @dumpOnException
    def getReturnType(node : ast.FunctionDef) -> str:
        result = getreturnString(node.returns) if node.returns else UNKNOWN
        if result == UNKNOWN:
            result = getType(node.lineno-1)
        if result == UNKNOWN:
            result = getTypeFromName(node.name)
        return result

    @dumpOnException
    def parseFunction(node : ast.FunctionDef, parentStack : list[str] = []) -> None:
        for element in node.body:
            if isinstance(element, ast.FunctionDef):
                parseFunction(element, parentStack + [str(node.name)])
            elif isinstance(element, ast.ClassDef):
                parseClassOrEnum(element, parentStack + [str(node.name)])
        result["functions"][".".join(parentStack + [str(node.name)])] = {
            "args": parseFunctionArgs(node),
            "return_type": getReturnType(node)
        }

    @dumpOnException
    def parseEnum(node : ast.ClassDef, parentStack : list[str] = []) -> None:
        values = []
        methods = {}
        properties = {}
        for element in node.body:
            if isinstance(element, ast.FunctionDef):
                # if the method has the decorator @property, then it's a property
                if "property" in [decorator.id for decorator in element.decorator_list]:  #type: ignore
                    properties[".".join(parentStack + [str(node.name), str(element.name)])] = {
                        "type": getreturnString(node.returns) if element.returns else getType(element.lineno-1), #type: ignore
                        "visibility": "private" if element.name.startswith("__") else "protected" if element.name.startswith("_") else "public"
                    }
                else:
                    #it's a method
                    methods[".".join(parentStack + [str(node.name), str(element.name)])] = {
                        "args": parseFunctionArgs(element),
                        "return_type": getReturnType(element),
                        "isStatic": "staticmethod" in [decorator.id for decorator in node.decorator_list], #type: ignore
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


    @dumpOnException
    def parseProperty(node : ast.FunctionDef, parentStack : list[str], properties : dict[str, dict[str, str]]) -> None:
        match PropertyType(node):
            case "":
                return
            case "r":
                # if the property is already in the properties dict, then modify it's mode to "rw" (It already has a getter)
                if ".".join(parentStack + [str(node.name)]) in properties:
                    properties[".".join(parentStack + [str(node.name)])]["mode"] = "rw"
                else:
                    properties[".".join(parentStack + [str(node.name)])] = {
                        "type": getreturnString(node.returns) if node.returns else getType(node.lineno-1),
                        "visibility": "private" if node.name.startswith("__") else "protected" if node.name.startswith("_") else "public",
                        "mode": "r"
                    }
            case "w":
                # if the property is already in the properties dict, then modify it's mode to "rw" (It already has a setter)
                if ".".join(parentStack + [str(node.name)]) in properties:
                    properties[".".join(parentStack + [str(node.name)])]["mode"] = "rw"
                else:
                    properties[".".join(parentStack + [str(node.name)])] = {
                        "type": getreturnString(node.returns) if node.returns else getType(node.lineno-1),
                        "visibility": "private" if node.name.startswith("__") else "protected" if node.name.startswith("_") else "public",
                        "mode": "w"
                    }
            case _:
                return
            
            
    @dumpOnException
    def containType(node : ast.AST, _type : str) -> bool:
        Logger.debug(f"Checking if {ast.dump(node)} contains type {_type}")
        if isinstance(node, ast.Name):
            return node.id == _type
        elif isinstance(node, ast.Attribute):
            return containType(node.value, _type)
        elif isinstance(node, ast.Subscript):
            return containType(node.value, _type)
        elif isinstance(node, ast.Call):
            return any(containType(arg, _type) for arg in node.args)
        elif isinstance(node, ast.List):
            return any(containType(elt, _type) for elt in node.elts)
        elif isinstance(node, ast.Tuple):
            return any(containType(elt, _type) for elt in node.elts)
        elif isinstance(node, ast.Constant):
            return node.value == _type
        else:
            Logger.warning(f"Unknown type {ast.dump(node)}")
            return False

    @dumpOnException
    def parseClass(node : ast.ClassDef, parentStack : list[str] = []) -> None:
        Logger.debug(f"Parsing class {node.name}")
        methods = {}
        attributes = {}
        properties = {}
        aggregate = set() # for nested classes that are not created and destroyed with the parent class, but are used in the parent class
                       # such objects are passed to the parent class in the constructor or in a method
        composite = set() # for nested classes that are created and destroyed with the parent class
        for element in node.body:
            if isinstance(element, ast.FunctionDef):
                # if the method has the decorator @property, then it's a property
                if PropertyType(element):
                    parseProperty(element, parentStack + [str(node.name)], properties)
                else:
                    #it's a method
                    methods[".".join(parentStack + [str(node.name), str(element.name)])] = {
                        "args": parseFunctionArgs(element),
                        "return_type": "" if element.name == "__init__" else getReturnType(element),
                        "isStatic": "staticmethod" in [decorator.id for decorator in element.decorator_list], #type: ignore
                        "visibility": "private" if element.name.startswith("__") else "protected" if element.name.startswith("_") else "public"
                    }
                    # parse arguments types to find aggregate classes
                    # there are three cases:
                    # 1. the argument is a class that is defined inside the current class (it's name is relative to the current class) ex: TYPE
                    # 2. the argument is a class that is defined elsewhere (it's name is absolute) ex : relation.TYPE
                    # 3. the argument is a built-in type or is defined in a external module : in this case, ignore it
                    for arg in element.args.args:
                        if arg.arg == "self":
                            continue
                        if "annotation" in dir(arg) and arg.annotation and any(containType(arg.annotation, _type) for _type in classes):
                            argType = getreturnString(arg.annotation)
                            Logger.debug(f"Aggregate class {argType} found in method {element.name} of class {node.name}")
                            
                            aggregate.add(argType)
                                
                            
                    
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
            "inheritFrom": [getreturnString(base) for base in node.bases], #type: ignore
            "properties": properties,
            "aggregate": list(aggregate),
            "composite": list(composite)
        }

    def parseClassOrEnum(node : ast.ClassDef, parentStack : list[str] = []) -> None:
        #if the class inherits from Enum, then it's an enum
        for base in node.bases:
            if isinstance(base, ast.Name) and base.id == "Enum":
                parseEnum(node, parentStack)
                return
        parseClass(node, parentStack)

    @dumpOnException
    def parseGlobalVariables(node : ast.Assign) -> None:
        for target in node.targets:
            if isinstance(target, ast.Name):
                _type = UNKNOWN
                if isinstance(node.value, ast.Constant):
                    _type = getTypeFromConstant(node.value)
                if _type == UNKNOWN:
                    _type = getType(target.lineno-1)
                result["globalVariables"][target.id] = _type

    @dumpOnException
    def parseImport(node : ast.ImportFrom) -> None:
        moduleName = node.module or ""
        backTimes = node.level
        if backTimes == 0:
            # the module is in the same directory, or it's a built-in module
            path = Path(file).parent / f"{moduleName}.py"
            if path.exists():
                importedFiles.append(str(path))
        else:
            # the module is in a parent directory
            path = Path(file).parent
            for _ in range(backTimes-1):
                path = path.parent

            moduleName = moduleName.replace('.', '/')
            if moduleName == "":
                moduleName = "."

            filepath = path / f"{moduleName}.py"
            if not filepath.exists():
                filepath = path / f"{moduleName}/__init__.py"
            if not filepath.exists():
                raise FileNotFoundError(
                    f"""files '{str(path / f"{moduleName}.py")}' and '{str(path / f"{moduleName}/__init__.py")}' not found"""
                )
            importedFiles.append(str(filepath))

    for element in node.body: # type: ignore
        # if isinstance(element, ast.ImportFrom):
        #     parseImport(element)
        if isinstance(element, ast.FunctionDef):
            parseFunction(element)
        elif isinstance(element, ast.ClassDef):
            parseClassOrEnum(element)
        elif isinstance(element, ast.Assign):
            parseGlobalVariables(element)

    # search in all nodes for ImportFrom nodes
    for node in ast.walk(node):
        if isinstance(node, ast.ImportFrom):
            parseImport(node)

    if parseIncludedFiles:
        for file in importedFiles:
            if file in PARSED_FILES:
                continue
            tree = getTree(file)
            parsed = parseTree(tree, file, classes, True, dump)
            result = merge(result, parsed)

    return result 
    
        
def parse(filename : str, parseIncludedFiles : bool = False, dump : bool = False) -> dict[str, str]:
    tree = getTree(filename)
    classes = getAllClasses(tree, filename, parseIncludedFiles)
    PARSED_FILES.clear() # clear the list of parsed files
    return parseTree(tree, filename, classes, parseIncludedFiles, dump)


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
    
    Logger.info("Done")