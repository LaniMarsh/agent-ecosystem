import random
from mesa import Agent
from agents.prey import Prey
from util import move_to_neighbor_avoiding_animals

class Predator(Agent):
    def __init__(self, model):
        super().__init__(model)
        self.energy = 100

    def move(self):
        nbrs = self.model.grid.get_neighborhood(self.pos, moore=True, include_center=False)
        self.model.grid.move_agent(self, random.choice(nbrs))

    def eat(self):
        cell_agents = self.model.grid.get_cell_list_contents([self.pos])
        prey_agents = [a for a in cell_agents if isinstance(a, Prey)]
        if prey_agents:
            meal = random.choice(prey_agents)
            self.model.grid.remove_agent(meal)
            if hasattr(meal, "remove"):
                meal.remove()
            self.energy += 100

    def breed(self):
        if self.energy >= 200:
            self.energy -= 100
            baby = Predator(self.model)
            self.model.grid.place_agent(baby, self.pos)
            move_to_neighbor_avoiding_animals(baby)

    def step(self):
        self.move()
        self.eat()
        self.breed()
        self.energy -= 1
