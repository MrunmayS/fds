import csv, math, json, random

from libpgm.graphskeleton import GraphSkeleton
from libpgm.nodedata import NodeData
from libpgm.discretebayesiannetwork import DiscreteBayesianNetwork
from libpgm.pgmlearner import PGMLearner
from libpgm.tablecpdfactorization import TableCPDFactorization


# Extracting the edges from data
def create_nodes_from_header(filename):
    csv_file = open(filename, 'r')
    reader = csv.reader(csv_file)
    x = next(reader)
    '''x = x[0].split(";")
    for i in range(len(x)):
        x[i] = x[i].replace('"', "")'''
    csv_file.close()
    return x


# Creating observations from data
def create_observations_from_csv(filename, fieldnames):
    observations = []
    csv_file = open(filename)
    reader = csv.DictReader(csv_file, fieldnames=fieldnames)
    next(reader)
    for row in reader:
        observation = dict()
        for node in nodes:
            observation[node] = row[node]
        observations.append(observation)
    return observations


# Making a tree from the nodes
def create_graph_skeleton(nodes, edges):
    graphSkeleton = GraphSkeleton()
    graphSkeleton.V = nodes
    graphSkeleton.E = edges
    graphSkeleton.toporder()
    return graphSkeleton

# Creating a Bayesian Network
def pristine_bn(V, E, Vdata):
    fresh_bn = DiscreteBayesianNetwork()
    fresh_bn.V = list(V)
    fresh_bn.E = list(E)
    fresh_bn.Vdata = Vdata.copy()
    return fresh_bn

# Find the cheapest edge that connects a node in the tree to a node not in the tree.
def pristine_fn(V, E, Vdata):
    pristine = pristine_bn(V, E, Vdata)
    return TableCPDFactorization(pristine)


# Calculate the edge information between two nodes.
def manual_mutual_information(node_a, node_b, observations, Vdata):
    node_a_values = Vdata[node_a]['vals']
    node_b_values = Vdata[node_b]['vals']

    running_sum = 0

    for a in node_a_values:
        marginal_a_dictionary = {}
        marginal_a_dictionary[node_a] = a
        marginal_a = count_matching_observations(marginal_a_dictionary, observations) / float(len(observations))

        for b in node_b_values:

            joint_query_dictionary = {}
            joint_query_dictionary[node_a] = a
            joint_query_dictionary[node_b] = b
            matching_joint_observations = count_matching_observations(joint_query_dictionary, observations)
            joint = count_matching_observations(joint_query_dictionary, observations) / float(len(observations))

            marginal_b_dictionary = {}
            marginal_b_dictionary[node_b] = b
            marginal_b = count_matching_observations(marginal_b_dictionary, observations) / float(len(observations))

            if joint > 0.0:
                running_sum += joint * math.log(joint / (marginal_a * marginal_b), 2)

    return running_sum



def count_matching_observations(match_dict, observations):
    matches = 0
    for o in observations:
        match = True
        for key in match_dict.keys():
            if o[key] != match_dict[key]:
                match = False
                break
        if match:
            matches += 1
    return matches


# saving the extracted edge information into a dictionary
def save_mutual_information(nodes, observations, Vdata):
    edges_for_tree = []
    nodes_for_tree = nodes[:]

    for i in range(len(nodes_for_tree)):
        for j in range(i + 1, len(nodes_for_tree)):
            node_a = nodes_for_tree[i]
            node_b = nodes_for_tree[j]

            mi = manual_mutual_information(node_a, node_b, observations, bn.Vdata)
            edge = (node_a, node_b, mi)
            edges_for_tree.append(edge)

    dump_file = open('mushroom.json', 'w')
    json.dump(edges_for_tree, dump_file)
    dump_file.close()

def load_mutual_information():
    dump_file = open('mushroom.json', 'r')
    return json.load(dump_file)


# Finding directed edges for the tree
def edges_for_maximum_spanning_tree(nodes, all_edges):
    added_nodes = []
    remaining_nodes = nodes[:]
    available_edges = all_edges[:]
    selected_edges = []

    # Select a random starting node.
    # print(remaining_nodes)
    start_node = random.choice(remaining_nodes)
    remaining_nodes.remove(start_node)
    added_nodes.append(start_node)

    # Make all edge costs the negative of their original cost.
    available_edges = [[edge[0], edge[1], -edge[2]] for edge in available_edges]

    while len(remaining_nodes):
        next_edge = cheapest_tree_non_tree_edge(added_nodes, remaining_nodes, available_edges)
        selected_edges.append(next_edge)
        available_edges.remove(next_edge)

        if next_edge[0] in remaining_nodes:
            remaining_nodes.remove(next_edge[0])
            added_nodes.append(next_edge[0])

        if next_edge[1] in remaining_nodes:
            remaining_nodes.remove(next_edge[1])
            added_nodes.append(next_edge[1])

    directed_edges = assign_edge_directions(added_nodes, selected_edges)

    return directed_edges



