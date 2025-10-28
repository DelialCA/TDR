import pandas as pd
import networkx as nx
import matplotlib.pyplot as plt


FILE_PATH = "TDR.xlsx"
PARADA_SHEET = "Parades"
MATRIZ_SHEET = "Matriu"

stops_df = pd.read_excel(FILE_PATH, sheet_name=PARADA_SHEET)
stops_df['Latitud'] = stops_df['Latitud'].astype(str).str.replace(',', '.').astype(float)
stops_df['Longitud'] = stops_df['Longitud'].astype(str).str.replace(',', '.').astype(float)

id2label = dict(zip(stops_df['ID'], stops_df['Nom']))
valid_ids = set(stops_df['ID'])


connections_df = pd.read_excel(FILE_PATH, sheet_name=MATRIZ_SHEET, index_col=0)
connections_df.replace('-', None, inplace=True)
connections_df = connections_df.apply(pd.to_numeric, errors='coerce')

def norm(x): return str(x).strip().lower()
name2id = {norm(n): i for n, i in zip(stops_df['Nom'], stops_df['ID'])}

connections_df.index = connections_df.index.map(norm).map(name2id)
connections_df.columns = connections_df.columns.map(norm).map(name2id)

connections_df.dropna(axis=0, inplace=True)
connections_df.dropna(axis=1, inplace=True)

connections_df.index = connections_df.index.astype(int)
connections_df.columns = connections_df.columns.astype(int)

G = nx.DiGraph()
for _, row in stops_df.iterrows():
    G.add_node(row['ID'], label=row['Nom'], pos=(row['Longitud'], row['Latitud']))

for u in connections_df.index:
    for v in connections_df.columns:
        w = connections_df.at[u, v]
        if pd.notna(w) and w > 0:
            G.add_edge(u, v, weight=float(w))


depot_id = 9
num_vehicles = 2
routes = [[depot_id] for _ in range(num_vehicles)]


def calcular_temps_ruta(route, graph):
    total = 0
    for i in range(len(route)-1):
        u, v = route[i], route[i+1]
        if graph.has_edge(u, v):
            total += graph[u][v]['weight']
        else:
            total += 1e6  
    return total

def mostrar_rutes_grafic(rutes, graph, id2label, fig=None, ax=None):
    if fig is None or ax is None:
        fig, ax = plt.subplots(figsize=(12, 10))
    else:
        ax.clear()
    pos = {node:(data['pos'][0], data['pos'][1]) for node, data in graph.nodes(data=True)}
    colors = ['tab:blue', 'tab:orange', 'tab:green', 'tab:purple']

    nx.draw_networkx_nodes(graph, pos, node_color='lightgray', node_size=300, ax=ax)
    nx.draw_networkx_labels(graph, pos, labels=id2label, font_size=9, ax=ax)
    nx.draw_networkx_nodes(graph, pos, nodelist=[depot_id], node_color='red', node_size=500, label='Dipòsit', ax=ax)

    for i, route in enumerate(rutes):
        color = colors[i % len(colors)]
        if len(route) > 1:
            edges = [(route[j], route[j+1]) for j in range(len(route)-1)]
            nx.draw_networkx_edges(graph, pos, edgelist=edges, edge_color=color, width=3, alpha=0.7, arrows=True, ax=ax)
        temps = calcular_temps_ruta(route, graph)
        ax.text(0.01, 0.95 - i*0.05, f"Ruta {i+1}: {len(route)-1} parades (excl. dipòsit), Temps aprox: {int(temps)}",
                transform=fig.transFigure, color=color, fontsize=12)

    ax.set_title("Rutes de repartiment")
    ax.axis('off')
    ax.legend()
    fig.tight_layout()
    fig.canvas.draw()
    plt.pause(0.1)  
    return fig, ax


plt.ion()
fig, ax = plt.subplots(figsize=(12, 10))

print(f"Rutes inicials (comencen al dipòsit ID {depot_id}):")
for i, r in enumerate(routes, 1):
    print(f"Ruta {i}: {r}")

mostrar_rutes_grafic(routes, G, id2label, fig, ax)

print("\nIntrodueix IDs de parades (escriu 'fi' per acabar).")


while True:
    user_input = input("ID parada: ").strip()
    if user_input.lower() == 'fi':
        break
    try:
        parada_id = int(user_input)
    except ValueError:
        print("❌ Introdueix un número d'ID o 'fi' per acabar.")
        continue
    if parada_id not in valid_ids:
        print(f"❌ L'ID {parada_id} no és vàlid.")
        continue

    print("Rutes actuals:")
    for i, r in enumerate(routes, 1):
        noms = [id2label.get(pid, str(pid)) for pid in r]
        print(f"  {i}: {r} ({' -> '.join(noms)})")

    while True:
        try:
            sel = int(input(f"A quina ruta vols afegir la parada {parada_id} ({id2label[parada_id]})? (1-{num_vehicles}): "))
            if 1 <= sel <= num_vehicles:
                break
            else:
                print(f"❌ Tria un número entre 1 i {num_vehicles}.")
        except ValueError:
            print("❌ Has d'introduir un número.")

    routes[sel-1].append(parada_id)
    print(f"✅ Parada {parada_id} afegida a la ruta {sel}.")

    mostrar_rutes_grafic(routes, G, id2label, fig, ax)

print("\n RUTES COMPLETES")
for i, r in enumerate(routes, 1):
    noms = [id2label.get(pid, str(pid)) for pid in r]
    temps = calcular_temps_ruta(r, G)
    print(f"Ruta {i} (parades: {len(r)-1}, temps aprox: {int(temps)}):")
    for pid, nom in zip(r, noms):
        print(f"  {pid} – {nom}")

plt.ioff()
plt.show()