from models import SearchResult


def search(G, start: int, goal: int, weight: str = 'custom_weight', depth_limit: int = 50) -> SearchResult:
    """
    Depth-Limited Search (DLS).
    DFS variant that stops exploring at specified depth limit.
    Prevents infinite loops in cyclic graphs while maintaining depth-first behavior.
    """
    if start == goal:
        return SearchResult(path=[start], nodes_expanded=0)

    visited = set()
    expansion_log = []
    nodes_expanded = 0
    parent_map = {}

    def dfs_recursive(node: int, depth: int) -> list[int] | None:
        nonlocal nodes_expanded
        visited.add(node)
        expansion_log.append(node)
        nodes_expanded += 1

        if node == goal:
            return [node]

        if depth >= depth_limit:
            return None

        # Explore neighbors in depth-first order
        for neighbor in G.successors(node):
            if neighbor not in visited:
                edge_data = G[node][neighbor]
                edge_cost = min(d.get(weight, 1.0) for d in edge_data.values())
                
                parent_map[neighbor] = node
                path = dfs_recursive(neighbor, depth + 1)
                
                if path is not None:
                    return [node] + path

        return None

    path = dfs_recursive(start, 0)
    if path is None:
        return SearchResult(path=[], nodes_expanded=nodes_expanded,
                            expansion_log=expansion_log, parent_map=parent_map)
    
    return SearchResult(path=path, nodes_expanded=nodes_expanded,
                       expansion_log=expansion_log, parent_map=parent_map)
