from agents.grass import GrassPatch

PLACEHOLDER_POS = (0, 0)

def cell_has_animals(model, pos):
    contents = model.grid.get_cell_list_contents([pos])
    return any(not isinstance(a, GrassPatch) for a in contents)

def cells_without_animals(model):
    coords = []
    for x in range(model.width):
        for y in range(model.height):
            pos = (x, y)
            if not cell_has_animals(model, pos):
                coords.append(pos)
    return coords

def place_agent_avoiding_animals(model, agent):
    candidates = cells_without_animals(model)
    if candidates:
        dest = model.random.choice(candidates)
    else:
        dest = (model.random.randrange(model.width), model.random.randrange(model.height))
    model.grid.place_agent(agent, dest)

def move_to_neighbor_avoiding_animals(agent):
    grid = agent.model.grid
    neighbors = grid.get_neighborhood(agent.pos, moore=True, include_center=False)
    safe = [p for p in neighbors if not cell_has_animals(agent.model, p)]
    grid.move_agent(agent, agent.model.random.choice(safe if safe else neighbors))
