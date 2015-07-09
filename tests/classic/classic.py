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

thisFilePath = os.path.dirname(os.path.realpath(__file__))

sys.path.append(os.path.join(thisFilePath, "..", "..", "python"))
from nova.pomdp import *


files = [
        {'name': "Tiger", 'filename': "tiger_95.pomdp", 'filetype': "pomdp"},
        #{'name': "Grid (4x3)", 'filename': "4x3_95.pomdp", 'filetype': "pomdp"},
        #{'name': "Tiger Grid", 'filename': "tiger_grid.pomdp", 'filetype': "pomdp"},
        #{'name': "Tag", 'filename': "tag.pomdp", 'filetype': "pomdp"},
        #{'name': "AUV Navigation", 'filename': "auvNavigation.pomdp", 'filetype': "pomdp"},
        #{'name': "Rock Sample (7x8)", 'filename': "rockSample_7_8.pomdp", 'filetype': "pomdp"},
        ]

numBeliefSteps = 4
numTrials = 10

timings = {'cpu': [list() for j in range(numBeliefSteps)],
            'gpu': [list() for j in range(numBeliefSteps)]}

for f in files:
    print(f['name'])

    filename = os.path.join(thisFilePath, f['filename'])

    for i in range(numTrials):
        print("Trial %i of %i" % (i + 1, numTrials))

        for j in range(numBeliefSteps):
            print("Belief Step %i of %i" % (32 * (j + 1), (32 * (numBeliefSteps + 1))))

            for p in ['cpu', 'gpu']:
                pomdp = POMDP()
                pomdp.load(filename, filetype=f['filetype'])
                pomdp.expand(method='random', numDesiredBeliefPoints=(32 * (j + 1)))

                Gamma, piResult, timing = pomdp.solve(process=p)
                timings[p][j] += [timing]

    #print(pomdp)
    #print(Gamma)
    #print(piResult)
    #print(timing)

