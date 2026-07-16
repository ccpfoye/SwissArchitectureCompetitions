local Graph = {
    node_list = {},
    edge_list = {}
}

function Graph:new(o)
    o = o or {}
    setmetatable(o, self)
    self.__index = self
    return o
end

return Graph
