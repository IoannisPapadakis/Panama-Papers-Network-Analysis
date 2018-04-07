import networkx as nx
import community as cm
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
# %matplotlib inline

# https://www.occrp.org/en/panamapapers/database

def load_clean_data():
    '''
    GOAL: This function builds the edges and nodes from the ICIJ open source data base
    of the Panama Papers. These files are concatenated and used to build networkX.Pandas.DataFrame(F), combines all
    the nodes from the lists into one data frame, and performs some data cleaning.
    ----------------------------
    INPUT: None
    OUPUT:
    - 'F' is the NetworkX graph from Pandas DataFrame.
    - 'all_nodes', is the concatenation of all node lists into one dataframe
    '''
    # Read the edge list and convert it to network
    edges = pd.read_csv('/Users/rdelapp/Galvanize/DSI_g61/capstone/panama_papers/data/csv_panama_papers_2018-02-14/panama_papers_edges.csv')
    edges = edges[edges["TYPE"] != "registrated address"]
    F = nx.from_pandas_dataframe(edges, "START_ID", "END_ID") # Return a graph from Pandas DataFrame.

    # Read node lists
    officers       = pd.read_csv('/Users/rdelapp/Galvanize/DSI_g61/capstone/panama_papers/data/csv_panama_papers_2018-02-14/panama_papers_nodes_officer.csv', index_col = "node_id")
    intermediaries = pd.read_csv('/Users/rdelapp/Galvanize/DSI_g61/capstone/panama_papers/data/csv_panama_papers_2018-02-14/panama_papers_nodes_intermediary.csv', index_col = "node_id")
    entities       = pd.read_csv('/Users/rdelapp/Galvanize/DSI_g61/capstone/panama_papers/data/csv_panama_papers_2018-02-14/panama_papers_nodes_entity.csv', index_col = "node_id")
    # addresses      = pd.read_csv('/Users/rdelapp/Galvanize/DSI_g61/capstone/panama_papers/data/csv_panama_papers_2018-02-14/panama_papers_nodes_address.csv', index_col = "node_id")

    # Combine the node lists into one dataframe
    officers["type"] = "officer"
    intermediaries["type"] = "intermediary"
    entities["type"] = "entity"
    # addresses["type"] = "address"
    #Concatentate
    all_nodes = pd.concat([officers, intermediaries, entities])

    # Do some cleanup of names
    all_nodes["name"] = all_nodes["name"].str.upper().str.replace(' ','_')

    # Ensure that all "Bearers" do not become a single node
    all_nodes["name"].replace(
        to_replace = [r"MRS?\.\s+", r"\.", r"\s+", "LIMITED", "THE BEARER", "BEARER", "BEARER 1", "EL PORTADOR", "AL PORTADOR"],
        value = ["","", "", "LTD", np.nan, np.nan, np.nan, np.nan, np.nan],
        inplace = True, regex = True)

    # all_nodes['type'].dropna

    # clear NAN's
    # if "ISSUES OF:" in F:
    #     F.remove_node("ISSUES OF:")
    #
    # if "" in F:
    #     F.remove_node("")
    return F, all_nodes

