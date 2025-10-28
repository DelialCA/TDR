import pandas as pd
import networkx as nx
import numpy as np
import matplotlib.pyplot as plt
from ortools.constraint_solver import pywrapcp, routing_enums_pb2
import folium
from folium import FeatureGroup

def generar_mapa_interactiu_multi_solucio(solutions, stops_df, index2id, id2label, depot_id=26, route_metrics=None, strategy_names=None):
    """
    Genera un mapa interactiu amb múltiples solucions de rutes.

    Paràmetres:
    - solutions: Llista de tuples [(routes, route_times), ...]
    - stops_df: DataFrame amb columnes ['ID', 'Latitud', 'Longitud']
    - index2id: Dict que converteix índexs interns a ID de parada
    - id2label: Dict que converteix ID a noms de parada
    - depot_id: ID del dipòsit (per defecte 26)
    - route_metrics: Opcional, llista de tuples (temps_total, [temps_ruta1, temps_ruta2])
    - strategy_names: Llista amb noms dels algorismes de cada solució
    """

    id2coord = dict(zip(stops_df['ID'], zip(stops_df['Latitud'], stops_df['Longitud'])))
    depot_coords = id2coord[depot_id]

    mapa = folium.Map(location=depot_coords, zoom_start=13, tiles="OpenStreetMap")
    colors = ['blue', 'orange', 'green', 'purple', 'darkred', 'cadetblue', 'darkblue', 'pink']

    for sol_num, (routes, route_times) in enumerate(solutions, start=1):
        alg_name = strategy_names[sol_num - 1] if strategy_names else f"Solució {sol_num}"
        capa = FeatureGroup(name=f"{alg_name}", show=(sol_num == 1))

        for v, r in enumerate(routes):
            color = colors[v % len(colors)]
            real_ids = [index2id[i] for i in r]
            coords = [id2coord[stop_id] for stop_id in real_ids]
            temps = route_times[v] if v < len(route_times) else "?"

            tooltip_text = f"Ruta {v+1} – {len(r)-2} parades – {temps} s"
            folium.PolyLine(coords, color=color, weight=5, opacity=0.8,
                            tooltip=tooltip_text).add_to(capa)

            for stop_id in real_ids:
                lat, lon = id2coord[stop_id]
                nom = id2label.get(stop_id, f"ID {stop_id}")
                folium.CircleMarker(
                    location=(lat, lon),
                    radius=5,
                    popup=nom,
                    color="black" if stop_id != depot_id else "red",
                    fill=True,
                    fill_color="red" if stop_id == depot_id else "white",
                    fill_opacity=0.9
                ).add_to(capa)

        
        folium.Marker(
            location=depot_coords,
            icon=folium.Icon(color='red', icon='bus', prefix='fa'),
            popup="DIPÒSIT"
        ).add_to(capa)

        capa.add_to(mapa)

    folium.LayerControl(collapsed=False).add_to(mapa)
    mapa.save("resultat eb.html")
    print("✅ Mapa desat com 'resultat.html' amb menú de solucions.")

#  1. CARREGAR DADES DES D'EXCEL
FILE_PATH = "TDR.xlsx"
PARADA_SHEET = "Parades"
MATRIZ_SHEET = "Matriu"

stops_df = pd.read_excel(FILE_PATH, sheet_name=PARADA_SHEET)
connections_df = pd.read_excel(FILE_PATH, sheet_name=MATRIZ_SHEET, index_col=0)

stops_df['Latitud'] = stops_df['Latitud'].astype(str).str.replace(',', '.').astype(float)
stops_df['Longitud'] = stops_df['Longitud'].astype(str).str.replace(',', '.').astype(float)

connections_df.replace('-', None, inplace=True)
connections_df = connections_df.apply(pd.to_numeric, errors='coerce')

def norm(x): return str(x).strip().lower()
name2id = {norm(n): i for n, i in zip(stops_df['Nom'], stops_df['ID'])}
connections_df.index = connections_df.index.map(norm).map(name2id)
connections_df.columns = connections_df.columns.map(norm).map(name2id)
connections_df.dropna(axis=0, inplace=True)
connections_df.dropna(axis=1, inplace=True)

#  2. CONSTRUIR EL GRAF 
G = nx.DiGraph()
for _, row in stops_df.iterrows():
    G.add_node(int(row['ID']), label=row['Nom'], pos=(row['Longitud'], row['Latitud']))

for u in connections_df.index:
    for v in connections_df.columns:
        w = connections_df.at[u, v]
        if pd.notna(w) and w > 0:
            G.add_edge(int(u), int(v), weight=float(w))


all_pairs = nx.floyd_warshall_numpy(G, weight='weight')
INF = 10**6
time_matrix = np.where(np.isinf(all_pairs), INF, np.rint(all_pairs)).astype(int)


num_stops = time_matrix.shape[0]
num_vehicles = 2


depot_id = 9
id_list = list(connections_df.index)
index2id = {i: id_ for i, id_ in enumerate(id_list)}
id2index = {id_: i for i, id_ in enumerate(id_list)}
depot_index = id2index[depot_id]

