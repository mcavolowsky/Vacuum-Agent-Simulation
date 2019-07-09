'''
This is hosted on github.

This is heavily based on the example from Artificial Intelligence: A Modern Approach located here:
http://aima.cs.berkeley.edu/python/agents.html
http://aima.cs.berkeley.edu/python/agents.py
'''

import inspect
from utils import *
import random, copy

# import my files
#import agents as ag
from agents import *
from objects import *
from display import *

'''Implement Agents and Environments (Chapters 1-2).

The class hierarchies are as follows:

Object ## A physical object that can exist in an environment
    Agent
        Wumpus
        RandomAgent
        ReflexVacuumAgent
        ...
    Dirt
    Wall
    ...

Environment ## An environment holds objects, runs simulations
    XYEnvironment
        VacuumEnvironment
        WumpusEnvironment

EnvFrame ## A graphical representation of the Environment

'''







class Environment:
    """
    Abstract class representing an Environment.  'Real' Environment classes inherit from this. Your Environment will
    typically need to implement:
        percept:           Define the percept that an agent sees.
        execute_action:    Define the effects of executing an action.
                           Also update the agent.performance slot.
    The environment keeps a list of .objects and .agents (which is a subset of .objects). Each agent has a .performance
    slot, initialized to 0.  Each object has a .location slot, even though some environments may not need this.
    """

    def __init__(self,):
        self.objects = []; self.agents = []

    # Mark: What does this do?  It isn't checked in the Environment class's add_object.
    object_classes = [] ## List of classes that can go into environment

    def percept(self, agent):
	    # Return the percept that the agent sees at this point. Override this.
        # Mark: Updated the code to use best practices on NotImplementedError over abstract
        raise NotImplementedError

    def execute_action(self, agent, action):
        "Change the world to reflect this action. Override this."
        raise NotImplementedError

    def default_location(self, obj):
        return None # Default location to place a new object with unspecified location.

    def exogenous_change(self):
	    "If there is spontaneous change in the world, override this."
	    pass

    def is_done(self):
        "By default, we're done when we can't find a live agent."
        for agent in self.agents:
            if agent.is_alive(): return False
        return True

    def step(self):
        '''Run the environment for one time step. If the
        actions and exogenous changes are independent, this method will
        do.  If there are interactions between them, you'll need to
        override this method.'''
        if not self.is_done():
            # for each agent
            # run agent.program with the agent's preception as an input
            # agent's perception = Env.precept(agent)
            actions = [agent.program(self.percept(agent))
                       for agent in self.agents]

            # for each agent-action pair, have the environment process the actions
            for (agent, action) in zip(self.agents, actions):
                self.execute_action(agent, action)

            # process any external events
            self.exogenous_change()

    def run(self, steps=1000):
	    for step in range(steps): # Run the Environment for given number of time steps.
                if self.is_done(): return
                self.step()

    def add_object(self, obj, location=None):
        '''Add an object to the environment, setting its location. Also keep track of objects that are agents.
        Shouldn't need to override this.'''
        obj.location = location or self.default_location(obj)
        # Mark: ^^ unsure about this line, lazy evaluation means it will only process if location=None?
        self.objects.append(obj)
        if isinstance(obj, Agent):
            obj.performance = 0
            self.agents.append(obj)
        return obj


