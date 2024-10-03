
# take a dict like out.json and create class Diagram in TeX

try:
    from .customTypes import Class, visibiliyToTeX
except ImportError:
    from customTypes import Class, visibiliyToTeX


from gamuLogger import Logger, debugFunc, LEVELS
import json

Logger.setLevel('stdout', LEVELS.DEBUG)

Logger.setModule("structToTeX")



# def Class(className : str, classDict : dict) -> str:
    
#     attibutes = [
#         "\\attribute{"
#         + visibiliyToTeX(attribute['visibility'])
#         + " "
#         + name.split('.')[-1]
#         + " : "
#         + attribute['type']
#         + "}"
#         for name, attribute in classDict['attributes'].items()
#     ]
#     attibutes.extend(
#         "\\attribute{"
#         + visibiliyToTeX(property['visibility'])
#         + " "
#         + name.split('.')[-1]
#         + " : "
#         + property['type']
#         + "}"
#         for name, property in classDict['properties'].items()
#     )
#     methods = [
#         "\\operation{"
#         + visibiliyToTeX(method['visibility'])
#         + " "
#         + name.split('.')[-1]
#         + "("
#         + ", ".join(method['args'])
#         + ") : "
#         + method['return_type']
#         + "}"
#         for name, method in classDict['methods'].items()
#     ]
    
#     inheritance = [
#         "\\inherit{" + parent + "}"
#         for parent in classDict['inheritFrom']
#     ]
    
#     width = max(len(className), max([0]+[len(attibute) for attibute in attibutes]), max([0]+[len(method) for method in methods]))
    
#     result =  """\\begin{class}[text width=""" + str(width/2) + """em]{""" + className + """}{&X,&Y}
# """ + "\n".join(inheritance) + """
# """ + "\n".join(attibutes) + """
# """ + "\n".join(methods) + """
# \\end{class}
# """

#     return result.replace("_", r"\string_")


def Enum(enumName : str, enumDict : dict) -> str:
    methods = []
    values = ["\\attribute{"+name+"}" for name in enumDict['values']]
    for name, method in enumDict['methods'].items():
        if method['isStatic']:
            methods.append("\\operation{\\underline{"+visibiliyToTeX(method['visibility'])+" "+name.split('.')[-1]+"("+", ".join(method['args'])+") : "+method['return_type']+"}}")
        else:
            methods.append("\\operation{"+visibiliyToTeX(method['visibility'])+" "+name.split('.')[-1]+"("+", ".join(method['args'])+") : "+method['return_type']+"}")

    result =  """\\begin{class}[text width=8cm]{""" + enumName + """}{&X,&Y}
""" + "\n".join(values) + """
""" "\n".join(methods) + """
\\end{class}
"""

    return result.replace("_", r"\string_")


def createMissingClasses(data : dict) -> None:
    # add missing classes to data (class referenced as inheritance parent, but not defined)
    classNames = list(data['classes'].keys())
    for className in classNames:
        classData = data['classes'][className]
        for parent in classData['inheritFrom']:
            if parent not in data['classes']:
                data['classes'][parent] = {
                    "attributes": {},
                    "properties": {},
                    "methods": {},
                    "inheritFrom": []
                }

def sortClasses(data : dict) -> dict:
    # sort classes by inheritance
    sortedClasses = {}
    for className, classData in data['classes'].items():
        if classData['inheritFrom'] == []:
            sortedClasses[className] = classData
    for className, classData in data['classes'].items():
        if className not in sortedClasses:
            sortedClasses[className] = classData
    return sortedClasses

def calcInheritanceLevels(data : dict) -> dict:
    # calculate inheritance levels
    inheritanceLevels = {}
    for className, classData in data['classes'].items():
        inheritanceLevels[className] = 0
    for className, classData in data['classes'].items():
        for parent in classData['inheritFrom']:
            inheritanceLevels[className] = max(inheritanceLevels[className], inheritanceLevels[parent]+1)
    return inheritanceLevels

def createClassDiagram(data : dict):
    createMissingClasses(data)
    classes = sortClasses(data)
    # inheritanceLevels = calcInheritanceLevels(data)
    classes = [Class.fromDict(className, classData) for className, classData in classes.items()]
    Class.placeAll()

    with open("resources/dynamic/classes.tex", 'w') as f:
        f.write("\\begin{tikzpicture}\n")
        for class_ in classes:
            f.write(class_.compute())
        f.write("\\end{tikzpicture}")
        
    


if __name__ == "__main__":
    with open("out.json", 'r') as f:
        data = json.load(f)

    # with open("testClass.tex", 'w') as f:
    #     for className, classData in data['classes'].items():
    #         f.write(Class(className, classData))
    createClassDiagram(data)
        
    with open("resources/dynamic/enums.tex", 'w') as f:
        for enumName, enumData in data['enums'].items():
            f.write(Enum(enumName, enumData))