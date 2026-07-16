local comp_pairs = require "pair_comps"
local comps = require "read_competitions"
local Graph = require "graphx"

comp_graph = Graph:new()

comp_graph.node_list = comps
comp_graph.edge_lists = comp_pairs

comp_graph.edge_list_key = "jugement_pairs"

-- Compute degree centrality
comp_graph:compute_degree_centrality()
comp_graph:compute_betweenness_centrality()

comp_graph:list_nodes_by_degree("canonical_name")