solutions = []
strategies = [
    routing_enums_pb2.FirstSolutionStrategy.PATH_CHEAPEST_ARC,
    routing_enums_pb2.FirstSolutionStrategy.PATH_MOST_CONSTRAINED_ARC,
    routing_enums_pb2.FirstSolutionStrategy.SAVINGS,
    routing_enums_pb2.FirstSolutionStrategy.CHRISTOFIDES,
    routing_enums_pb2.FirstSolutionStrategy.ALL_UNPERFORMED,
    routing_enums_pb2.FirstSolutionStrategy.BEST_INSERTION,
    routing_enums_pb2.FirstSolutionStrategy.PARALLEL_CHEAPEST_INSERTION,
    routing_enums_pb2.FirstSolutionStrategy.LOCAL_CHEAPEST_INSERTION,
    routing_enums_pb2.FirstSolutionStrategy.GLOBAL_CHEAPEST_ARC,
    routing_enums_pb2.FirstSolutionStrategy.LOCAL_CHEAPEST_ARC,
    routing_enums_pb2.FirstSolutionStrategy.FIRST_UNBOUND_MIN_VALUE,
    routing_enums_pb2.FirstSolutionStrategy.AUTOMATIC,
]
strategy_names = [
    "Solució 1 - Path Cheapest Arc",
    "Solució 2 - Path Most Constrained Arc",
    "Solució 3 - Savings",
    "Solució 4 - Christofides",
    "Solució 5 - All Unperformed",
    "Solució 6 - Best Insertion",
    "Solució 7 - Parallel Cheapest Insertion",
    "Solució 8 - Local Cheapest Insertion",
    "Solució 9 - Global Cheapest Arc",
    "Solució 10 - Local Cheapest Arc",
    "Solució 11 - First Unbound Min Value",
    "Solució 12 - Automatic",
]


for strat in strategies:
    manager = pywrapcp.RoutingIndexManager(num_stops,
                                           num_vehicles,
                                           [depot_index]*num_vehicles,
                                           [depot_index]*num_vehicles)
    routing = pywrapcp.RoutingModel(manager)

    def time_callback(from_idx, to_idx):
        i, j = manager.IndexToNode(from_idx), manager.IndexToNode(to_idx)
        return int(time_matrix[i, j])

    transit_callback_idx = routing.RegisterTransitCallback(time_callback)
    routing.SetArcCostEvaluatorOfAllVehicles(transit_callback_idx)

    def demand_callback(from_idx):
        return 1

    demand_callback_idx = routing.RegisterUnaryTransitCallback(demand_callback)
    max_stops_per_vehicle = int(np.ceil(num_stops * 1.2 / num_vehicles))  # 46

    routing.AddDimensionWithVehicleCapacity(
        demand_callback_idx,
        0,
        [max_stops_per_vehicle] * num_vehicles,
        True,
        "Load"
    )

    search_params = pywrapcp.DefaultRoutingSearchParameters()
    search_params.first_solution_strategy = strat
    search_params.local_search_metaheuristic = routing_enums_pb2.LocalSearchMetaheuristic.GUIDED_LOCAL_SEARCH
    search_params.time_limit.FromSeconds(20)
    search_params.log_search = False

    solution = routing.SolveWithParameters(search_params)
    if solution:
        routes, route_times = [], []
        for veh in range(num_vehicles):
            idx = routing.Start(veh)
            route, route_time = [], 0
            while not routing.IsEnd(idx):
                node = manager.IndexToNode(idx)
                route.append(node)
                next_idx = solution.Value(routing.NextVar(idx))
                route_time += routing.GetArcCostForVehicle(idx, next_idx, veh)
                idx = next_idx
            route.append(manager.IndexToNode(idx))
            routes.append(route)
            route_times.append(route_time)
        solutions.append((routes, route_times))

#  5. MOSTRAR SOLUCIONS 
id2label = dict(zip(stops_df['ID'], stops_df['Nom']))

for sol_num, (routes, route_times) in enumerate(solutions, start=1):
    alg_name = strategy_names[sol_num - 1]
    print(f"\n 🔁  {alg_name} ")
    total = sum(route_times)
    for k, (r, t) in enumerate(zip(routes, route_times), start=1):
        noms = [id2label[index2id[n]] for n in r]
        print(f"\n🚌  Ruta {k}  (temps {t}, parades: {len(r) - 2}):")
        for n, nom in zip(r, noms):
            print(f"   {n} – {nom}")
    print(f"\n⏱️  Temps total: {total}")

#  6. GRAF DE LA PRIMERA SOLUCIÓ 
if solutions:
    routes = solutions[0][0]
    pos = nx.get_node_attributes(G, 'pos')
    edge_colors = ['tab:blue', 'tab:orange']
    plt.figure(figsize=(14, 12))
    nx.draw(G, pos, node_size=500, node_color='lightgray',
            labels=id2label, font_size=8, arrows=False)

    for v, r in enumerate(routes):
        real_ids = [index2id[i] for i in r]
        edges = [(real_ids[i], real_ids[i+1]) for i in range(len(real_ids)-1)]
        nx.draw_networkx_edges(G, pos,
                               edgelist=edges,
                               edge_color=edge_colors[v % 2],
                               width=3,
                               arrows=True)

    nx.draw_networkx_nodes(G, pos,
                           nodelist=[depot_id],
                           node_color='red',
                           node_size=700,
                           label='Dipòsit')

    plt.title("Millor solució (de 5 estratègies)")
    plt.axis('off')
    plt.tight_layout()
    plt.show()
else:
    print("❌ No s'ha trobat cap solució vàlida.")

generar_mapa_interactiu_multi_solucio(solutions, stops_df, index2id, id2label, depot_id=26, strategy_names=strategy_names)