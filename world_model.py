import random
from mesa import Model
from mesa.space import MultiGrid
from mesa.datacollection import DataCollector

# Solara viz
from mesa.visualization import SolaraViz, SpaceRenderer, make_plot_component
from mesa.visualization.components import AgentPortrayalStyle

from agents.grass import GrassPatch
from agents.prey import Prey
from agents.predator import Predator
from util import place_agent_avoiding_animals

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

        for _ in range(prey_count):
            prey = Prey(self)
            place_agent_avoiding_animals(self, prey)

        for _ in range(predator_count):
            predator = Predator(self)
            place_agent_avoiding_animals(self, predator)

        def _count(model, T):
            return sum(isinstance(a, T) for a in model.agents)

        def _grown_grass(model):
            return sum(isinstance(a, GrassPatch) and a.grown for a in model.agents)

        self.datacollector = DataCollector(
            model_reporters={
                "Prey":       lambda m: _count(m, Prey),
                "Predator":   lambda m: _count(m, Predator),
                "GrownGrass": _grown_grass,
            }
        )
        self.datacollector.collect(self)

    def step(self):
        self.agents.shuffle_do("step")
        self.datacollector.collect(self)

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

# run with: python -m solara run world_model.py
model = PreyPredatorModel(height=10, width=10, prey_count=10, predator_count=1)
renderer = SpaceRenderer(model=model, backend="matplotlib").render(agent_portrayal=agent_portrayal)

# add plots on page 1
PreyPlot   = make_plot_component("Prey", page=1)
PredPlot   = make_plot_component("Predator", page=1)
GrassPlot  = make_plot_component("GrownGrass", page=1)

page = SolaraViz(
    model,
    renderer,
    components=[PreyPlot, PredPlot, GrassPlot],
    model_params={
        "height": 10,
        "width": 10,
        "prey_count":     {"type": "SliderInt", "value": 10, "label": "Prey",      "min": 0, "max": 200, "step": 1},
        "predator_count": {"type": "SliderInt", "value": 1,  "label": "Predators", "min": 0, "max": 50,  "step": 1},
    },
    name="Predator–Prey–Grass",
)
