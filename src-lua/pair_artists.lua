local comp_pairs = require "pair_comps"
local comps = require "read_competitions"
local Graph = require "graphx"

local comp_graph = Graph:new()
comp_graph.node_list = comps
comp_graph.edge_lists = comp_pairs


-- repeated code, oh well.
-- Source - https://stackoverflow.com/a/7615129
-- Posted by user973713, modified by community. See post 'Timeline' for change history
-- Retrieved 2026-07-16, License - CC BY-SA 4.0
function mysplit(inputstr, sep)

    if inputstr == nil then
	return nil
    end

    if sep == nil then
	sep = "%s"
    end
    local t = {}
    for str in string.gmatch(inputstr, "([^"..sep.."]+)") do
	table.insert(t, str)
    end
    return t
end

-- For each competition c:
-- -- For each participating artist c_artist
-- -- -- extract the artist and store in table
-- -- For each adjacent competition c_adj:
-- -- -- For each participating artist c_adj_artist
-- -- -- -- insert an edge between c_artist and c_adj_artist. 
-- -- -- -- If edge exists, append to out_artist_name's metadata the competition ID

local artist_node_list = {}
local artist_edge_lists = {}

local edge_list_keys = {jugement_pairs=true, listing_pairs=true}

for node_id, edge_lists in pairs(comp_graph.edge_lists) do 
    for edge_list_key, _ in pairs(edge_list_keys) do
	for out_node_id, shared_artist_names in pairs(edge_lists[edge_list_key]) do
	    -- print(node_id, out_node_id, shared_artist_names)
	    -- Add the names as nodes
	    for _,name in ipairs(shared_artist_names) do
		if not artist_node_list[name] then
		    artist_node_list[name] = true
		    artist_edge_lists[name] = {}
		end
		if not artist_edge_lists[name][edge_list_key] then
		    artist_edge_lists[name][edge_list_key] = {}
		end
	    end

	    -- Create edges between the nodes
	    for _,name in ipairs(shared_artist_names) do
		-- Add name as a node
		for _, inner_name in ipairs(shared_artist_names) do
		    if name ~= inner_name then
			artist_edge_lists[name][edge_list_key][inner_name] = {origin_comp_id=node_id, out_comp_id=out_node_id}
		    end
		end
	    end
	end
    end
end


local artist_graph = Graph:new{node_list=artist_node_list, edge_lists = artist_edge_lists, edge_list_key="jugement_pairs"}

return artist_graph
