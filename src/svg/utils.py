import lxml.etree as ET

from gamuLogger import Logger

Logger.setModule("SVG_Utils")


def getTextWidth(text : str, fontsize : int) -> int:
    return len(text) * 10 * (fontsize // 16)

def getTextHeight(fontsize : int) -> int:
    return fontsize + 5


def visibiliyToUML(visibility : str):
    if visibility == "private":
        return "–"
    elif visibility == "protected":
        return "#"
    elif visibility == "public":
        return "+"
    else:
        return "?"
    
def Arg2Text(arg : dict) -> str:
    return f"{arg['name']} : {arg['type']}"

def Args2Text(args : list) -> str:
    return ", ".join([Arg2Text(arg) for arg in args])

def Attribute2Text(name, attribute : dict) -> str:
    return f"{visibiliyToUML(attribute['visibility'])} {name.split('.')[-1]} : {attribute['type']}"

def Method2Text(name, method : dict) -> str:
    return f"{visibiliyToUML(method['visibility'])} {name.split('.')[-1]}({Args2Text(method['args'])}) : {method['return_type']}"


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




















if __name__ == "__main__":
    def createTextElement(text : str, x : int, y : int, fontsize : int) -> str:
        # sourcery skip: extract-duplicate-method
        # return f'<text transform="translate({x} {y})" text-anchor="middle" font-size="{fontsize}px" font-family="monospace">{text}</text>'
        G = ET.Element("g", None, None)
        G.attrib["transform"] = f"translate({x} {y})"
        G.attrib['color'] = "white"

        textElement = ET.Element("text", None, None)
        textElement.text = text
        textElement.attrib["text-anchor"] = "middle"
        textElement.attrib["font-size"] = f"{fontsize}px"
        textElement.attrib["font-family"] = "monospace"
        textElement.attrib["transform"] = f"translate({getTextWidth(text, fontsize)/2}, {fontsize})"
        textElement.attrib["stroke"] = "none"
        textElement.attrib["fill"] = "currentColor"
        G.append(textElement)
        
        border = ET.Element("rect", None, None)
        border.attrib["x"] = "0"
        border.attrib["y"] = "0"
        border.attrib["width"] = f"{getTextWidth(text, fontsize)}"
        border.attrib["height"] = f"{getTextHeight(fontsize)}"
        border.attrib["fill"] = "none"
        border.attrib["stroke"] = "currentColor"
        G.append(border)
        return ET.tostring(G).decode("utf-8")
        

    def getY():
        y = 0
        while True:
            y += 50
            yield y

   
    with open("testFont.svg", "w") as file:
        file.write('<svg xmlns="http://www.w3.org/2000/svg" width="1000" height="1000">\n')
        y = getY()
        for fontsize in range(10, 40, 2):
            file.write(createTextElement("Hello World", 100, next(y), fontsize))
            file.write("\n")
        file.write("</svg>")