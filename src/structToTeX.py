
# take a dict like out.json and create class Diagram in TeX


from gamuLogger import Logger, debugFunc, LEVELS
import json

Logger.setLevel('stdout', LEVELS.DEBUG)

@debugFunc()
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
    
    attibutes = []
    methods = []
    for name, attribute in classDict['attributes'].items():
        attibutes.append("\\attribute{"+visibiliyToTeX(attribute['visibility'])+" "+name.split('.')[-1]+" : "+attribute['type']+"}")
    for name, property in classDict['properties'].items():
        attibutes.append("\\attribute{"+visibiliyToTeX(property['visibility'])+" "+name.split('.')[-1]+" : "+property['type']+"}")
    for name, method in classDict['methods'].items():
        methods.append("\\operation{"+visibiliyToTeX(method['visibility'])+" "+name.split('.')[-1]+"("+", ".join(method['args'])+") : "+method['return_type']+"}")
    
    result =  """\\begin{tikzpicture}
\\begin{class}[text width=17cm]{""" + className + """}{0,0}
""" + "\n".join(attibutes) + """
""" + "\n".join(methods) + """
\\end{class}
\\end{tikzpicture}
"""

    return result.replace("_", "\string_")


def Enum(enumName : str, enumDict : dict):
    values = []
    methods = []
    for name in enumDict['values']:
        values.append("\\attribute{"+name+"}")
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

    return result.replace("_", "\string_")


if __name__ == "__main__":
    with open("out.json", 'r') as f:
        data = json.load(f)

    with open("testClass.tex", 'w') as f:
        for className, classData in data['classes'].items():
            f.write(Class(className, classData))
        
    with open("testEnum.tex", 'w') as f:
        for enumName, enumData in data['enums'].items():
            f.write(Enum(enumName, enumData))