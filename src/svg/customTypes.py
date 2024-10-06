# import xml.etree.ElementTree as ET
import lxml.etree as ET
from enum import Enum
import math

try:
    from .utils import getTextWidth, getTextHeight, Attribute2Text, Method2Text
except ImportError:
    from utils import getTextWidth, getTextHeight, Attribute2Text, Method2Text
    
COLOR = "black"
TITLE_FONT_SIZE = 26
ATTRIBUTE_FONT_SIZE = 20
SEPARATOR_HEIGHT = 20

def Separator(x : int, y : int, width : int, color : str = 'black') -> ET.Element:   
    separator = ET.Element("line")
    separator.attrib["x1"] = "0"
    separator.attrib["y1"] = "0"
    separator.attrib["x2"] = f"{width}"
    separator.attrib["y2"] = "0"
    separator.attrib["stroke"] = color
    separator.attrib["stroke-width"] = "1"
    separator.attrib["transform"] = f"translate({x} {y})"
    
    return separator



class Element:
    """Base class for all elements"""
    def __init__(self, name : str):
        self.name = name
        
        self._width = 0
        self._height = 0
        
        self.__x = 0
        self.__y = 0
        
        self.__placed = False
    
    def place(self, x : int, y : int) -> None:
        self.__placed = True
        self.__x = x
        self.__y = y
        
    def build(self) -> ET.Element:

        element = ET.Element("g")
        element.attrib["class"] = "element"
        element.attrib["id"] = self.name
        
        return element
    
    @property
    def placed(self) -> bool:
        return self.__placed
    
    @property
    def NW(self) -> tuple[int, int]:
        """North-West corner"""
        return (self.__x, self.__y)
    
    @property
    def NE(self) -> tuple[int, int]:
        """North-East corner"""
        return (self.__x + self._width, self.__y)
    
    @property
    def SW(self) -> tuple[int, int]:
        """South-West corner"""
        return (self.__x, self.__y + self._height)
    
    @property
    def SE(self) -> tuple[int, int]:
        """South-East corner"""
        return (self.__x + self._width, self.__y + self._height)
    
    @property
    def N(self) -> tuple[int, int]:
        """North center"""
        return (self.__x + self._width/2, self.__y)
    
    @property
    def S(self) -> tuple[int, int]:
        """South center"""
        return (self.__x + self._width/2, self.__y + self._height)
    
    @property
    def W(self) -> tuple[int, int]:
        """West center"""
        return (self.__x, self.__y + self._height/2)
    
    @property
    def E(self) -> tuple[int, int]:
        """East center"""
        return (self.__x + self._width, self.__y + self._height/2)


    @property
    def x(self) -> int:
        return self.__x
    
    @property
    def y(self) -> int:
        return self.__y


    @property
    def width(self) -> int:
        return self._width
    
    @property
    def height(self) -> int:
        return self._height

    @property
    def center(self) -> tuple[int, int]:
        return (self.__x + self._width/2, self.__y + self._height/2)

    def getNearSide(self, x : int, y : int) -> float:
        distance = {
            self.N : ((self.N[0] - x)**2 + (self.N[1] - y)**2),
            self.S : ((self.S[0] - x)**2 + (self.S[1] - y)**2),
            self.W : ((self.W[0] - x)**2 + (self.W[1] - y)**2),
            self.E : ((self.E[0] - x)**2 + (self.E[1] - y)**2)
        }
        
        return min(distance, key=distance.get)

    def isOverlapping(self, other : 'Element') -> bool:
        if not self.placed or not other.placed:
            return False
        # check if some point of self is inside other
        for x in range( int(self.__x),  int(self.__x + self._width), 10):
            for y in range( int(self.__y),  int(self.__y + self._height), 10):
                if other.__x <= x <= other.__x + other._width and other.__y <= y <= other.__y + other._height:
                    return True
        return False

