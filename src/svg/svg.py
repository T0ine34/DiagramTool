import lxml.etree as ET

try:
    from .customTypes import Class, Enum, Relation, Element
    from.utils import createMissingClasses
except ImportError:
    from customTypes import Class, Enum, Relation, Element
    from utils import createMissingClasses
    
    
SPACE = 20

class SVG:
    def __init__(self) -> None:
        self.__tree = ET.Element("svg")
        self.__tree.attrib['xmlns'] = "http://www.w3.org/2000/svg"

    def append(self, element) -> None:
        self.__tree.append(element)
        
    def save(self, filename : str, showBorder : bool = False) -> None:
        with open(filename, "w") as file:
            file.write(self.toString(showBorder))
        print(f"SVG generated in {filename}")
        
    def attrib(self, key, value) -> None:
        self.__tree.attrib[key] = value
        
    def toString(self, showBorder : bool = False) -> str:
        if showBorder:
            border = ET.Element("rect")
            border.attrib['x'] = "0"
            border.attrib['y'] = "0"
            border.attrib['width'] = self.__tree.attrib['width']
            border.attrib['height'] = self.__tree.attrib['height']
            border.attrib['fill'] = "none"
            border.attrib['stroke'] = "red"
            border.attrib['stroke-width'] = "1"
            self.__tree.append(border)
        return ET.tostring(self.__tree, pretty_print=True).decode("utf-8")

    def placeObjects(self, objects : list[Element]) -> None:
        
        #place classes
        nbLines = max([1] + [obj.getInheritanceTreeSize() for obj in objects if isinstance(obj, Class)])
        grid = [
            [
                obj
                for obj in objects
                if isinstance(obj, Class)
                and obj.getInheritanceLevel() == crtLine
            ]
            for crtLine in range(nbLines)
        ]
        
        lineHeights = [max([0] + [obj.height for obj in line]) for line in grid]
        
        y = SPACE
        for i, line in enumerate(grid):
            x = SPACE
            for obj in line:
                bestX = obj.getBestX()
                obj.place(bestX, y)
                if bestX == -1:
                    obj.place(x, y)
                
                while any(obj.isOverlapping(other) for other in line if other != obj):
                    obj.place(obj.x + SPACE, obj.y)
                
                self.append(obj.build())
                x += obj.width + SPACE
            y += lineHeights[i] + SPACE
            
        # place enums (all in one line)
        y += SPACE
        x = SPACE
        for obj in [obj for obj in objects if isinstance(obj, Enum)]:
            obj.place(x, y)
            self.append(obj.build())
            x += obj.width + 30
        
            
    def placeRelations(self, objects : list[Element], data : dict) -> None:
        for sourceName, sourceData in data['classes'].items():
            source = next(obj for obj in objects if obj.name == sourceName)
            for targetName in sourceData['inheritFrom']:
                target = next(obj for obj in objects if obj.name == targetName)
                relation = Relation(source, target, Relation.TYPE.INHERITANCE)
                self.append(relation.build())

