import networkx as nx
import matplotlib.pyplot as plt
import numpy as np
from scipy.optimize import linear_sum_assignment

# Function to create a grid
def create_grid(rows, cols, spacing):
    return [(x * spacing, y * spacing) for x in range(cols) for y in range(rows)]

# Function to check if a vertex overlaps with another on the grid
def is_overlapping_on_grid(vertex_positions, vertex_sizes, margin):
    for i, (v1, pos1) in enumerate(vertex_positions.items()):
        for j, (v2, pos2) in enumerate(vertex_positions.items()):
            if i >= j:
                continue
            size1 = [dim + margin for dim in vertex_sizes[v1]]  # Add margin to size
            size2 = [dim + margin for dim in vertex_sizes[v2]]  # Add margin to size
            if (
                abs(pos1[0] - pos2[0]) < (size1[0] + size2[0]) / 2
                and abs(pos1[1] - pos2[1]) < (size1[1] + size2[1]) / 2
            ):
                return True
    return False

# Function to assign vertices to grid positions
def assign_to_grid(G, grid, vertex_sizes, margin):
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
    
    return assigned_positions

# Function to plot the graph with vertices on a grid
def plot_graph_on_grid(G, positions, vertex_sizes, margin):
    plt.figure(figsize=(8, 8))
    for node, (x, y) in positions.items():
        width, height = vertex_sizes[node]
        width += margin  # Include margin in visualization
        height += margin  # Include margin in visualization
        rect = plt.Rectangle((x - width / 2, y - height / 2), width, height, color="lightblue", alpha=0.7)
        plt.gca().add_patch(rect)
    nx.draw(
        G, positions, with_labels=True, node_size=0,  # Use rectangles, so disable default nodes
        edge_color="gray"
    )
    plt.grid(True)
    plt.axis("equal")
    plt.show()

# Example graph
G = nx.Graph()
G.add_nodes_from(range(4))
G.add_edges_from([(0, 1), (1, 2), (2, 3), (3, 0), (0, 2)])

# Assign sizes to vertices
vertex_sizes = {node: (1, 1) for node in G.nodes}  # Example sizes (width, height)

# Define a margin (space around each vertex)
margin = 0.5

# Create a grid
grid_spacing = 2  # Ensure grid spacing is large enough to account for vertex size + margin
grid = create_grid(rows=5, cols=5, spacing=grid_spacing)

# Assign vertices to grid positions
positions = assign_to_grid(G, grid, vertex_sizes, margin)

print(positions)

# Plot the graph
# plot_graph_on_grid(G, positions, vertex_sizes, margin)
