# ============================================
# Práctica con ordenador I - Extensión 2
# DataMind Labs (Pregunta 3)
# ============================================

import gurobipy as gp
from gurobipy import GRB

# --------------------------------------------
# 1. Datos de entrada
# --------------------------------------------

origins = ["A", "B", "C"]          # A: Lisboa, B: Madrid, C: Turín
destinations = ["1", "2", "3"]     # 1: París, 2: Berlín, 3: Varsovia

# Oferta (MilGb)
supply = {"A": 5, "B": 6, "C": 7}

# Demanda (MilGb)
demand = {"1": 4, "2": 5, "3": 9}

# Costes variables en céntimos €/MilGb
cost_cents = {
    ("A", "1"): 4, ("A", "2"): 3, ("A", "3"): 6,
    ("B", "1"): 7, ("B", "2"): 4, ("B", "3"): 9,
    ("C", "1"): 9, ("C", "2"): 5, ("C", "3"): 2,
}

# Pasamos a €/MilGb
cost = {(i, j): cost_cents[i, j] / 100.0 for (i, j) in cost_cents}

channel_capacity = 10          # MilGb por canal
base_channel_cost = 50         # € por canal
extra_channel_increment = 15   # € extra si usamos el 5º canal
warehouse_fixed_cost = 5000    # € por activar cada almacén
max_channels_per_pair = 5      # cota superior razonable por par

# --------------------------------------------
# 2. Modelo y variables
# --------------------------------------------

m = gp.Model("DataMind_Ext2")

# Flujo de datos (MilGb)
x = m.addVars(origins, destinations, lb=0.0, name="x")

# Número de canales entre i y j
k = m.addVars(
    origins, destinations,
    vtype=GRB.INTEGER, lb=0,
    name="k"
)

# Indicador binario de par i-j activo (para privacidad)
y = m.addVars(
    origins, destinations,
    vtype=GRB.BINARY,
    name="y"
)

# Uso del 5º canal
y_extra = m.addVar(vtype=GRB.BINARY, name="y_extra")

# NUEVO: activación de almacenes A, B, C
z = m.addVars(
    origins,
    vtype=GRB.BINARY,
    name="z"
)

# --------------------------------------------
# 3. Función objetivo
#    Min: costes variables + canales + 5º canal + almacenes
# --------------------------------------------

m.setObjective(
    gp.quicksum(cost[i, j] * x[i, j] for i in origins for j in destinations)
    + base_channel_cost * gp.quicksum(k[i, j] for i in origins for j in destinations)
    + extra_channel_increment * y_extra
    + warehouse_fixed_cost * gp.quicksum(z[i] for i in origins),
    GRB.MINIMIZE
)

# --------------------------------------------
# 4. Restricciones
# --------------------------------------------

# 4.1 Capacidad total entre i y j: x_ij <= 10 * k_ij
for i in origins:
    for j in destinations:
        m.addConstr(
            x[i, j] <= channel_capacity * k[i, j],
            name=f"cap_{i}_{j}"
        )

# 4.2 Enlace entre k_ij y y_ij: solo hay canales si el par está activo
for i in origins:
    for j in destinations:
        m.addConstr(
            k[i, j] <= max_channels_per_pair * y[i, j],
            name=f"link_{i}_{j}"
        )

# 4.3 Oferta por almacén (MODIFICADA): sum_j x_ij <= supply_i * z_i
for i in origins:
    m.addConstr(
        gp.quicksum(x[i, j] for j in destinations) <= supply[i] * z[i],
        name=f"supply_{i}"
    )

# 4.4 Demanda en cada destino (igual que antes)
for j in destinations:
    m.addConstr(
        gp.quicksum(x[i, j] for i in origins) == demand[j],
        name=f"demand_{j}"
    )

# 4.5 Número total de canales: sum k_ij <= 4 + y_extra
m.addConstr(
    gp.quicksum(k[i, j] for i in origins for j in destinations) <= 4 + y_extra,
    name="num_channels"
)

# 4.6 Privacidad en Berlín: no A->2 y B->2 a la vez
m.addConstr(
    y["A", "2"] + y["B", "2"] <= 1,
    name="privacy_Berlin"
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
    for i in origins:
        for j in destinations:
            if x[i, j].x > 1e-6:
                print(f"  x[{i},{j}] = {x[i, j].x:.2f}")

    print("\nNúmero de canales k_ij:")
    for i in origins:
        for j in destinations:
            if k[i, j].x > 0.5:
                print(f"  k[{i},{j}] = {int(round(k[i, j].x))}")

    print("\nPares activos y_ij:")
    for i in origins:
        for j in destinations:
            if y[i, j].x > 0.5:
                print(f"  y[{i},{j}] = 1")

    print("\nAlmacenes activos z_i:")
    for i in origins:
        print(f"  z[{i}] = {int(z[i].x)}")

    print(f"\n¿Se usa el 5º canal extra? y_extra = {int(y_extra.x)}")
else:
    print("El modelo no ha encontrado solución óptima.")