class Class(Element):
    __instances = {} # type: dict[str, Class]
    def __init__(self, name : str, attributes : dict, properties : dict, methods : dict, inheritFrom : list):
        super().__init__(name)
        self.attributes = attributes
        self.properties = properties
        self.methods = methods
        self.inheritFrom = inheritFrom
        
        self._width = self.__calcWidth()
        self._height = self.__calcHeight()
        
        Class.__instances[name] = self
         
    def __calcWidth(self) -> int:
        maxLen = getTextWidth(self.name, TITLE_FONT_SIZE)
        for key, data in self.attributes.items():
            maxLen = max(maxLen, getTextWidth(Attribute2Text(key, data), ATTRIBUTE_FONT_SIZE))
        for key in self.properties:
            maxLen = max(maxLen, getTextWidth(Attribute2Text(key, self.properties[key]), ATTRIBUTE_FONT_SIZE))
        for key in self.methods:
            maxLen = max(maxLen, getTextWidth(Method2Text(key, self.methods[key]), ATTRIBUTE_FONT_SIZE))
        return maxLen
    
    def __calcHeight(self) -> int:
        height = getTextHeight(TITLE_FONT_SIZE)
        height += SEPARATOR_HEIGHT # separator
        height += getTextHeight(ATTRIBUTE_FONT_SIZE) * (len(self.attributes) + len(self.properties) + len(self.methods))
        height += SEPARATOR_HEIGHT # separator
        return height
        
    @staticmethod
    def fromDict(name : str, classDict : dict) -> 'Class':
        return Class(name, classDict['attributes'], classDict['properties'], classDict['methods'], classDict['inheritFrom'])
    
    def getInheritanceLevel(self) -> int:
        level = 0
        for parent in self.inheritFrom:
            level = max(level, Class.__instances[parent].getInheritanceLevel() + 1)
        return level
    
    def getInheritanceTreeSize(self) -> int:
        return self.__reqGetInheritanceTreeSize() + 1 
    
    def __reqGetInheritanceTreeSize(self) -> int:
        size = 0
        #count all parents
        size += self.getInheritanceLevel() # number of parents (excluding itself)
        
        #count all children
        for cls in Class.__instances.values():
            if self.name in cls.inheritFrom:
                size += cls.__reqGetInheritanceTreeSize()
        return size
    
    def build(self) -> ET.Element:   
        G = super().build()
             
        # group
        G.attrib["class"] = "class"
        G.attrib['width'] = f"{self._width}"
        G.attrib['height'] = f"{self._height}"
        G.attrib['color'] = COLOR
        G.attrib['transform'] = f"translate({self.x} {self.y})"
        
        # border
        border = ET.Element("rect")
        border.attrib["class"] = "border"
        border.attrib["x"] = "0"
        border.attrib["y"] = "0"
        border.attrib["width"] = f"{self._width}"
        border.attrib["height"] = f"{self._height}"
        border.attrib['stroke-width'] = "1"
        border.attrib['fill'] = "none"
        border.attrib['stroke'] = "currentColor"
        G.append(border)
        
        y = 0
        
        # class name
        className = ET.Element("text")
        className.text = self.name
        className.attrib["class"] = "className"
        className.attrib['transform'] = f"translate({self._width/2}, {ATTRIBUTE_FONT_SIZE + 5})"
        className.attrib['text-anchor'] = "middle"
        className.attrib['x'] = "0"
        className.attrib['y'] = f"{y}"
        className.attrib['fill'] = "currentColor"
        className.attrib['stroke'] = "none"
        className.attrib['font-size'] = f"{TITLE_FONT_SIZE}px"
        
        G.append(className)
        y += getTextHeight(TITLE_FONT_SIZE) + 5
        
        # separator
        G.append(Separator(0, y, self._width, 'currentColor'))
        y += SEPARATOR_HEIGHT
        
        # attributes
        for key, value in self.attributes.items():
            attribute = ET.Element("text")
            attribute.text = Attribute2Text(key, value)
            attribute.attrib["class"] = "attribute"
            attribute.attrib['transform'] = f"translate(5, {y})"
            attribute.attrib['x'] = "0"
            attribute.attrib['y'] = "0"
            attribute.attrib['font-size'] = f"{ATTRIBUTE_FONT_SIZE}px"
            attribute.attrib['fill'] = "currentColor"
            attribute.attrib['stroke'] = "none"
            G.append(attribute)
            y += getTextHeight(ATTRIBUTE_FONT_SIZE)
            
        # properties
        for key, value in self.properties.items():
            _property = ET.Element("text")
            _property.text = Attribute2Text(key, value)
            _property.attrib["class"] = "property"
            _property.attrib['transform'] = f"translate(5, {y})"
            _property.attrib['x'] = "0"
            _property.attrib['y'] = "0"
            _property.attrib['font-size'] = f"{ATTRIBUTE_FONT_SIZE}px"
            _property.attrib['fill'] = "currentColor"
            _property.attrib['stroke'] = "none"
            G.append(_property)
            y += getTextHeight(ATTRIBUTE_FONT_SIZE)
            
        # separator
        G.append(Separator(0, y, self._width, 'currentColor'))
        y += SEPARATOR_HEIGHT
        
        # methods
        for key, value in self.methods.items():
            method = ET.Element("text")
            method.text = Method2Text(key, value)
            method.attrib["class"] = "method"
            method.attrib['transform'] = f"translate(5, {y})"
            method.attrib['x'] = "0"
            method.attrib['y'] = "0"
            method.attrib['font-size'] = f"{ATTRIBUTE_FONT_SIZE}px"
            method.attrib['fill'] = "currentColor"
            method.attrib['stroke'] = "none"
            G.append(method)
            y += getTextHeight(ATTRIBUTE_FONT_SIZE)
        
        
        return G  
        
    def getBestX(self) -> int:
        if len(self.inheritFrom) == 0:
            return -1
        best = sum(Class.__instances[parent].S[0] for parent in self.inheritFrom) // len(self.inheritFrom)
        return best - self._width // 2
        
