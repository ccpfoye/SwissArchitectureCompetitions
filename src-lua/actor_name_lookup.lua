local csv = require "csv"
local ActorLookup = {}
-- Read the actor CSV
--
-- Actor Name Object:
-- 	author_raw 	observed, raw name
-- 	norm		normalized name
-- 	actor_idx	idx in actors.csv, the ACM's list of actors. Might be off by ~2 ?
-- 	actor_name	Name in actors.csv. Display name.
-- 	actor_slug	slugified version of name
-- 	first_last	First and Last name version of name
-- 	match_type	If the match between the first-last normalized name and ACM actor name was "exact" or min "lev"enshtein distance
-- 	lev_dist	If the match was a levenshtein distance, the lev distance.


-- load CSV
local actor_names = csv.open("../Data/author_to_actor.csv", {header=true})

-- Load actor name objs
local actor_name_objs = {}

-- Assign actor name objects to a table
for fields in actor_names:lines() do
    local new_actor_name_object = {}
    for i, v in pairs(fields) do
	new_actor_name_object[i] = v
    end
    print("\n")
    actor_name_objs[new_actor_name_object["author_raw"]] = new_actor_name_object
end

-- Give ActorLookup the name table
ActorLookup["actor_name_table"] = actor_name_objs

-- ActorLookup actor lookup!
function ActorLookup:lookup_actor_name(actor_name_raw)
    if self.actor_name_table[actor_name_raw] then
	return self.actor_name_table[actor_name_raw].actor_slug
    else return nil end
end

return ActorLookup









