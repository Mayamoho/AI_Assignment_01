import heapq
from models import SearchResult
from heuristic import haversine


def search(G, start: int, goal: int, weight: str = 'custom_weight') -> SearchResult:
    """
    Best-First Search.
    Uses only heuristic (h(n)) to guide search - ignores path cost (g(n)).
    Greedy approach that always expands the node that appears closest to goal.
    """
    if start == goal:
        return SearchResult(path=[start], nodes_expanded=0)

    counter = [1]
    
    def push(heap, h, node):
        counter[0] += 1
        heapq.heappush(heap, (h, counter[0], node))

    # Priority queue ordered by heuristic only (no g-cost)
    heap = [(haversine(G, start, goal), 0, start)]
    visited = set()
    parent_map = {start: None}
    expansion_log = []
    nodes_expanded = 0

    while heap:
        _, _, node = heapq.heappop(heap)
        
        if node in visited:
            continue
            
        visited.add(node)
        expansion_log.append(node)
        nodes_expanded += 1

        if node == goal:
            # Reconstruct path
            path = []
            current = node
            while current is not None:
                path.append(current)
                current = parent_map[current]
            path.reverse()
            
            return SearchResult(path=path, nodes_expanded=nodes_expanded,
                              expansion_log=expansion_log, parent_map=parent_map)

        # Expand neighbors
        for neighbor in G.successors(node):
            if neighbor not in visited and neighbor not in parent_map:
                try:
                    h = haversine(G, neighbor, goal)
                except (KeyError, Exception):
                    continue
                
                parent_map[neighbor] = node
                push(heap, h, neighbor)

    return SearchResult(path=[], nodes_expanded=nodes_expanded,
                       expansion_log=expansion_log, parent_map=parent_map)
