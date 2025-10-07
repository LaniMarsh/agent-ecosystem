from mesa import Agent

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
