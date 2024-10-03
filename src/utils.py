def visibiliyToTeX(visibility : str):
    if visibility == "private":
        return "-"
    elif visibility == "protected":
        return "#"
    elif visibility == "public":
        return "+"
    else:
        return "?"
    
    
def groupBy(l : list, key : callable) -> list[list]:
    """
    example : 
    groupBy([1, 1, 3, 4, 4, 6], lambda x: x) -> [[1, 1], [3], [4, 4], [6]]
    """
    result = []
    for elem in l:
        if not result or key(result[-1][0]) != key(elem):
            result.append([elem])
        else:
            result[-1].append(elem)
    return result