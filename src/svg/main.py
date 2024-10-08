try:
    from .svg import SVG
    from .utils import createMissingClasses
    from .customTypes import Class, Enum, Relation, Element
except ImportError:
    from svg import SVG
    from utils import createMissingClasses
    from customTypes import Class, Enum, Relation, Element


def createDiagram(data) -> SVG:
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
    
    return svg


if __name__ == "__main__":
    import json
    import argparse
    
    parser = argparse.ArgumentParser()
    parser.add_argument("file", help="The json file to parse")
    args = parser.parse_args()
    
    with open(args.file, 'r') as f:
        data = json.load(f)

    svg = createDiagram(data)
    svg.save("test.svg", showBorder=True)