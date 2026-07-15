local csv = require "csv"
local actor_lookup = require "actor_name_lookup"

-- Load competitions into competition object table:
-- Field Name		Description
-- -------------------------------------------------------
-- canonical_name	name of the competition in the file
-- normalized_name	Name of competition and listing, lower-cased and removed extra things Frey used to deliniate comps and jugements
-- jugement_names	Names of the listings of the jugements for this competition listing
-- listing_names	Names of the competition listings
-- slug			slugified name of the competition
--
-- competition_id	Unique id (integer) for each competition.
--
-- has_jugement		Does this listing have a corresponding judgement?
--
-- auteurs_listing	Names of jury in the original competition listing
-- roles_listing	Roles of the *jury* in the original competition listing
-- auteurs_jugement	Names of the competing architects / artists listed in the jugements
-- roles_jugement	The awards/prizes given to the artists listed in the jugement
--
-- date_debut_listing	Date string (day.month.year) of the beginning of the listing.
-- date_fin_listing	Final date of the original listing.
-- date_debut_jugement	Date string of the date of the judgement
-- date_fin_jugement	Date string of end of jugement.
--
-- num_listings		Number of original competition listings. Usually 1.
-- num_jugements	Number of judgement listings (occassionally multiple rounds listed)
--
-- localite		Location (Town, Canton, etc.)
-- canton		Listed canton.
-- pays			Country (usually "Suisse")
--
-- dossiers		Files inside the ACM archive
-- pieces		Information in ACM archive objects?
-- notes_listing	Pierre Frey's notes in the original competition listing
-- notes_jugement	Pierre Frey's notes on the judgement of this listing
--
-- npa			Unclear
-- ouvert_a		To whom was this competition open to?
--
-- adresse_1		Unclear.
-- adresse_2		Unclear.
-- adresse_3		Unclear. Address somehow?
--
-- is_isolate		In a network of shared artists, is this isolated?

-- https://stackoverflow.com/questions/5525817/inline-conditions-in-lua-a-b-yes-no
function table_ternary ( table_check , F )
    if table_check then return table_check else return F end
end

local Competitions = {}

local competition_data = csv.open("../Data/competitions.csv", {header=true})

local name_fields = {auteurs_listing=true, auteurs_jugement=true}

for fields in competition_data:lines() do
    local new_competition_object = {}

    for i,v in pairs(fields) do

	if name_fields[i] then

	    local new_names = string.gsub(v, "[^;]+", function(name)
		local actor_name = actor_lookup:lookup_actor_name(name)
		if actor_name and actor_name ~= '' then
		    return actor_name
		end
	    end)
	    print(new_names)	    

	    new_competition_object[i] = new_names
	else
	    new_competition_object[i] = v
	end

    end

    Competitions[new_competition_object["competition_id"]] =  new_competition_object
end


return Competitions