def build_subgraph(F, all_nodes):
    '''
    GOAL: This function build the subgraph of the notes_of_interest, creates the graph,
    and then saves the figure.
    -------------------------------
    INPUT:
        - 'F' is the NetworkX graph from Pandas DataFrame.
        - 'all_nodes', is the concatenation of all node lists into one dataframe.
        - 'cc'... [edit]
    OUPUT:
        - 'ego' is a subgraph of the countries of interest.
    '''

    # We only want to look at Saudi Arabia and, maybe, Jordan
    # CCODES = ["SAU", "JOR"] # country code to be examined in subgraph
    # CCODES = "UZB", "TKM", "KAZ", "KGZ", "TJK"
    CCODES = "SAU", "JOR"
    #seeds = all_nodes[all_nodes["country_codes"] == 'SAU'].index
    seeds = all_nodes[all_nodes["country_codes"].isin(CCODES)].index

    # # Next Computes the shortest path from the node seed to all reachable nodes that
    # # are cutoff hops away and closer.  The function returns a dictionary with the target nodes as keys,
    # # so the keys are the cutoff-neighborhood of the seed.
    nodes_of_interest = set.union(*[set(nx.single_source_shortest_path_length(F, seed, cutoff = 2).keys())
                                   for seed in seeds])
    # nodes_of_interest = [elem.nodes() for elem in nx.connected_component_subgraphs(F)
    #                     if nx.number_of_nodes(elem) >= 3
    #                     or nx.number_of_edges(elem) >= 3]
    # Extract the subgraph that contains all the keys for all the dictionaries
    # with all the connecting eges ... and relabel it
    ego = nx.subgraph(F, nodes_of_interest)
    nodes = all_nodes.reindex(ego)
    nodes = nodes[~nodes.index.duplicated()] # There are duplicate country codes on some nodes
    # nodes = nodes.fillna('Unknown')
    nodes = nodes.replace(np.nan, 'Unknown', regex=True)
    nodes = nodes.replace(pd.isnull, 'Unknown', regex=True)
    nodes = nodes[nodes["type"].notnull()]
    #  Sets node attributes for nodes["country_codes"] from a given value or dictionary of values
    nx.set_node_attributes(ego, nodes["country_codes"], "cc")
    nx.set_node_attributes(ego, nodes["type"], "ty")
    nx.set_node_attributes(ego, nodes["name"], "nm")
    # get rid of null and turn the list into a dictionary
    valid_names = nodes[nodes["name"].notnull()]["name"].to_dict()
    ego = nx.relabel_nodes(ego, nodes[nodes.name.notnull()].name)
    # ego = nx.relabel_nodes(ego, nodes[nodes.address.notnull()
    #                                 & nodes.name.isnull()].address)
    nx.relabel_nodes(ego, valid_names)

    # ego_edges = filter(lambda x: g.degree()[x[0]] > 0 and g.degree()[x[1]] > 0, g.edges())
    # ego.add_edges_from(ego_edges)
    return ego

def GeneralGraph(G, filename):
    '''
    INPUT:
    - ego, NetworkX subgraph
    - filename, is the name of the file you want to save it to.
    '''
    # Save and proceed to gephi!
    with open ("/Users/rdelapp/Galvanize/DSI_g61/capstone/panama_papers/figures/panama-{y}.graphml".format(y=filename), "wb") as ofile:
        nx.write_graphml(G, ofile)
    pass

def split_graph(G, ego_nodes, part_type):
    if part_type == 'dendrogram':
        partition = cm.generate_dendrogram(G)
    else:
    #first compute the best partition
        partition = cm.best_partition(G) # Louvian
    for com in set(partition.values()):
        list_nodes = [nodes for nodes in partition.keys() if partition[nodes] == com]
        ego[com] = nx.subgraph(F, list_nodes)
        # with all the connecting eges ... and relabel it
        ego = nx.subgraph(F, list_nodes)
        nodes = ego_nodes.reindex(ego)
        nodes = nodes[~nodes.index.duplicated()] # There are duplicate country codes on some nodes

        #  Sets node attributes for nodes["country_codes"] from a given value or dictionary of values
        nx.set_node_attributes(ego, nodes["country_codes"], "cc")
        nx.set_node_attributes(ego, nodes["type"], "ty")
        nx.set_node_attributes(ego, nodes["name"], "nm")
        # get rid of null and turn the list into a dictionary
        valid_names = nodes[nodes["name"].notnull()]["name"].to_dict()
        ego = nx.relabel_nodes(ego, nodes[nodes.name.notnull()].name)
        # ego = nx.relabel_nodes(ego, nodes[nodes.address.notnull()
        #                                 & nodes.name.isnull()].address)
        nx.relabel_nodes(ego, valid_names)
    # ego = build_community_subgroup(G, nodes)
    # GeneralGraph(ego, 'partition-modularity')
    # nx.draw_networkx_nodes(G, pos, list_nodes, node_size = 20,
    #                             node_color = str(count / size))
    # nx.draw_networkx_edges(G,pos, alpha=0.5)
    # plt.show()


# if __name__ == '__main__':