class Enum(Element):
    def __init__(self, name : str, values : list, methods : dict):
        super().__init__(name)
        self.values = values
        self.methods = methods
        
        self._width = self.__calcWidth()
        self._height = self.__calcHeight()
        
    def __calcWidth(self) -> int:
        maxLen = getTextWidth(self.name, TITLE_FONT_SIZE)
        maxLen = max(maxLen, getTextWidth("<<enumeration>>", ATTRIBUTE_FONT_SIZE))
        for value in self.values:
            maxLen = max(maxLen, getTextWidth(value, ATTRIBUTE_FONT_SIZE))
        for key in self.methods:
            maxLen = max(maxLen, getTextWidth(Method2Text(key, self.methods[key]), ATTRIBUTE_FONT_SIZE))
        return maxLen
    
    def __calcHeight(self) -> int:
        height = getTextHeight(ATTRIBUTE_FONT_SIZE)
        height += getTextHeight(TITLE_FONT_SIZE)
        height += SEPARATOR_HEIGHT
        height += getTextHeight(ATTRIBUTE_FONT_SIZE) * (len(self.values) + len(self.methods))
        height += SEPARATOR_HEIGHT
        return height
    
    @staticmethod
    def fromDict(name : str, enumDict : dict) -> 'Enum':
        return Enum(name, enumDict['values'], enumDict['methods'])
    
    def build(self) -> ET.Element:
        G = super().build()
    
        # group
        G.attrib["class"] = "enum"
        G.attrib['width'] = f"{self._width}"
        G.attrib['height'] = f"{self._height}"
        G.attrib['color'] = COLOR
        G.attrib['transform'] = f"translate({self.x} {self.y})"
        
        # border
        border = ET.Element("rect")
        border.attrib["class"] = "border"
        border.attrib["x"] = "0"
        border.attrib["y"] = "0"
        border.attrib["width"] = f"{self._width}"
        border.attrib["height"] = f"{self._height}"
        border.attrib['stroke-width'] = "1"
        border.attrib['fill'] = "none"
        border.attrib['stroke'] = "currentColor"
        G.append(border)
        
        y = 0
        
        # <<enumeration>>
        enumSurTitle = ET.Element("text")
        enumSurTitle.text = "<<enumeration>>"
        enumSurTitle.attrib["class"] = "enumSurTitle"
        enumSurTitle.attrib['transform'] = f"translate({self._width/2}, {ATTRIBUTE_FONT_SIZE + 5})"
        enumSurTitle.attrib['text-anchor'] = "middle"
        enumSurTitle.attrib['x'] = "0"
        enumSurTitle.attrib['y'] = f"{y}"
        enumSurTitle.attrib['fill'] = "currentColor"
        enumSurTitle.attrib['stroke'] = "none"
        enumSurTitle.attrib['font-size'] = f"{ATTRIBUTE_FONT_SIZE}px"
        enumSurTitle.attrib['font-style'] = "italic"
        
        G.append(enumSurTitle)
        y += getTextHeight(ATTRIBUTE_FONT_SIZE) + 5
        
        # name
        enumName = ET.Element("text")
        enumName.text = self.name
        enumName.attrib["class"] = "enumName"
        enumName.attrib['transform'] = f"translate({self._width/2}, {ATTRIBUTE_FONT_SIZE + 5})"
        enumName.attrib['text-anchor'] = "middle"
        enumName.attrib['x'] = "0"
        enumName.attrib['y'] = f"{y}"
        enumName.attrib['fill'] = "currentColor"
        enumName.attrib['stroke'] = "none"
        enumName.attrib['font-size'] = f"{TITLE_FONT_SIZE}px"
        
        G.append(enumName)
        y += getTextHeight(TITLE_FONT_SIZE) + 5
        
        # separator
        G.append(Separator(0, y, self._width, 'currentColor'))
        y += SEPARATOR_HEIGHT
        
        # values
        for value in self.values:
            valueElement = ET.Element("text")
            valueElement.text = value
            valueElement.attrib["class"] = "value"
            valueElement.attrib['transform'] = f"translate(5, {y})"
            valueElement.attrib['x'] = "0"
            valueElement.attrib['y'] = "0"
            valueElement.attrib['font-size'] = f"{ATTRIBUTE_FONT_SIZE}px"
            valueElement.attrib['fill'] = "currentColor"
            valueElement.attrib['stroke'] = "none"
            G.append(valueElement)
            y += getTextHeight(ATTRIBUTE_FONT_SIZE)
            
        # separator
        G.append(Separator(0, y, self._width, 'currentColor'))
        y += SEPARATOR_HEIGHT
        
        # methods
        for key, value in self.methods.items():
            method = ET.Element("text")
            method.text = Method2Text(key, value)
            method.attrib["class"] = "method"
            method.attrib['transform'] = f"translate(5, {y})"
            method.attrib['x'] = "0"
            method.attrib['y'] = "0"
            method.attrib['font-size'] = f"{ATTRIBUTE_FONT_SIZE}px"
            method.attrib['fill'] = "currentColor"
            method.attrib['stroke'] = "none"
            G.append(method)
            y += getTextHeight(ATTRIBUTE_FONT_SIZE)
            
        return G
        


    
