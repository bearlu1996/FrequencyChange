import os
from pm4py.objects.log.importer.xes import importer as xes_importer
from pm4py.algo.discovery.inductive import algorithm as inductive_miner
from pm4py.objects.petri.importer import importer as pnml_importer
from pm4py.visualization.petrinet import visualizer as pn_visualizer
from pm4py.algo.conformance.alignments import algorithm as alignments
import numpy as np
import matplotlib.pyplot as plt 
import ruptures as rpt
import datetime
from array import *

def getTime(elem):
    return elem[0]

#variant = xes_importer.Variants.ITERPARSE
#parameters = {variant.value.Parameters.TIMESTAMP_SORT: True}
net, initial_marking, final_marking = pnml_importer.apply("helpdesk.pnml")
log = xes_importer.apply(os.path.join("helpdesk.xes"))

target_place_id = "n5" #n5 refers to the place after "Take in charge ticket" 
transitions_before_place = set()
transitions_after_place = set()
transitions_before_place_id = set()
transitions_after_place_id = set()
transitions_after_labels = {}
places = net.places
transitions = net.transitions
arcs = net.arcs
counter = 1
for p in places:
    #print(p.name)
    if p.name == target_place_id:
        if len(p.out_arcs) == 1:
            print("The place you select is not an exclusive choice point, please try again.")
            quit()
        else:
            for arc in p.in_arcs:
                transitions_before_place.add(arc.source)
                transitions_before_place_id.add(arc.source.name)
            for arc in p.out_arcs:
                transitions_after_place.add(arc.target)
                transitions_after_place_id.add(arc.target.name)
                transitions_after_labels.update({arc.target.name: counter})
                counter = counter + 1
if len(transitions_after_place) == 0:
    print("The target place does not exist, please try again.")
    quit()

print("The place you selected is: " + target_place_id)
print("The input transitions are: ")
for t in transitions_before_place:
    if t.label == None:
        print("Transition id: " + t.name + ", Label: hidden")
    else:
        print("Transition id: " + t.name + ", Label: " + t.label)

print("The output transitions are: ")
for t in transitions_after_place:
    if t.label == None:
        print("Transition id: " + t.name + ", Label: hidden" + ", Choice: " + str(transitions_after_labels[t.name]))
    else:
        print("Transition id: " + t.name + ", Label: " + t.label + ", Choice: " + str(transitions_after_labels[t.name]))

parameters = {alignments.Parameters.PARAM_ALIGNMENT_RESULT_IS_SYNC_PROD_AWARE:"True"}
aligned_traces = alignments.apply_log(log, net, initial_marking, final_marking, parameters=parameters)

sequence = []
choice_sequence = np.array([[99],[100]])
choice_sequence_trace_index = {}
points_counter = 0
traces_counter = -1
for aligned_trace in aligned_traces:
    trace_move = -1
    traces_counter = traces_counter + 1
    find_before = False
    alignment = aligned_trace["alignment"]
    #print(alignment)
    for i in range (0, len(alignment)):
    #for i in range (0, 1):  
        if alignment[i][0][0] != ">>":
            trace_move = trace_move + 1
            #print(alignment[i][0][0])
            #print(trace_move)
        if alignment[i][0][1] == ">>":
            continue
        if alignment[i][0][1] in transitions_before_place_id:
            find_before = True
        if alignment[i][0][1] in transitions_after_place_id and find_before:
            t_name = alignment[i][0][1]
            value = transitions_after_labels[t_name]
            #choice_sequence = np.concatenate((choice_sequence, np.array([[value]])), axis=0)
            #choice_sequence_trace_index.update({points_counter: traces_counter})
            if alignment[i][0][0] != ">>":
                sequence.append([log[traces_counter][trace_move - 1]["time:timestamp"], value])
            else:
                sequence.append([log[traces_counter][trace_move]["time:timestamp"], value])
            
            points_counter = points_counter + 1
            find_before = False
sequence.sort(key=getTime)
#print(sequence)

for item in sequence:
    choice_sequence = np.concatenate((choice_sequence, np.array([[item[1]]])), axis=0)
choice_sequence = np.delete(choice_sequence, 0, axis = 0)
choice_sequence = np.delete(choice_sequence, 0, axis = 0)
c = rpt.costs.CostRbf()
##algo = rpt.Dynp(model="l2").fit(choice_sequence)
algo = rpt.Pelt(model="rbf", custom_cost=c).fit(choice_sequence)
result = algo.predict(pen = 5)
##print(test_sequence_1)
##print(choice_sequence[1][0])
##print(choice_sequence)
#
for i in range(0, len(result) - 1):
   print("Concept drift detected at point " + str(result[i]) + ", at trace " + str(sequence[result[i] - 1][0]))
#print()
#

#Prototype only, should modify the code below if using another model and log
A = 0
B = 0
C = 0

for i in range(0, result[0]):
    if choice_sequence[i][0] == 1:
        A = A + 1
    if choice_sequence[i][0] == 2:
        B = B + 1
    if choice_sequence[i][0] == 3:
        C = C + 1
   

total = result[0]
print(A/total)
print(B/total)
print(C/total)
print()

A = 0
B = 0
C = 0

for i in range(result[0], result[1]):
    if choice_sequence[i][0] == 1:
        A = A + 1
    if choice_sequence[i][0] == 2:
        B = B + 1
    if choice_sequence[i][0] == 3:
        C = C + 1
   

total = result[1] - result[0]
print(A/total)
print(B/total)
print(C/total)
print()

A = 0
B = 0
C = 0

for i in range(result[1], len(choice_sequence)):
    if choice_sequence[i][0] == 1:
        A = A + 1
    if choice_sequence[i][0] == 2:
        B = B + 1
    if choice_sequence[i][0] == 3:
        C = C + 1
    

total = len(choice_sequence) - result[1]
print(A/total)
print(B/total)
print(C/total)

print()


rpt.display(choice_sequence, result)
plt.show()