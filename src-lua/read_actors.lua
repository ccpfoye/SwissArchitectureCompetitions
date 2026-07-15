local csv = require "csv"
local f = csv.open("../Data/competitions.csv", {header=true})

for fields in f:lines() do
    for i, v in pairs(fields) do print(i,v) end
    print("\n")
end