class ARROW_TYPE(Enum):
    DIAMOND = 1
    TRIANGLE = 2
    OPEN_TRIANGLE = 3
    

def Arrow(position : tuple[int, int], angle : float, arrowType : ARROW_TYPE, filled : bool):
    match arrowType:
        case ARROW_TYPE.DIAMOND:
            arrow = ET.Element("polygon")
            arrow.attrib["points"] = f"{position[0]-5},{position[1]-5} {position[0]+5},{position[1]} {position[0]-5},{position[1]+5} {position[0]-15},{position[1]}"
            arrow.attrib["fill"] = "currentColor" if filled else "none"
        case ARROW_TYPE.TRIANGLE:
            arrow = ET.Element("polygon")
            arrow.attrib["points"] = f"{position[0]-5},{position[1]-5} {position[0]+5},{position[1]} {position[0]-5},{position[1]+5}"
            arrow.attrib["fill"] = "currentColor" if filled else "none"
        case ARROW_TYPE.OPEN_TRIANGLE:
            arrow = ET.Element("polyline")
            arrow.attrib["points"] = f"{position[0]-5},{position[1]-5} {position[0]+5},{position[1]} {position[0]-5},{position[1]+5}"
            arrow.attrib["fill"] = "none"
            if filled:
                raise ValueError("Open triangle can't be filled")
        case _:
            raise ValueError("Invalid arrow type")
    
    arrow.attrib["stroke"] = "currentColor"
    arrow.attrib["stroke-width"] = "1"
    arrow.attrib["transform"] = f"rotate({angle} {position[0]} {position[1]}) translate(-5)"
    
    return arrow
    

