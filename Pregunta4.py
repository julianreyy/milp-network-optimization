# ============================================
# Práctica con ordenador I - Extensión 3
# DataMind Labs (Pregunta 4)
# ============================================

import gurobipy as gp
from gurobipy import GRB

# --------------------------------------------
# 1. Datos de entrada
# --------------------------------------------

origins = ["A", "B", "C"]          # A: Lisboa, B: Madrid, C: Turín
destinations = ["1", "2", "3"]     # 1: París, 2: Berlín, 3: Varsovia
T = "T"                            # Nodo de transbordo: Zúrich

# Oferta (MilGb)
supply = {"A": 5, "B": 6, "C": 7}

# Demanda (MilGb)
demand = {"1": 4, "2": 5, "3": 9}

# Costes en céntimos €/MilGb
cost_cents = {
    # Arcos directos origen -> destino (igual que antes)
    ("A", "1"): 4, ("A", "2"): 3, ("A", "3"): 6,
    ("B", "1"): 7, ("B", "2"): 4, ("B", "3"): 9,
    ("C", "1"): 9, ("C", "2"): 5, ("C", "3"): 2,
}

# Añadimos costes de arcos que pasan por Zúrich: 5 céntimos €/MilGb
for i in origins:
    cost_cents[(i, T)] = 5
for j in destinations:
    cost_cents[(T, j)] = 5

# Convertimos a €/MilGb
cost = {a: cost_cents[a] / 100.0 for a in cost_cents}

channel_capacity = 10          # MilGb por canal
base_channel_cost = 50         # € por canal
extra_channel_increment = 15   # € extra si se usa el 5º canal
warehouse_fixed_cost = 5000    # € por almacén activado
max_channels_per_pair = 5      # cota superior razonable por arco

# Conjunto de arcos:
arcs = []

# Arcos directos origen -> destino
for i in origins:
    for j in destinations:
        arcs.append((i, j))

# Arcos origen -> Zúrich
for i in origins:
    arcs.append((i, T))

# Arcos Zúrich -> destino
for j in destinations:
    arcs.append((T, j))

# --------------------------------------------
# 2. Modelo y variables
# --------------------------------------------

m = gp.Model("DataMind_Ext3")

# Flujo x[a] (MilGb) para cada arco a
x = m.addVars(arcs, lb=0.0, name="x")

# Número de canales k[a] en cada arco a
k = m.addVars(arcs, vtype=GRB.INTEGER, lb=0, name="k")

# Indicador de arco activo y[a]
y = m.addVars(arcs, vtype=GRB.BINARY, name="y")

# Uso del 5º canal
y_extra = m.addVar(vtype=GRB.BINARY, name="y_extra")

# Activación de almacenes (A, B, C)
z = m.addVars(origins, vtype=GRB.BINARY, name="z")

# --------------------------------------------
# 3. Función objetivo
# --------------------------------------------

m.setObjective(
    # Costes variables
    gp.quicksum(cost[a] * x[a] for a in arcs)
    # Costes fijos por canal
    + base_channel_cost * gp.quicksum(k[a] for a in arcs)
    # Recargo si se usa el 5º canal
    + extra_channel_increment * y_extra
    # Costes fijos de almacenes
    + warehouse_fixed_cost * gp.quicksum(z[i] for i in origins),
    GRB.MINIMIZE
)

# --------------------------------------------
# 4. Restricciones
# --------------------------------------------

# 4.1 Capacidad: x[a] <= 10 * k[a] para todos los arcos
for (i, j) in arcs:
    m.addConstr(
        x[i, j] <= channel_capacity * k[i, j],
        name=f"cap_{i}_{j}"
    )

# 4.2 Enlace entre k[a] y y[a]: solo hay canales si el arco está activo
for (i, j) in arcs:
    m.addConstr(
        k[i, j] <= max_channels_per_pair * y[i, j],
        name=f"link_{i}_{j}"
    )

# 4.3 Oferta en cada origen: sum_j x[i,j] <= supply[i] * z[i]
for i in origins:
    m.addConstr(
        gp.quicksum(x[i, j] for (ii, j) in arcs if ii == i) <= supply[i] * z[i],
        name=f"supply_{i}"
    )

# 4.4 Demanda en cada destino: sum_i x[i,j] == demand[j]
for j in destinations:
    m.addConstr(
        gp.quicksum(x[i, j] for (i, jj) in arcs if jj == j) == demand[j],
        name=f"demand_{j}"
    )

# 4.5 Balance de flujo en Zúrich: sum_i x[i,T] = sum_j x[T,j]
m.addConstr(
    gp.quicksum(x[i, T] for i in origins) ==
    gp.quicksum(x[T, j] for j in destinations),
    name="balance_Zurich"
)

# 4.6 Número total de canales: sum k[a] <= 4 + y_extra
m.addConstr(
    gp.quicksum(k[a] for a in arcs) <= 4 + y_extra,
    name="num_channels"
)

# 4.7 Privacidad en Berlín: no A->2 y B->2 a la vez
m.addConstr(
    y["A", "2"] + y["B", "2"] <= 1,
    name="privacy_Berlin"
)

# 4.8 Mínimo flujo si se activa Zúrich -> París: x[T,1] >= 0.5 * y[T,1]
m.addConstr(
    x[T, "1"] >= 0.5 * y[T, "1"],
    name="min_flow_T_Paris"
)

# --------------------------------------------
# 5. Optimización
# --------------------------------------------

m.optimize()

# --------------------------------------------
# 6. Mostrar solución
# --------------------------------------------

if m.status == GRB.OPTIMAL:
    print(f"Coste total mínimo = {m.objVal:.2f} €\n")

    print("Flujos x_ij (MilGb):")
    for (i, j) in arcs:
        if x[i, j].x > 1e-6:
            print(f"  x[{i},{j}] = {x[i, j].x:.2f}")

    print("\nNúmero de canales k_ij:")
    for (i, j) in arcs:
        if k[i, j].x > 0.5:
            print(f"  k[{i},{j}] = {int(round(k[i, j].x))}")

    print("\nArcos activos y_ij:")
    for (i, j) in arcs:
        if y[i, j].x > 0.5:
            print(f"  y[{i},{j}] = 1")

    print("\nAlmacenes activos z_i:")
    for i in origins:
        print(f"  z[{i}] = {int(z[i].x)}")

    print(f"\n¿Se usa el 5º canal extra? y_extra = {int(y_extra.x)}")
else:
    print("El modelo no ha encontrado solución óptima.")
