artist_graph = require "pair_artists"

artist_graph.edge_list_key = "listing_pairs"

artist_graph:compute_degrees()
artist_graph:compute_degree_centrality()
artist_graph:compute_betweenness_centrality()

artist_graph:list_nodes_by_degree()
--artist_graph:list_nodes_by_degree_centrality()
--artist_graph:list_nodes_by_betweenness_centrality()
