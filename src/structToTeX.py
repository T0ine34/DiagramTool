
# take a dict like out.json and create class Diagram in TeX


from gamuLogger import Logger, debugFunc, LEVELS
import json

Logger.setLevel('stdout', LEVELS.DEBUG)

Logger.setModule("structToTeX")


def visibiliyToTeX(visibility : str):
    if visibility == "private":
        return "-"
    elif visibility == "protected":
        return "#"
    elif visibility == "public":
        return "+"
    else:
        return "?"


def Class(className : str, classDict : dict):
    
    attibutes = [
        "\\attribute{"
        + visibiliyToTeX(attribute['visibility'])
        + " "
        + name.split('.')[-1]
        + " : "
        + attribute['type']
        + "}"
        for name, attribute in classDict['attributes'].items()
    ]
    attibutes.extend(
        "\\attribute{"
        + visibiliyToTeX(property['visibility'])
        + " "
        + name.split('.')[-1]
        + " : "
        + property['type']
        + "}"
        for name, property in classDict['properties'].items()
    )
    methods = [
        "\\operation{"
        + visibiliyToTeX(method['visibility'])
        + " "
        + name.split('.')[-1]
        + "("
        + ", ".join(method['args'])
        + ") : "
        + method['return_type']
        + "}"
        for name, method in classDict['methods'].items()
    ]
    result =  """\\begin{tikzpicture}
\\begin{class}[text width=15cm]{""" + className + """}{0,0}
""" + "\n".join(attibutes) + """
""" + "\n".join(methods) + """
\\end{class}
\\end{tikzpicture}
"""

    return result.replace("_", r"\string_")


def Enum(enumName : str, enumDict : dict):
    methods = []
    values = ["\\attribute{"+name+"}" for name in enumDict['values']]
    for name, method in enumDict['methods'].items():
        if method['isStatic']:
            methods.append("\\operation{\\underline{"+visibiliyToTeX(method['visibility'])+" "+name.split('.')[-1]+"("+", ".join(method['args'])+") : "+method['return_type']+"}}")
        else:
            methods.append("\\operation{"+visibiliyToTeX(method['visibility'])+" "+name.split('.')[-1]+"("+", ".join(method['args'])+") : "+method['return_type']+"}")

    result =  """\\begin{tikzpicture}
\\begin{class}[text width=8cm]{""" + enumName + """}{0,0}
""" + "\n".join(values) + """
""" "\n".join(methods) + """
\\end{class}
\\end{tikzpicture}
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
                    "parents": []
                }



def createClassDiagram(data : dict):
    createMissingClasses(data)
    with open("testClass.tex", 'w') as f:
        for className, classData in data['classes'].items():
            f.write(Class(className, classData))
        
    


if __name__ == "__main__":
    with open("out.json", 'r') as f:
        data = json.load(f)

    # with open("testClass.tex", 'w') as f:
    #     for className, classData in data['classes'].items():
    #         f.write(Class(className, classData))
    createClassDiagram(data)
        
    with open("testEnum.tex", 'w') as f:
        for enumName, enumData in data['enums'].items():
            f.write(Enum(enumName, enumData))