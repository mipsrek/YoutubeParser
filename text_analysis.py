import networkx as nx
import pandas as pd
from top2vec import Top2Vec


def topic_modeling(documents):
    model = Top2Vec(documents, speed="learn", workers=4)

    num_topics = model.get_num_topics()
    topic_words, word_scores, topic_scores, topic_nums = model.get_topics()

    model.visualize_topics()

    return topic_words

graph = nx.read_gexf('graph.gexf')
nodes_df = pd.DataFrame.from_dict(dict(graph.nodes(data=True)), orient='index')
nodes_df.index.name = 'node_id'
nodes_df.reset_index(inplace=True)

texts = nodes_df["transcript"].tolist()
topics = topic_modeling(texts)