class XYEnvironment(Environment):
    '''This class is for environments on a 2D plane, with locations
    labelled by (x, y) points, either discrete or continuous.  Agents
    perceive objects within a radius.  Each agent in the environment
    has a .location slot which should be a location such as (0, 1),
    and a .holding slot, which should be a list of objects that are
    held '''

    #robot_images = {(1,0):'img/robot-right.gif',(-1,0):'img/robot-left.gif',(0,-1):'img/robot-up.gif',(0,1):'img/robot-down.gif'}

    def __init__(self, width=10, height=10):
        update(self, objects=[], agents=[], width=width, height=height)

    def objects_at(self, location):
        "Return all objects exactly at a given location."
        return [obj for obj in self.objects if obj.location == location]

    def objects_near(self, location, radius):
        "Return all objects within radius of location."
        radius2 = radius * radius
        return [obj for obj in self.objects
                if distance2(location, obj.location) <= radius2]

    def percept(self, agent):
        "By default, agent perceives objects within radius r."
        return [self.object_percept(obj, agent)
                for obj in self.objects_near(agent)]

    def execute_action(self, agent, action):
        if action == 'TurnRight':
            agent.heading = self.turn_heading(agent.heading, -1)
        elif action == 'TurnLeft':
            agent.heading = self.turn_heading(agent.heading, +1)
        elif action == 'Forward':
            self.move_to(agent, vector_add(agent.heading, agent.location))
        elif action == 'Grab':
            objs = [obj for obj in self.objects_at(agent.location)
                if (obj != agent and obj.is_grabbable(agent))]
            if objs:
                agent.holding.append(objs)
                for o in objs:
                    o.location = agent

        elif action == 'Release':
            if agent.holding:
                agent.holding.pop()
        agent.bump = False

    def object_percept(self, obj, agent): #??? Should go to object?
        "Return the percept for this object."
        return obj.__class__.__name__

    def default_location(self, obj):
        return (random.choice(self.width), random.choice(self.height))

    def move_to(self, obj, destination):
        "Move an object to a new location."

        obstacles = [os for os in self.objects_at(destination) if os.blocker]
        if not obstacles:
            obj.location = destination


    def add_object(self, obj, location=(1, 1)):
        Environment.add_object(self, obj, location)
        obj.holding = []
        obj.held = None
        return obj

    def add_agent(self, agent, location=(1,1)):
        agent.bump = False
        self.add_object(agent, location)
        return agent

    def add_walls(self):
        "Put walls around the entire perimeter of the grid."
        for x in range(self.width):
            self.add_object(Wall(), (x, 0))
            self.add_object(Wall(), (x, self.height-1))
        for y in range(self.height):
            self.add_object(Wall(), (0, y))
            self.add_object(Wall(), (self.width-1, y))

    def turn_heading(self, heading, inc,
                 headings=[(1, 0), (0, 1), (-1, 0), (0, -1)]):
        "Return the heading to the left (inc=+1) or right (inc=-1) in headings."
        return headings[(headings.index(heading) + inc) % len(headings)]

#______________________________________________________________________________
## Vacuum environment

class VacuumEnvironment(XYEnvironment):
    '''The environment of [Ex. 2.12]. Agent perceives dirty or clean,
    and bump (into obstacle) or not; 2D discrete world of unknown size;
    performance measure is 100 for each dirt cleaned, and -1 for
    each turn taken.'''
    def __init__(self, width=10, height=10):
        XYEnvironment.__init__(self, width, height)
        self.add_walls()

    object_classes = []

    def percept(self, agent):
        '''The percept is a tuple of ('Dirty' or 'Clean', 'Bump' or 'None').
        Unlike the TrivialVacuumEnvironment, location is NOT perceived.'''
        status =  if_(self.find_at(Dirt, agent.location), 'Dirty', 'Clean')
        bump = if_(agent.bump, 'Bump', 'None')
        return (status, bump)

    def execute_action(self, agent, action):
        if action == 'Suck':
            if self.find_at(Dirt, agent.location):
                agent.performance += 100
        agent.performance -= 1
        XYEnvironment.execute_action(self, agent, action)

    def find_at(self, cls, loc):
        return [o for o in self.objects_at(loc) if isinstance(o, cls)]

    def exogenous_change(self):
        if random.uniform(0,1)<.9:
            loc = (random.randrange(self.width), random.randrange(self.height))
            if not (self.find_at(Dirt, loc) or self.find_at(Wall, loc)):
                self.add_object(Dirt(), loc)

#______________________________________________________________________________

def compare_agents(EnvFactory, AgentFactories, n=10, steps=1000):
    '''See how well each of several agents do in n instances of an environment.
    Pass in a factory (constructor) for environments, and several for agents.
    Create n instances of the environment, and run each agent in copies of
    each one for steps. Return a list of (agent, average-score) tuples.'''
    envs = [EnvFactory() for i in range(n)]
    return [(A, test_agent(A, steps, copy.deepcopy(envs)))
            for A in AgentFactories]

def test_agent(AgentFactory, steps, envs):
    "Return the mean score of running an agent in each of the envs, for steps"
    total = 0
    for env in envs:
        agent = AgentFactory()
        env.add_object(agent)
        env.run(steps)
        total += agent.performance
    return float(total)/len(envs)

#______________________________________________________________________________

def test1():

    e = VacuumEnvironment()
    ef = EnvFrame(e)
    for i in range(1,9):
        e.add_agent(DisplayObject(TraceAgent(NewRandomReflexAgent())),location=(i,i))
    ef.update_display()

    if False:
        for x in range(1,9):
            for y in range(1,9):
                e.add_object(Dirt(),location=(x,y))


    ef.run()
    ef.mainloop()

test1()