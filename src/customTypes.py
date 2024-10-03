try:
    from .utils import visibiliyToTeX, groupBy
except ImportError:
    from utils import visibiliyToTeX, groupBy
    
    
from enum import Enum

class Mode(Enum):
    CREATING = 0
    PLACING = 1
    WRITING = 2


class Class:
    __instances = [] #type: list[Class]
    __mode = Mode.CREATING
    def __init__(self, name : str, attributes : dict[str, dict], methods : dict[str, dict], inheritFrom : list[str], properties : dict[str, dict]):
        if Class.__mode != Mode.CREATING:
            raise Exception("Cannot create a new class when not in creating mode")
        
        self.name = name
        self.attributes = attributes
        self.methods = methods
        self.inheritFrom = inheritFrom
        self.properties = properties
        
        self.x = 0 #in em
        self.y = 0 #in ex
        
        self.width =max(len(name), max([0]+[len(attribute) for attribute in attributes]), max([0]+[len(method) for method in methods]))
        self.height = (len(attributes)*1.6 + len(methods)*1.6 + 2 + 3)*2 # 1 for the class name, 2 for borders
        
        self.inheritanceLevel = 0
        self.isOrphan = True # True if the class is not connected to any other class
        
        
        Class.__instances.append(self)
        
    @staticmethod
    def fromDict(name : str, classDict : dict):
        return Class(name, classDict['attributes'], classDict['methods'], classDict['inheritFrom'], classDict['properties'])
    
    
    def calcInheritanceLevel(self):
        if Class.__mode == Mode.CREATING:
            Class.__mode = Mode.PLACING
        if Class.__mode != Mode.PLACING:
            raise Exception("Cannot calculate inheritance level when not in placing mode")
        
        if self.inheritanceLevel != 0:
            return self.inheritanceLevel
        if self.inheritFrom == []:
            self.inheritanceLevel = 1
            return 1
        self.inheritanceLevel = max([Class.findClass(inherited).calcInheritanceLevel() for inherited in self.inheritFrom]) + 1

        # check if the class is an orphan
        if self.inheritanceLevel != 0:
            self.isOrphan = False
    
        for _class in Class.__instances:
            if self.name in _class.inheritFrom:
                _class.isOrphan = False
                break
        return self.inheritanceLevel
        
    
    @staticmethod
    def findClass(name : str) -> 'Class':
        for instance in Class.__instances:
            if instance.name == name:
                return instance
        return None
    
    
    def compute(self) -> str:
        if Class.__mode == Mode.PLACING:
            Class.__mode = Mode.WRITING
        if Class.__mode != Mode.WRITING:
            raise Exception("Cannot compute the class when not in writing mode")
        
        attibutes = [
            "\\attribute{"
            + visibiliyToTeX(attribute['visibility'])
            + " "
            + name.split('.')[-1]
            + " : "
            + attribute['type']
            + "}"
            for name, attribute in self.attributes.items()
        ]
        attibutes.extend(
            "\\attribute{"
            + visibiliyToTeX(property['visibility'])
            + " "
            + name.split('.')[-1]
            + " : "
            + property['type']
            + "}"
            for name, property in self.properties.items()
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
            for name, method in self.methods.items()
        ]
        
        inheritance = [
            "\\inherit{" + parent + "}"
            for parent in self.inheritFrom
        ]
        
        result =  """\\begin{class}[text width=""" + str(self.width) + """em]{""" + self.name + """}{""" + str(self.x) + "em ," + str(self.y) + """ex}
""" + "\n".join(inheritance) + """
""" + "\n".join(attibutes) + """
""" + "\n".join(methods) + """
\\end{class}
"""

        return result.replace("_", r"\string_")
    
    
    @staticmethod
    def placeAll():
        """
        Set the x and y coordinates of all the classes
        """
        if Class.__mode == Mode.CREATING:
            Class.__mode = Mode.PLACING
        if Class.__mode != Mode.PLACING:
            raise Exception("Cannot place all classes when not in placing mode")
        
        for _class in Class.__instances:
            _class.calcInheritanceLevel()
            
        
        grid = [] # type: list[list[Class]]
            
        # first, place the classes witch aren't orphans
        # classes with the lowest inheritance level will be placed first, at the top of the diagram
        
        classes = sorted(Class.__instances, key = lambda x: x.inheritanceLevel)
        classes = [x for x in classes if not x.isOrphan]
        classes = groupBy(classes, lambda x: x.inheritanceLevel)
        for level in classes:
            for _class in level:
                if grid == []:
                    grid.append([_class])
                    continue
                for i, row in enumerate(grid):
                    if all([_class.x - _class.width > x.width + x.x for x in row]):
                        grid[i].append(_class)
                        break
                else:
                    grid.append([_class])
        
        # then, place the orphans where there is space
        orphans = [x for x in Class.__instances if x.isOrphan]
        for _class in orphans:
            if grid == []:
                grid.append([_class])
                continue
            for i, row in enumerate(grid):
                if all([_class.x - _class.width > x.width + x.x for x in row]):
                    grid[i].append(_class)
                    break
            else:
                grid.append([_class])
                
        row_heights = [max([x.height for x in row]) for row in grid]
        row_heights = [0] + row_heights
        row_heights = [sum(row_heights[:i]) for i in range(1, len(row_heights))]
        
        col_widths = [max([x.width for x in row]) for row in grid]
        col_widths = [0] + col_widths

        for i, row in enumerate(grid):
            for j, _class in enumerate(row):
                _class.x = col_widths[j] + _class.width
                _class.y = row_heights[i] + _class.height
                
        return grid
    