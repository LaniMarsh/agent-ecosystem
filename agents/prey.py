import random
from mesa import Agent
from agents.grass import GrassPatch
from util import move_to_neighbor_avoiding_animals

class Prey(Agent):
    def __init__(self, model):
        super().__init__(model)
        self.energy = 100

    def move(self):
        nbrs = self.model.grid.get_neighborhood(self.pos, moore=True, include_center=False)
        self.model.grid.move_agent(self, random.choice(nbrs))

    def eat(self):
        cell_agents = self.model.grid.get_cell_list_contents([self.pos])
        grasses = [a for a in cell_agents if isinstance(a, GrassPatch)]
        if grasses and grasses[0].eat():
            self.energy += 10

    def breed(self):
        if self.energy >= 200:
            self.energy -= 100
            baby = Prey(self.model)
            self.model.grid.place_agent(baby, self.pos)
            move_to_neighbor_avoiding_animals(baby)  # avoid other animals, grass OK

    def step(self):
        self.move()
        self.eat()
        self.breed()
        self.energy -= 1