class LINE_TYPE(Enum):
    SOLID = 0
    DASHED = 1
    
def Line(start : tuple[int, int], end : tuple[int, int], lineType : LINE_TYPE):
    line = ET.Element("line")
    line.attrib["x1"] = f"{start[0]}"
    line.attrib["y1"] = f"{start[1]}"
    line.attrib["x2"] = f"{end[0]}"
    line.attrib["y2"] = f"{end[1]}"
    line.attrib["stroke"] = "currentColor"
    line.attrib["stroke-width"] = "1"
    
    match lineType:
        case LINE_TYPE.SOLID:
            pass
        case LINE_TYPE.DASHED:
            line.attrib["stroke-dasharray"] = "5,5"
        case _:
            raise ValueError("Invalid line type")
    
    return line


def GeomLine(start : tuple[int, int], end : tuple[int, int], lineType : LINE_TYPE):
    G = ET.Element("g")
    G.attrib["class"] = "relation"
    
    if start[0] == end[0]:
        G.append(Line(start, end, lineType))
        return G
    
    p0 = start
    p1 = (start[0], (start[1]+end[1])//2)
    p2 = (end[0], (start[1]+end[1])//2)
    p3 = end
    
    G.append(Line(p0, p1, lineType))
    G.append(Line(p1, p2, lineType))
    G.append(Line(p2, p3, lineType))

    return G

    
class Relation:
    class TYPE(Enum):
        ASSOCIATION = 0
        AGGREGATION = 1
        COMPOSITION = 2
        INHERITANCE = 3
        IMPLEMENTATION = 4
        DEPENDENCY = 5
    def __init__(self, source : Element, target : Element, relationType : TYPE):
        self.source = source
        self.target = target
        self.relationType = relationType
        
    def build(self) -> ET.Element:
        G = ET.Element("g")
        G.attrib["class"] = "relation"
        
        startPoint = self.source.N
        endPoint = self.target.S
        
        # angle = math.degrees(math.atan2(endPoint[1] - startPoint[1], endPoint[0] - startPoint[0]))
        angle = -90
        
        
        match self.relationType:
            case Relation.TYPE.ASSOCIATION: # Solid line, open triangle
                G.append(GeomLine(startPoint, endPoint, LINE_TYPE.SOLID))
                G.append(Arrow(endPoint, angle, ARROW_TYPE.OPEN_TRIANGLE, False))
                
            case Relation.TYPE.AGGREGATION: # Solid line, empty diamond
                G.append(GeomLine(startPoint, endPoint, LINE_TYPE.SOLID))
                G.append(Arrow(endPoint, angle, ARROW_TYPE.DIAMOND, False))
                
            case Relation.TYPE.COMPOSITION: # Solid line, filled diamond
                G.append(GeomLine(startPoint, endPoint, LINE_TYPE.SOLID))
                G.append(Arrow(endPoint, angle, ARROW_TYPE.DIAMOND, True))
                
            case Relation.TYPE.INHERITANCE: # Solid line, filled triangle
                G.append(GeomLine(startPoint, endPoint, LINE_TYPE.SOLID))
                G.append(Arrow(endPoint, angle, ARROW_TYPE.TRIANGLE, True))
                
            case Relation.TYPE.IMPLEMENTATION: # Dashed line, filled triangle
                G.append(GeomLine(startPoint, endPoint, LINE_TYPE.DASHED))
                G.append(Arrow(endPoint, angle, ARROW_TYPE.TRIANGLE, True))
                
            case Relation.TYPE.DEPENDENCY: # Dashed line, open triangle
                G.append(GeomLine(startPoint, endPoint, LINE_TYPE.DASHED))
                G.append(Arrow(endPoint, angle, ARROW_TYPE.OPEN_TRIANGLE, False))
                
            case _:
                raise ValueError("Invalid relation type")

        return G