def cheapest_tree_non_tree_edge(nodes_in_tree, nodes_not_in_tree, available_edges):
    valid_edges = []
    for edge in available_edges:
        if (edge[0] in nodes_in_tree and edge[1] in nodes_not_in_tree) or (edge[1] in nodes_in_tree and edge[0] in nodes_not_in_tree):
            valid_edges.append(edge)
    edge_costs = [edge[2] for edge in valid_edges]

    cheapest_edge = None
    cheapest_cost = float("inf")
    for edge in valid_edges:
        if edge[2] < cheapest_cost:
            cheapest_edge = edge
            cheapest_cost = edge[2]

    return cheapest_edge


# Assigning the direction of the edges
def assign_edge_directions(nodes, edges):
    all_edges = edges[:]
    
    visited_nodes = []
    make_parent = []
    # Start with a random node.
    root = random.choice(nodes)
    make_parent.append(root)
    while len(make_parent) > 0:
        visiting = make_parent[0]
        make_parent = make_parent[1:]
        visited_nodes.append(visiting)
        for i in range(len(all_edges)):
            if all_edges[i][1] == visiting and all_edges[i][0] not in visited_nodes:
                all_edges[i][0], all_edges[i][1] = all_edges[i][1], all_edges[i][0]
            if all_edges[i][0] == visiting and all_edges[i][1] not in make_parent:
                make_parent.append(all_edges[i][1])

    return all_edges


def remove_weights_from_edges(edges):
    removing_weights = edges[:]
    return [[edge[0], edge[1]] for edge in removing_weights]

def train_model(skeleton, observations):
    learner = PGMLearner()
    bn = learner.discrete_mle_estimateparams(skeleton, observations)
    return bn.V, bn.E, bn.Vdata

def test_model(observations, V, E, Vdata):
    correct = 0
    for observation in observations:
        map_class = classify_observation(observation, V, E, Vdata)
        if map_class == observation['poisonous']:
            correct += 1

    return correct, len(observations)

def classify_observation(observation, V, E, Vdata):
    o = observation.copy()
    remove_missing_data(o)
    remove_untrained_values(o, Vdata)

    if 'poisonous' not in o.keys():
        return None

    actual_class = o['poisonous']
    del o['poisonous']

    map_class = None
    map_prob = -1
    try:
        for value in Vdata['poisonous']['vals']:
            query = dict(poisonous=value)
            evidence = dict(o)
            factorization = pristine_fn(V, E, Vdata)
            result = factorization.specificquery(query, evidence)
            if result > map_prob:
                map_class = value
                map_prob = result
        return map_class
    except:
        return None

def remove_missing_data(observation):
    for key in observation.copy().keys():
        if observation[key] == '?':
            del observation[key]

def remove_untrained_values(observation, learned_Vdata):
    for key in observation.copy().keys():
        observation_value = observation[key]
        known_values = learned_Vdata[key]['vals']
        if observation_value not in known_values:
            del observation[key]

def k_fold_indices(k, n):
    testing_size = n / k
    training_size = n - testing_size

    validation_sets = []
    all_indices = range(n)    
    for i in range(k):
        training_indices = list(all_indices)
        index = int(testing_size * i)
        
        x = range(index,index + int(testing_size))
        testing_indices = []
        for a in x:
            testing_indices.append(int(a))
        for j in testing_indices:
            training_indices.remove(j)
        validation_sets.append([training_indices, testing_indices])
    return validation_sets

def run_cross_validation(k, observations, graphSkeleton):
    cv_indices = k_fold_indices(k, len(observations))

    print('Performing {0}-fold cross validation.'.format(k))

    accuracies = []

    for i in range(len(cv_indices)):
        print('\tRunning iteration {0}.'.format(i + 1))
        testing = [observations[j] for j in cv_indices[i][1]]
        training = [observations[j] for j in cv_indices[i][0]]

        learned_V, learned_E, learned_Vdata = train_model(graphSkeleton, training)

        correct, n = test_model(testing, learned_V, learned_E, learned_Vdata)
        accuracy = correct/float(n)
        accuracies.append(accuracy)

        print('\t\tAccuracy: {0}'.format(accuracy))

    print('\tWeighted accuracy: {0}'.format(sum(accuracies)/len(accuracies)))

data_file_path = 'mushroom.csv'

# Creating Nodes
nodes = create_nodes_from_header(data_file_path)
edges = [] # Starting with 0 edges
print(nodes)

# Creating observations dictornary from data file
observations = create_observations_from_csv(data_file_path, nodes)

# Creating graph skeleton with 0 edge information
graphSkeleton = create_graph_skeleton(nodes, edges)

# Using MLP. we create a bayesian network
bn = PGMLearner().discrete_mle_estimateparams(graphSkeleton, observations)
save_mutual_information(nodes[1:], observations, bn.Vdata)
edges_with_weights = load_mutual_information() # strip unnecessary weights from edges.
final_edges = edges_for_maximum_spanning_tree(nodes[1:], edges_with_weights)
edges = remove_weights_from_edges(final_edges)
for i in range(1, len(nodes)): # adding one more edge
    edges.append([nodes[0], nodes[i]]) 

graphSkeleton = create_graph_skeleton(nodes, edges) # Creating graph skeleton with edge information
run_cross_validation(10, observations, graphSkeleton) # Running cross validation