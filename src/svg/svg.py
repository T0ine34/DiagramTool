import lxml.etree as ET

from typing import Sequence

try:
    from .customTypes import Class, Enum, Relation, Element
except ImportError:
    from customTypes import Class, Enum, Relation, Element
    
from gamuLogger import Logger
    
SPACE = 50

class SVG:
    def __init__(self) -> None:
        self.__tree = ET.Element("svg", None, None)
        self.__tree.attrib['xmlns'] = "http://www.w3.org/2000/svg"
        self.__objects = []

    def append(self, element) -> None:
        if isinstance(element, Element):
            self.__objects.append(element)
        self.__tree.append(element.build())
        
    def save(self, filename : str, showBorder : bool = False) -> None:
        with open(filename, "w") as file:
            file.write(self.toString(showBorder))
        
    def attrib(self, key, value) -> None:
        self.__tree.attrib[key] = value
        
    def toString(self, showBorder : bool = False) -> str:
        # calculate width and height of svg
        width = max(int(obj.SE[0]) for obj in self.__objects) + SPACE
        height = max(int(obj.SE[1]) for obj in self.__objects) + SPACE
        self.attrib('width', f"{width}")
        self.attrib('height', f"{height}")
        
        if showBorder:
            self.drawBorder(width, height)
        return ET.tostring(self.__tree, pretty_print=True).decode("utf-8") #type: ignore

    def placeObjects(self, objects : Sequence[Element]) -> None:
        
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
                
                # while any(obj.isOverlapping(other) for other in line if other != obj):
                #     obj.place(obj.x + SPACE, obj.y)
                def getOverlapping():
                    overlapping = None
                    for other in line:
                        if other == obj:
                            continue
                        if obj.isOverlapping(other):
                            overlapping = other
                            break
                    return overlapping
                
                overlapping = getOverlapping()
                while overlapping:
                    obj.place(overlapping.E[0] + SPACE, obj.y)
                    overlapping = getOverlapping()
                
                
                
                self.append(obj)
                x += obj.width + SPACE
            y += lineHeights[i] + SPACE
            
        # place enums (all in one line)
        y -= SPACE # remove last SPACE
        x = SPACE
        for obj in [obj for obj in objects if isinstance(obj, Enum)]:
            obj.place(x, y)
            self.append(obj)
            x += obj.width + 30
        
            
    def placeRelations(self, objects : Sequence[Element], data : dict) -> None:
        for sourceName, sourceData in data['classes'].items():
            source = next(obj for obj in objects if obj.name == sourceName)
            for targetName in sourceData['inheritFrom']:
                target = next(obj for obj in objects if obj.name == targetName)
                relation = Relation(source, target, Relation.TYPE.INHERITANCE)
                self.append(relation)


    def drawBorder(self, width : int, height : int) -> None:
        border = ET.Element("rect", None, None)
        border.attrib['x'] = "0"
        border.attrib['y'] = "0"
        border.attrib['width'] = f"{width}"
        border.attrib['height'] = f"{height}"
        border.attrib['fill'] = "none"
        border.attrib['stroke'] = "red"
        border.attrib['stroke-width'] = "1"
        self.__tree.append(border)