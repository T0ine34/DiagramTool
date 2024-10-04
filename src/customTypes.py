try:
    from .utils import visibiliyToTeX, groupBy, DUMP
except ImportError:
    from utils import visibiliyToTeX, groupBy, DUMP
    
    
from gamuLogger import Logger
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
            raise RuntimeError("Cannot create a new class when not in creating mode")
        
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
            raise RuntimeError("Cannot calculate inheritance level when not in placing mode")
        
        if self.inheritanceLevel != 0:
            return self.inheritanceLevel
        if self.inheritFrom == []:
            self.inheritanceLevel = 0
            return 0
        self.inheritanceLevel = max(Class.findClass(inherited).calcInheritanceLevel() for inherited in self.inheritFrom) + 1
        return self.inheritanceLevel


    def calcOrphan(self):
        # check if the class is an orphan
        if self.inheritanceLevel != 0:
            Logger.info(f"{self.name} is not an orphan because it has an inheritance level of {self.inheritanceLevel}")
            self.isOrphan = False
            return False
    
        for _class in Class.__instances:
            if self.name in _class.inheritFrom:
                Logger.info(f"{self.name} is not an orphan because {_class.name} inherits from it")
                self.isOrphan = False
                return False
            
        Logger.info(f"{self.name} is an orphan")
        return self.isOrphan
        
    
    @staticmethod
    def findClass(name : str) -> 'Class':
        return next(
            (instance for instance in Class.__instances if instance.name == name),
            None,
        )
    
    
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
    def placeAll(maxWidth : int):
        """
        Set the x and y coordinates of all the classes
        maxWidth : the maximum width of the diagram, in em
        """
        if Class.__mode == Mode.CREATING:
            Class.__mode = Mode.PLACING
        if Class.__mode != Mode.PLACING:
            raise RuntimeError("Cannot place all classes when not in placing mode")

        for _class in Class.__instances:
            _class.calcInheritanceLevel()
            _class.calcOrphan()


        grid = [] # type: list[list[Class]]

        # first, place the classes witch aren't orphans
        # classes with the lowest inheritance level will be placed first, at the top of the diagram

        classes = sorted((x for x in Class.__instances if not x.isOrphan), key=lambda x: x.inheritanceLevel)
        DUMP(Class.__instances, "instances")
        DUMP(classes, "classes")
        for _class in classes:
            if len(grid) <= _class.inheritanceLevel:
                grid.append([_class])
            else:
                grid[_class.inheritance] = [_class] + grid[_class.inheritance]

        # then, place the orphans where there is space
        orphans = sorted((x for x in Class.__instances if x.isOrphan), key=lambda x: x.inheritanceLevel)
        for _class in orphans:
            for i, row in enumerate(grid):
                if sum(x.width for x in row) + _class.width < maxWidth:
                    grid[i].append(_class)
                    break
            else:
                grid.append([_class])


        # compute the x and y coordinates
        row_heights = [max(x.height+10 for x in row) for row in grid]
        row_heights = [0] + row_heights
        row_heights = [sum(row_heights[:i]) for i in range(1, len(row_heights))]

        col_widths = [max(x.width for x in row) for row in grid]
        col_widths = [0] + col_widths

        last_x = 0
        for i, row in enumerate(grid):
            for j, _class in enumerate(row):
                _class.x = last_x + col_widths[j]/2
                _class.y = row_heights[i] + _class.height/2
                last_x += col_widths[j]
            last_x = 0
            
        
        #center it around the origin (0, 0)
        currentMiddleX = sum(x.x for x in Class.__instances)/len(Class.__instances)
        currentMiddleY = sum(x.y for x in Class.__instances)/len(Class.__instances)
        for _class in Class.__instances:
            _class.x -= currentMiddleX
            _class.y -= currentMiddleY

        DUMP(grid, "grid")
        
        return grid
    