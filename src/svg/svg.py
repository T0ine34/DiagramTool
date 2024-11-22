import lxml.etree as ET

from typing import Sequence
import networkx as nx 
from scipy.optimize import linear_sum_assignment
import numpy as np
import colour

try:
    from .customTypes import Class, _Enum as Enum, Relation, Element
    from .utils import groupBy
except ImportError:
    from customTypes import Class, _Enum as Enum, Relation, Element
    from utils import groupBy
    
from gamuLogger import Logger
Logger.setModule("DiagramTool.SVG")
    
SPACE = 100



def assign_to_grid(G : nx.Graph, grid, vertex_sizes, margin):
    # Calculate the cost matrix based on distances between vertices and grid points
    cost_matrix = []
    vertex_list = list(G.nodes)
    for v in vertex_list:
        v_cost = []
        for gx, gy in grid:
            # Add a cost proportional to the sum of vertex sizes (to maintain spacing)
            size_with_margin = sum([dim + margin for dim in vertex_sizes[v]])
            v_cost.append(size_with_margin + np.linalg.norm([gx, gy]))
        cost_matrix.append(v_cost)
    
    # Solve assignment problem to minimize total cost
    row_ind, col_ind = linear_sum_assignment(cost_matrix)
    assigned_positions = {vertex_list[i]: grid[j] for i, j in zip(row_ind, col_ind)}
    
    counter = 0
    for k, v in assigned_positions.items():
        assigned_positions[k] = (v[0] + margin, v[1] + margin)
        Logger.debug(f"Assigned {k} to {assigned_positions[k]}")
    
    return assigned_positions



class SVG:
    def __init__(self, color : colour.Color) -> None:
        self.__tree = ET.Element("svg", None, None)
        self.__tree.attrib['xmlns'] = "http://www.w3.org/2000/svg"
        self.__objects = []
        self.__color = color

    def append(self, element) -> None:
        if isinstance(element, Element):
            self.__objects.append(element)
        self.__tree.append(element.build(self.__color))
        
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

    def placeObjects(self, classes : Sequence[Class], enums : Sequence[Enum]) -> None:
        
        # place classes
        classes_index = list(enumerate(classes)) # form of (index, obj)
        vertices = range(len(classes))
        edges = [] # form of (source_index, target_index)
        for i, obj in classes_index:
            # inheritances
            for inh in obj.inheritFrom:
                target_index = next(index for index, o in classes_index if o.name == inh)
                edges.append((i, target_index))
            # compositions
            for comp in obj.composition:
                target_index = next(index for index, o in classes_index if o.name == comp)
                edges.append((i, target_index))
            # aggregations
            for agg in obj.aggregation:
                target_index = next(index for index, o in classes_index if o.name == agg)
                edges.append((i, target_index))
                
        vertexSizes = { i: (c.width, c.height) for i, c in classes_index}
        
        G = nx.Graph()
        G.add_nodes_from(vertices)
        G.add_edges_from(edges)
        
        x_spacing = max(c.width for c in classes) + SPACE
        y_spacing = max(c.height for c in classes) + SPACE
        grid = [(x * x_spacing, y * y_spacing) for x in range(len(classes)) for y in range(len(classes))]
        
        assigned_positions = assign_to_grid(G, grid, vertexSizes, SPACE)
        
        for i, obj in classes_index:
            obj.place(*assigned_positions[i])
            self.append(obj)
        
        # place enums (all in one line)
        y = max(int(obj.SE[1]) for obj in classes) + SPACE
        x = SPACE
        for obj in enums:
            obj.place(x, y) 
            self.append(obj)
            x += obj.width + 30
        
            
    def placeRelations(self, objects : Sequence[Element], data : dict) -> None:
        for sourceName, sourceData in data['classes'].items():
            source = next(obj for obj in objects if obj.name == sourceName)
            
            # place inheritance relations
            for targetName in sourceData['inheritFrom']:
                target = next(obj for obj in objects if obj.name == targetName)
                relation = Relation(source, target, Relation.TYPE.INHERITANCE)
                self.append(relation)
                
            # place composition relations
            for targetName in sourceData['composition']:
                target = next(obj for obj in objects if obj.name == targetName)
                relation = Relation(source, target, Relation.TYPE.COMPOSITION)
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