from mesa import Agent, Model
from mesa.space import MultiGrid
from mesa.visualization import SolaraViz, SpaceRenderer, make_plot_component
from mesa.visualization.components import AgentPortrayalStyle
from mesa.datacollection import DataCollector
import random

PLACEHOLDER_POS = (0, 0)


class AgentCounter():
    def __init__(self):
        pass

    def render(self, model):
        prey_count = sum(isinstance(agent, Prey) for agent in model.agents)
        predator_count = sum(isinstance(agent, Predator) for agent in model.agents)
        grass_count = sum(isinstance(agent, GrassPatch) for agent in model.agents)
        return f"Prey: {prey_count}, Predators: {predator_count}, GrassPatch: {grass_count}"


# Utilities
def _cell_has_types(model, pos, forbidden_types):
    contents = model.grid.get_cell_list_contents([pos])
    return any(isinstance(a, forbidden_types) for a in contents)

def _cells_without_types(model, forbidden_types):
    coords = []
    for x in range(model.width):
        for y in range(model.height):
            pos = (x, y)
            if not _cell_has_types(model, pos, forbidden_types):
                coords.append(pos)
    return coords

def place_agent_avoiding(model, agent, forbidden_types=(object,)):
    candidates = _cells_without_types(model, forbidden_types)
    if candidates:
        dest = model.random.choice(candidates)
    else:
        dest = (model.random.randrange(model.width), model.random.randrange(model.height))
    model.grid.place_agent(agent, dest)

def move_agent_random_avoiding(model, agent, forbidden_types=(object,)):
    candidates = _cells_without_types(model, forbidden_types)
    if candidates:
        dest = model.random.choice(candidates)
    else:
        dest = (model.random.randrange(model.width), model.random.randrange(model.height))
    model.grid.move_agent(agent, dest)

def move_to_neighbor_avoiding(agent, forbidden_types=(object,)):
    grid = agent.model.grid
    neighbors = grid.get_neighborhood(agent.pos, moore=True, include_center=False)
    safe = [p for p in neighbors if not _cell_has_types(agent.model, p, forbidden_types)]
    dest = agent.model.random.choice(safe if safe else neighbors)
    grid.move_agent(agent, dest)



class GrassPatch(Agent):
    def __init__(self, model, grown=True, regrow_time=20):
        super().__init__(model)
        self.grown = grown
        self.regrow_time_default = regrow_time
        self.regrow_timer = 0

    def step(self):
        if not self.grown:
            self.regrow_timer -= 1
            if self.regrow_timer <= 0:
                self.grown = True

    def eat(self):
        if self.grown:
            self.grown = False
            self.regrow_timer = self.regrow_time_default
            return True
        return False


class Prey(Agent):
    def __init__(self, model):
        super().__init__(model)
        self.energy = 100

    def move(self):
        possible_steps = self.model.grid.get_neighborhood(
            self.pos, moore=True, include_center=False
        )
        new_position = random.choice(possible_steps)
        self.model.grid.move_agent(self, new_position)

    def eat(self):
        cell_agents = self.model.grid.get_cell_list_contents([self.pos])
        grasses = [a for a in cell_agents if isinstance(a, GrassPatch)]
        if grasses:
            if grasses[0].eat():
                self.energy += 10

    def breed(self):
        if self.energy >= 200:
            self.energy -= 100
            baby = Prey(self.model)
            self.model.grid.place_agent(baby, self.pos)
            move_to_neighbor_avoiding(baby, forbidden_types=(Prey, Predator))
            print("new prey")

    def step(self):
        self.move()
        self.eat()
        self.breed()
        self.energy -= 1


