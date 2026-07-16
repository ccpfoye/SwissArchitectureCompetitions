comps = require "read_competitions"

comp_pairs = {}

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

-- Extract shared pairs in jugements and listings
for comp_id, comp_metadata in pairs(comps) do
    -- What juges sat together?
    local listing_names = mysplit(comp_metadata.auteurs_listing, ";")
    local listing_comp_pairs = {}

    -- What artists competed together?
    local jugement_names = mysplit(comp_metadata.auteurs_jugement, ";")
    local jugement_comp_pairs = {}

    --print(comp_metadata.auteurs_listing)
    
    -- no jugement names or listing names for this comp: skip!
    if not jugement_names and not listing_names then goto continue end

    for comp_id_j, comp_metadata_j in pairs(comps) do
	-- no self-edges
	if comp_id == comp_id_j then
	    break
	end

	local shared_listing_names = {}
	local has_shared_listing_name = false

	local shared_jugement_names = {}
	local has_shared_jugement_name = false


	-- Extract shared names
	local listing_names_j = mysplit(comp_metadata_j.auteurs_listing, ";")
	local jugement_names_j = mysplit(comp_metadata_j.auteurs_jugement, ";")


	-- Check if listing names (jury members!) are shared
	if listing_names and listing_names_j then -- neither are empty

	    local lookup_listing_names = {}
	    for k, v in ipairs(listing_names_j) do
		lookup_listing_names[v] = true
	    end

	    for name_idx, listing_name in ipairs(listing_names) do
		if lookup_listing_names[listing_name] then
		    table.insert(shared_listing_names, listing_name)
		    has_shared_listing_name = true
		end
	    end
	end

	-- Check if jugement names (architects!) are shared
	if jugement_names and jugement_names_j then

	    local lookup_jugement_names = {}
	    for k, v in ipairs(jugement_names_j) do
		lookup_jugement_names[v] = true
	    end

	    for name_idx, jugement_name in ipairs(jugement_names) do
		if lookup_jugement_names[jugement_name] then
		    table.insert(shared_jugement_names, jugement_name)
		    has_shared_jugement_name = true
		end
	    end
	end


	-- If any shared jury members, save this
	if has_shared_listing_name then
	    listing_comp_pairs[comp_id_j] = shared_listing_names
	end

	-- If any shared artist members, save this.
	if has_shared_jugement_name then
	    jugement_comp_pairs[comp_id_j] = shared_jugement_names
	end

	comp_pairs[comp_id] = {listing_pairs = listing_comp_pairs, jugement_pairs = jugement_comp_pairs}
    end
    ::continue::
end

