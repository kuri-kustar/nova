""" The MIT License (MIT)

    Copyright (c) 2015 Kyle Hollins Wray, University of Massachusetts

    Permission is hereby granted, free of charge, to any person obtaining a copy of
    this software and associated documentation files (the "Software"), to deal in
    the Software without restriction, including without limitation the rights to
    use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of
    the Software, and to permit persons to whom the Software is furnished to do so,
    subject to the following conditions:

    The above copyright notice and this permission notice shall be included in all
    copies or substantial portions of the Software.

    THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
    IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS
    FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR
    COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER
    IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN
    CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
"""

import os
import sys

import itertools as it

thisFilePath = os.path.dirname(os.path.realpath(__file__))

sys.path.append(os.path.join(thisFilePath, "..", "..", "..", "python"))
from nova.mdp import *
from nova.pomdp import *


trials = [
         {'name': "VI CPU", 'filename': "domains/grid_world_mdp.raw", 'filetype': "raw", 'algorithm': "vi", 'process': "cpu", 'w': 4, 'h': 3},
         {'name': "VI GPU", 'filename': "domains/grid_world_mdp.raw", 'filetype': "raw", 'algorithm': "vi", 'process': "gpu", 'w': 4, 'h': 3},
         {'name': "LAO* CPU", 'filename': "domains/grid_world_ssp.raw", 'filetype': "raw", 'algorithm': "lao*", 'process': "cpu", 'w': 4, 'h': 3},
         {'name': "RTDP CPU", 'filename': "domains/grid_world_ssp.raw", 'filetype': "raw", 'algorithm': "rtdp", 'process': "cpu", 'w': 4, 'h': 3},

         {'name': "VI CPU (Intense)", 'filename': "domains/another_grid_world_mdp.raw", 'filetype': "raw", 'algorithm': "vi", 'process': "cpu", 'w': 10, 'h': 10},
         {'name': "VI GPU (Intense)", 'filename': "domains/another_grid_world_mdp.raw", 'filetype': "raw", 'algorithm': "vi", 'process': "gpu", 'w': 10, 'h': 10},
         {'name': "LAO* CPU (Intense)", 'filename': "domains/another_grid_world_ssp.raw", 'filetype': "raw", 'algorithm': "lao*", 'process': "cpu", 'w': 10, 'h': 10},
         {'name': "RTDP CPU (Intense)", 'filename': "domains/another_grid_world_ssp.raw", 'filetype': "raw", 'algorithm': "rtdp", 'process': "cpu", 'w': 10, 'h': 10},

         #{'name': "VI CPU (Intense)", 'filename': "domains/intense_grid_world_mdp.raw", 'filetype': "raw", 'algorithm': "vi", 'process': "cpu", 'w': 50, 'h': 50},
         #{'name': "VI GPU (Intense)", 'filename': "domains/intense_grid_world_mdp.raw", 'filetype': "raw", 'algorithm': "vi", 'process': "gpu", 'w': 50, 'h': 50},
         #{'name': "LAO* CPU (Intense)", 'filename': "domains/intense_grid_world_ssp.raw", 'filetype': "raw", 'algorithm': "lao*", 'process': "cpu", 'w': 50, 'h': 50},
         #{'name': "RTDP CPU (Intense)", 'filename': "domains/intense_grid_world_ssp.raw", 'filetype': "raw", 'algorithm': "rtdp", 'process': "cpu", 'w': 50, 'h': 50},

         #{'name': "VI CPU (Massive)", 'filename': "domains/massive_grid_world_mdp.raw", 'filetype': "raw", 'algorithm': "vi", 'process': "cpu", 'w': 75, 'h': 75},
         #{'name': "VI GPU (Massive)", 'filename': "domains/massive_grid_world_mdp.raw", 'filetype': "raw", 'algorithm': "vi", 'process': "gpu", 'w': 75, 'h': 75},
         #{'name': "LAO* CPU (Massive)", 'filename': "domains/massive_grid_world_ssp.raw", 'filetype': "raw", 'algorithm': "lao*", 'process': "cpu", 'w': 75, 'h': 75},
         ]


for trial in trials:
    print(trial['name'])

    gridWorldFile = os.path.join(thisFilePath, trial['filename'])
    gridWorld = MDP()
    gridWorld.load(gridWorldFile, filetype=trial['filetype'])

    if trial['algorithm'] == "vi":
        gridWorld.horizon = 10000
    elif trial['algorithm'] == "lao*":
        gridWorld.horizon = 1000000
    elif trial['algorithm'] == "rtdp":
        gridWorld.horizon = 10000

    # The heuristic (admissible) is the manhattan distance to the goal, which is always the upper right corner.
    #h = np.array([abs(y) + abs(trial['w'] - 1 - x) for y, x in it.product(range(trial['h']), range(trial['w']))] + [0.0]).flatten()
    h = np.array([0.0 for s in range(gridWorld.n)])

    policy, timing = gridWorld.solve(algorithm=trial['algorithm'], process=trial['process'], heuristic=h)

    prettyActions = ["L", "U", "R", "D"]

    if policy.r == 0:
        for y in range(trial['h']):
            for x in range(trial['w']):
                print(prettyActions[policy.pi[y * trial['w'] + x]] + " ", end='')
            print()
    else:
        S = [policy.S[i] for i in range(policy.r)]
        for y in range(trial['h']):
            for x in range(trial['w']):
                try:
                    i = S.index(y * trial['w'] + x)
                    print(prettyActions[policy.pi[i]] + " ", end='')
                except ValueError:
                    print("  ", end='')
            print()


