local queue = require "queue"
local stack = require "stack"


local Graph = { -- functions as a schema
    node_list = {
	node_id = {} -- Stores node metadata with metadata keys
    },
    edge_lists = {
	edge_id = { -- access the edge_list with Graph.edge_list_key
	    edge_list_key_1 = {
		out_node_id = {}, -- edge metadata
		out_node_id_2 = {} -- etc.
		-- . . .
	    },
	    edge_list_key_2 = {},
	}
	-- edge_id2, edge_id3, ...
    },
    edge_list_key = {}, -- access edge_lists
    degrees = {}, -- store the degrees of the nodes
    num_nodes = 0, -- number of nodes in the graph

    -- Store centrality measures
    degree_centrality = {},
    
    -- Directed?
    directed = false
}

function Graph:new(o)
    o = o or {}
    setmetatable(o, self)
    self.__index = self
    return o
end

function Graph:count_nodes()
    local num_nodes = 0
    for node_id, metadata in pairs(self.node_list) do
	num_nodes = num_nodes + 1
    end
    self.num_nodes = num_nodes
end

function Graph:compute_degrees(do_weighted)
    -- compute degree of nodes
    for node, node_edge_lists in pairs(self.edge_lists) do
	local node_degree = 0
	local edge_list = node_edge_lists[self.edge_list_key]

	for out_node, edge_labels in pairs(edge_list) do
	    if do_weighted then
		node_degree = node_degree + #edge_labels
	    else
		node_degree = node_degree + 1
	    end
	end
	self.degrees[node] = node_degree
    end
	 
end

function Graph:compute_degree_centrality()
    -- count degree and nodes
    self:count_nodes()
    self:compute_degrees()

    for node, degree in pairs(self.degrees) do
	self.degree_centrality[node] = self.degrees[node] / self.num_nodes
    end
end

--- Brandes' Algorithm
--- https://en.wikipedia.org/wiki/Brandes'_algorithm
function Graph:compute_betweenness_centrality()

    -- Make sure we count nodes
    if self.num_nodes == 0 then
	self:count_nodes()
    end

    local bc = {} -- betweenness centrality
    local delta = {}
    local sigma = {}
    local previous = {}
    local dist = {}

    for node_id in pairs(self.node_list) do
	bc[node_id] = 0	
    end

    for s in pairs(self.node_list) do

	for v in pairs(self.node_list) do
	    delta[v] = 0
	    sigma[v] = 0
	    previous[v] = {}
	    dist[v] = nil
	end

	sigma[s] = 1
	dist[s] = 0

	to_explore = queue()
	to_explore:enqueue(s)

	vertex_visit = stack.new()

	while not to_explore:empty() do
	    local u = to_explore:dequeue()
	    vertex_visit:push(u)

	    local neighbors = self.edge_lists[u] and self.edge_lists[u][self.edge_list_key]
	    
	    if neighbors then -- some nodes are isolated.
		for v in pairs(neighbors) do
		    if not dist[v] then
			dist[v] = dist[u] + 1
			to_explore:enqueue(v)
		    end
		    if dist[v] == dist[u] + 1 then
			sigma[v] = sigma[v] + sigma[u]
			table.insert(previous[v], u)
		    end
		end
	    end
	end

	while not vertex_visit:is_empty() do
	    local v = vertex_visit:pop()

	    for _, u in pairs(previous[v]) do 
		delta[u] = delta[u] + sigma[u] / sigma[v] * (1 + delta[v])
	    end

	    if v ~= s then
		bc[v] = bc[v] + delta[v]
	    end
	end
    end


    -- Normalize computed BC
    local scale -- scaling factor
    local n = self.num_nodes

    if self.directed then
	scale = (n - 1) * (n - 2)
    else
	scale = (n - 1) * (n - 2) / 2
    end

    for node_id in pairs(bc) do
	bc[node_id] = bc[node_id] / scale
    end

	self.betweenness_centrality = bc

end


function Graph:bfs(u,v)
    -- breadth-first search from node s to v
    local to_explore = queue()
    local explored = {}
    local parents = {}


    -- label root as explored
    explored[u] = true
    
    -- enqueue root
    to_explore:enqueue(u)

    while not to_explore:empty() do
	local w = to_explore:dequeue()

	if w == v then
	    local path = {}
	    local parent = w

	    while parent ~= u do
		table.insert(path, parent)
		parent = parents[parent]
	    end
	    table.insert(path, u)

	    return path
	end

	for w_adj in pairs(self.edge_lists[w][self.edge_list_key]) do
	    if not explored[w_adj] then
		explored[w_adj] = true
		parents[w_adj] = w
		to_explore:enqueue(w_adj)
	    end
	end
    end

end


-- + Sorted degrees, centrality measures +
-- Nice util function
function sort_table_by_values(t, descending)
    -- sort keys by values
    local keys = {}
    for key in pairs(t) do
        table.insert(keys, key)
    end
    table.sort(keys, function(a, b)
        if descending then
            return t[a] > t[b]
        else
            return t[a] < t[b]
        end
    end)
    return keys
end

function Graph:sorted_degrees(descending)
    return sort_table_by_values(self.degrees, descending)
end

function Graph:sorted_degree_centrality(descending)
    return sort_table_by_values(self.degree_centrality, descending)
end

function Graph:sorted_betweenness_centrality(descending)
    return sort_table_by_values(self.betweenness_centrality, descending)
end

-- Pretty print metrics
function Graph:list_nodes_by_metric(metric_table, metadata_key, descending)
    local sorted_metric = sort_table_by_values(metric_table, descending)
    print("Node ID", metadata_key, "Degree")
    if metadata_key then
	for _, node_id in pairs(sorted_metric) do
	    print(node_id, self.node_list[node_id][metadata_key], metric_table[node_id])
	end
    else
	for _, node_id in pairs(sorted_metric) do
	    print(node_id, metric_table[node_id])
	end
    end
end

function Graph:list_nodes_by_degree(metadata_key, descending)
    self:list_nodes_by_metric(self.degrees, metadata_key, descending)
end

function Graph:list_nodes_by_degree_centrality(metadata_key, descending)
    self:list_nodes_by_metric(self.degree_centrality, metadata_key, descending)
end

function Graph:list_nodes_by_betweenness_centrality(metadata_key, descending)
    self:list_nodes_by_metric(self.betweenness_centrality, metadata_key, descending)
end


return Graph
