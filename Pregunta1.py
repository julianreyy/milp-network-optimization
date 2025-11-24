import gurobipy as gp
from gurobipy import GRB


#Datos de entrada

#Orígenes y destinos
origins = ["A", "B", "C"]  # A: Lisboa, B: Madrid, C: Turín
destinations = ["1", "2", "3"] # 1: París, 2: Berlín, 3: Varsovia

# Oferta
oferta = {
    "A": 5,
    "B": 6,
    "C": 7
}

# Demanda
demand = {
    "1": 4,
    "2": 5,
    "3": 9
}

#Costes variables en céntimos €/MilGb
cost_cents = {
    ("A", "1"): 4, ("A", "2"): 3, ("A", "3"): 6,
    ("B", "1"): 7, ("B", "2"): 4, ("B", "3"): 9,
    ("C", "1"): 9, ("C", "2"): 5, ("C", "3"): 2
}

#Se pasa de centimos/MilGb a €/MilGb
cost = {(i, j): cost_cents[i, j] / 100.0 for (i, j) in cost_cents}

channel_capacity = 10   # MilGb por canal
base_channel_cost = 50  # € por canal (los 4 primeros)
extra_channel_increment = 15 # € adicionales si se usa el canal quinto extra

#Parámetros y variables

m = gp.Model("DataMind_Base")

# Flujo de datos (MilGb)
x = m.addVars(origins, destinations, lb=0.0, name="x")

# Activación de canal entre i y j
y = m.addVars(origins, destinations, vtype=GRB.BINARY, name="y")

# Variable binaria: uso del 5º canal
y_extra = m.addVar(vtype=GRB.BINARY, name="y_extra")

#Función objetivo

m.setObjective(
    gp.quicksum(cost[i, j] * x[i, j] for i in origins for j in destinations)
    + base_channel_cost * gp.quicksum(y[i, j] for i in origins for j in destinations)
    + extra_channel_increment * y_extra,
    GRB.MINIMIZE
)

#Restricciones

#Capacidad por canal
for i in origins:
    for j in destinations:
        m.addConstr(x[i, j] <= channel_capacity * y[i, j],
                    name=f"cap_{i}_{j}")

#Oferta en cada origen
for i in origins:
    m.addConstr(
        gp.quicksum(x[i, j] for j in destinations) <= oferta[i],
        name=f"oferta{i}"
    )

#Demanda en cada destino
for j in destinations:
    m.addConstr(
        gp.quicksum(x[i, j] for i in origins) == demand[j],
        name=f"demand_{j}"
    )

#Número máximo de canales
m.addConstr(
    gp.quicksum(y[i, j] for i in origins for j in destinations) <= 4 + y_extra,
    name="num_channels"
)

# Privacidad en Berlín:

m.addConstr(
    y["A", "2"] + y["B", "2"] <= 1,
    name="privacy_Berlin"
)

#Optimización


m.optimize()

#Mostrar solución

if m.status == GRB.OPTIMAL:
    print(f"Coste total mínimo = {m.objVal:.2f} €\n")

    print("Flujos x_ij (MilGb):")
    for i in origins:
        for j in destinations:
            if x[i, j].x > 1e-6:
                print(f"  x[{i},{j}] = {x[i, j].x:.2f}")

    print("\nCanales activos y_ij:")
    for i in origins:
        for j in destinations:
            if y[i, j].x > 0.5:
                print(f"  y[{i},{j}] = 1")

    print(f"\n y_extra = {int(y_extra.x)}")
else:
    print("El modelo que se ha dado no ha encontrado la solución óptima.")
