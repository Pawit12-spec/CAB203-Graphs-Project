import graphs, digraphs, csv

## Optional imports
# import itertools
# import functools

def maxMinTransfers(fileName):
    # Read the CSV rows as tuples and store them in a set.
    with open(fileName) as f:
        R = {tuple(row) for row in csv.reader(f)}
    # V: set of all stations found in any row.
    V = {x for r in R for x in r}
    # E: undirected edges; each row’s first element is connected to every other item in that row.
    E = { (r[0], s) for r in R for s in r[1:] } | { (s, r[0]) for r in R for s in r[1:] }
    # "Stations" are those stations that are never in the first column.
    stations = V - { r[0] for r in R }
    # Generate all unordered pairs from th stations.
    P = { (a, b) for a in stations for b in stations if a < b }
    # For each pair, compute transfers as: max(0, (distance - 1)//2).
    max_transfers = max(
        (max(0, (graphs.distance(V, E, a, b) - 1) // 2)
         for (a, b) in P),
        default=0
    )
    return max_transfers
    

#print(maxMinTransfers('lines1.csv'))


def assignCrew(crew, timeslots):
    # Produce an ordered tuple of timeslots.
    ts = tuple(sorted(timeslots, key=lambda t: (t[1], t[2], t[0])))
    cl = set(crew)
    S, P = {'Morning': (4, 12), 'Day': (9, 17), 'Night': (16, 24)}, {(8, 10), (16, 18)}
    
    # Eligibility: p is eligible for position pos on timeslot t if:
    # - p has the required role,
    # - the timeslot is within p's shift bounds,
    # - if p has peak restrictions, t does not conflict with any peak block,
    # - and, for Drivers, if t requires ETCS then p must have it.
    eligible = lambda pos, p, t: (pos[1] in p[1] and S[p[3]][0] <= t[1] <= t[2] <= S[p[3]][1] and
                                  (not p[4] or all(not (t[1] < pe[1] and t[2] > pe[0]) for pe in P)) and
                                  (pos[1] != "Driver" or (not t[3] or p[2])))
    
    V = set(range(len(ts)))  # indices for the ordered timeslots
    A = {(i, role) for i in V for role in ("Driver", "Guard")}
    # B: set of crew members who are eligible for at least one timeslot.
    B = {p[0] for p in cl}
    # E: edges between timeslot-role pairs and crew members.
    E = {(pos, p[0]) for pos in A for p in cl if eligible(pos, p, ts[pos[0]])}
    
    # Check if the bipartite graph is perfect.
    # If not, return None.
    M = digraphs.maxMatching(A, B, E)
    fm = {pos: name for (pos, name) in M if pos in A}
    if len(fm) != len(A): return None 
    
    # Check if all timeslots have been assigned a Driver and a Guard.
    assign = {i: {"Driver": fm[(i, "Driver")], "Guard": fm[(i, "Guard")]} 
              for i in V if (i, "Driver") in fm and (i, "Guard") in fm}
    if len(assign) != len(V): return None

    return {f"{ts[i][0]}-{ts[i][1]}-{ts[i][2]}": (assign[i]["Driver"], assign[i]["Guard"]) for i in V}


def trainSchedule(timeslots):
 # Each timeslot t = (Line, start, end) is treated as occupying [start, end+1)
    # Two timeslots conflict if their occupancy intervals overlap.
    V = {i for i in range(len(timeslots))}
    E = {(i, j) for i in V for j in V 
         if i != j and timeslots[i][2] + 1 > timeslots[j][1] and timeslots[j][2] + 1 > timeslots[i][1]}
    # The minimum number of trains equals the chromatic number of this conflict graph.
    k, _ = graphs.minColouring(V, E)
    return k


def trackNetworkCapacity(trackNetwork, blockTimes, destination):
    # Recursively get edges from a segment (consecutive pairs)
    def segEdges(seg):
        return set() if len(seg) < 2 else {(seg[0], seg[1])} | segEdges(seg[1:])
    
    E_seg = set.union(*(segEdges(seg) for seg in trackNetwork))
    V = {v for seg in trackNetwork for v in seg}            # all vertices in segments
    S = {seg[0] for seg in trackNetwork}                      # outer sources
    supersrc = "supersrc"
    V |= {supersrc}                                           # add a supersource
    
    # Capacity on each block is 60 / (blockTime)
    cap = {e: 60 / blockTimes[e] for e in E_seg}
    big = sum(cap[e] for e in cap)                            # a high capacity for source edges
    E_sup = {(supersrc, s) for s in S}
    cap |= {e: big for e in E_sup}                            # supersource edges get capacity 'big'
    
    E_all = E_seg | E_sup
    f = digraphs.maxFlow(V, E_all, cap, supersrc, destination)
    return sum(f[e] for e in f if e[0] == supersrc)


# slots = [
#             # Line,  StartTime, EndTime
#             ('IPNA', 6, 9),
#             ('IPNA', 7, 10),
#             ('IPNA', 8, 11),
#             ('CASP', 7, 9),
#             ('CASP', 9, 11),
#             ('ABCD', 9, 12),
#             ('ABCD', 11, 14)
#         ]
# slots2 = [
#             # Line,  StartTime, EndTime
#             ('IPNA', 6, 9),
#             ('CASP', 11, 13),
#             ('ABCD', 9, 12)
#         ]
# # print("slot 1: ",trainSchedule(slots))
# # print("slot 2: ",trainSchedule(slots2))

# crew = {
#             # Driver,   Roles allowed        ETCS certified, shift,     peekTimeRestricted
#             ('Alice',   ('Guard', 'Driver'), True,           'Morning', False),
#             ('Bob',     ('Driver'),          False,          'Day',     True),
#             ('Charlie', ('Guard'),           True,           'Morning', False),
#             ('Denise',  ('Guard', 'Driver'), False,          'Day',     True),
#             ('Elaine',  ('Guard', 'Driver'), False,          'Night',   False),
#             ('Frank',   ('Guard', 'Driver'), True,           'Night',   False),
#         }

# slots = {
#             # Line,  StartTime, EndTime, ETCS required
#             ('IPNA', 6, 9, True),
#             ('CASP', 11, 13, False),
#             ('RPSP', 17, 19, True)
#         }

# #print("crew: ", assignCrew(crew, slots))

# trackNetwork = [
#             [ 1, 2, 3, 4, 99 ],
#         ]

# blockTimes = {
#             (1, 2): 2,
#             (2, 3): 2,
#             (3, 4): 3,
#             (4, 99): 1,
#         }
#print("trackNetwork: ", trackNetworkCapacity(trackNetwork, blockTimes, 99))