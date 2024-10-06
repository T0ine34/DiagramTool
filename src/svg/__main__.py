
import json
from . import SVG, createMissingClasses, Class, Enum


if __name__ == "__main__":
    with open('out.json', 'r') as file:
        data = json.load(file)
    createMissingClasses(data)
    
    objects = [
        Class.fromDict(key, value) for key, value in data['classes'].items()
    ]
    objects.extend(
        Enum.fromDict(key, value) for key, value in data['enums'].items()
    )
    svg = SVG()

    # place objects
    svg.placeObjects(objects)

    # place relations
    svg.placeRelations(objects, data)

    # calculate width and height of svg
    width = max(obj.SE[0] for obj in objects) + 10
    height = max(obj.SE[1] for obj in objects) + 10
    svg.attrib('width', f"{width}")
    svg.attrib('height', f"{height}")

    svg.save("test.svg", showBorder=True)