class Predator(Agent):
    def __init__(self, model):
        super().__init__(model)
        self.energy = 100

    def move(self):
        possible_steps = self.model.grid.get_neighborhood(
            self.pos, moore=True, include_center=False
        )
        new_position = random.choice(possible_steps)
        self.model.grid.move_agent(self, new_position)

    def eat(self):
        prey_neighbors = self.model.grid.get_cell_list_contents(
            [self.pos]
        )
        prey_agents = [agent for agent in prey_neighbors if isinstance(agent, Prey)]
        if prey_agents:
            prey_to_eat = random.choice(prey_agents)
            self.model.grid.remove_agent(prey_to_eat)
            prey_to_eat.remove()
            self.energy += 100

    def breed(self):
        if self.energy >= 200:
            self.energy -= 100
            baby = Predator(self.model)
            self.model.grid.place_agent(baby, self.pos)
            move_to_neighbor_avoiding(baby, forbidden_types=(Prey, Predator))
            print("new predator")

    def step(self):
        self.move()
        self.eat()
        self.breed()
        self.energy -= 1


class PreyPredatorModel(Model):
    def __init__(self, height, width, prey_count, predator_count):
        super().__init__()
        self.height = height
        self.width = width
        self.grid = MultiGrid(width, height, torus=True)
        self.running = True

        for x in range(self.width):
            for y in range(self.height):
                grass = GrassPatch(self, grown=(random.random() < 0.8), regrow_time=20)
                self.grid.place_agent(grass, (x, y))

        for i in range(prey_count):
            prey = Prey(self)
            place_agent_avoiding(self, prey, forbidden_types=(Prey, Predator))

        for i in range(predator_count):
            predator = Predator(self)
            place_agent_avoiding(self, predator, forbidden_types=(Prey, Predator))

        def _count(model, T):
            return sum(isinstance(a, T) for a in model.agents)

        def _grown_grass(model):
            return sum(isinstance(a, GrassPatch) and a.grown for a in model.agents)

        self.datacollector = DataCollector(
            model_reporters={
                "Prey": _count(self, Prey) if False else (lambda m: _count(m, Prey)),
                "Predator": lambda m: _count(m, Predator),
                "GrownGrass": _grown_grass,
            }
        )
        self.datacollector.collect(self)

    def step(self):
        self.agents.shuffle_do("step")
        self.datacollector.collect(self)

# for i in range(100):
#     model.step()
#
#     # Print population counts
#     prey_count = sum(isinstance(agent, Prey) for agent in model.agents)
#     predator_count = sum(isinstance(agent, Predator) for agent in model.agents)
#     grass_count = sum(isinstance(agent, GrassPatch) for agent in model.agents)
#     print(f"Step {i}: Prey={prey_count}, Predators={predator_count}, GrassPatch={grass_count}")

def agent_portrayal(agent):
    if isinstance(agent, GrassPatch):
        return AgentPortrayalStyle(
            color=("tab:green" if agent.grown else "tab:brown"),
            size=30,
            alpha=0.6,
        )
    if isinstance(agent, Prey):
        return AgentPortrayalStyle(
            color="tab:blue",
            size=60,
        )
    if isinstance(agent, Predator):
        return AgentPortrayalStyle(
            color="tab:red",
            size=80,
            marker="^",
        )
        # fallback
    return AgentPortrayalStyle(color="gray", size=40)

model = PreyPredatorModel(height=10, width=10, prey_count=10, predator_count=1)

renderer = SpaceRenderer(model=model, backend="matplotlib").render(
    agent_portrayal=agent_portrayal
)

PreyPlot  = make_plot_component("Prey", page=1)
PredPlot  = make_plot_component("Predator", page=1)
GrassPlot = make_plot_component("GrownGrass", page=1)

page = SolaraViz(
    model,
    renderer,
    components=[PreyPlot, PredPlot, GrassPlot],
    model_params={
        "height": 10,
        "width": 10,
        "prey_count":     {"type": "SliderInt", "value": 10, "label": "Prey",      "min": 0, "max": 20, "step": 1},
        "predator_count": {"type": "SliderInt", "value": 1,  "label": "Predators", "min": 0, "max": 10,  "step": 1},
    },
    name="Predator–Prey–Grass",
)