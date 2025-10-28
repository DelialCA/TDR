import pandas as pd
import networkx as nx
import matplotlib.pyplot as plt

file_path = "TDR.xlsx"
stops_df = pd.read_excel(file_path, sheet_name="Parades")
connections_df = pd.read_excel(file_path, sheet_name="Matriu", index_col=0)

stops_df['Latitud'] = stops_df['Latitud'].astype(str).str.replace(',', '.').astype(float)
stops_df['Longitud'] = stops_df['Longitud'].astype(str).str.replace(',', '.').astype(float)

connections_df.replace('-', None, inplace=True)
connections_df = connections_df.apply(pd.to_numeric, errors='coerce')

def normalize(name):
    return str(name).strip().lower()

name_to_id = {
    normalize(name): stop_id
    for name, stop_id in zip(stops_df['Nom'], stops_df['ID'])
}

connections_df.index = connections_df.index.map(normalize).map(name_to_id)
connections_df.columns = connections_df.columns.map(normalize).map(name_to_id)

missing_rows = connections_df.index[connections_df.index.isna()]
missing_cols = connections_df.columns[connections_df.columns.isna()]
if not missing_rows.empty or not missing_cols.empty:
    print("No coincident", missing_rows.tolist())
    print("No coincidents 2", missing_cols.tolist())

connections_df.dropna(axis=0, inplace=True)
connections_df.dropna(axis=1, inplace=True)


G = nx.DiGraph()


for _, row in stops_df.iterrows():
    G.add_node(row['ID'], label=row['Nom'], pos=(row['Longitud'], row['Latitud']))


for from_stop in connections_df.index:
    if from_stop == 1:
        print(from_stop)
    for to_stop in connections_df.columns:
        weight = connections_df.at[from_stop, to_stop]
        if pd.notna(weight) and weight > 0:
            G.add_edge(from_stop, to_stop, weight=weight)

pos = nx.get_node_attributes(G, 'pos')
labels = nx.get_node_attributes(G, 'label')
edge_labels = nx.get_edge_attributes(G, 'weight')

plt.figure(figsize=(14, 12))
nx.draw(G, pos, with_labels=True, labels=labels, node_size=500, node_color='skyblue', font_size=8, arrows=True)
nx.draw_networkx_edge_labels(G, pos, edge_labels=edge_labels, font_size=6)
plt.title("Graf del bus")
plt.axis('off')
plt.tight_layout()
plt.show()