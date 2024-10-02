
# take a dict like out.json and create class Diagram in TeX


from gamuLogger import Logger, debugFunc, LEVELS
import json

Logger.setLevel('stdout', LEVELS.DEBUG)

Logger.setModule("structToTeX")


class CoordGen:
    def __init__(self) -> None:
        self.x = 15
        self.y = 30
        
    def __iter__(self):
        return self
    
    def __next__(self):
        x = self.x
        y = self.y
        self.y -= 5
        if self.y < -30:
            raise StopIteration
        if self.x < -15:
            self.x = 15
            self.y = 30
        return "{},{}".format(x, y)
    
    def skipX(self):
        self.x -= 5
        if self.x < -15:
            self.x = 15
            self.y -= 5
        
    def skipY(self):
        self.y -= 5
        if self.y < -30:
            self.y = 30
            self.x -= 5
            if self.x < -15:
                self.x = 15
                self.y = 30

def Coords(): #usage: next(Coords())
    for x in range(20, -20, -10):
        for y in range(40, -40, -10):
            yield "{},{}".format(x, y)
            
coords = Coords()


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
    
    inheritance = [
        "\\inherit{" + parent + "}"
        for parent in classDict['inheritFrom']
    ]
    
    width = max(len(className), max([0]+[len(attibute) for attibute in attibutes]), max([0]+[len(method) for method in methods]))
    
    result =  """\\begin{class}[text width=""" + str(width/2) + """em]{""" + className + """}{""" + str(next(coords)) + """}
""" + "\n".join(inheritance) + """
""" + "\n".join(attibutes) + """
""" + "\n".join(methods) + """
\\end{class}
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

    result =  """\\begin{class}[text width=8cm]{""" + enumName + """}{""" + str(next(coords)) + """}
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

def createClassDiagram(data : dict):
    createMissingClasses(data)
    data['classes'] = sortClasses(data)
    with open("resources/dynamic/classes.tex", 'w') as f:
        f.write("\\begin{tikzpicture}\n")
        for className, classData in data['classes'].items():
            f.write(Class(className, classData))
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