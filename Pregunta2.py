# ============================================
# Práctica con ordenador I - Extensión 1
# DataMind Labs (Pregunta 2)
# ============================================

import gurobipy as gp
from gurobipy import GRB

# --------------------------------------------
# 1. Datos de entrada  (IGUAL que en P1)
# --------------------------------------------

origins = ["A", "B", "C"]          # A: Lisboa, B: Madrid, C: Turín
destinations = ["1", "2", "3"]     # 1: París, 2: Berlín, 3: Varsovia

supply = {"A": 5, "B": 6, "C": 7}  # MilGb
demand = {"1": 4, "2": 5, "3": 9}  # MilGb

# Costes variables en céntimos €/MilGb
cost_cents = {
    ("A", "1"): 4, ("A", "2"): 3, ("A", "3"): 6,
    ("B", "1"): 7, ("B", "2"): 4, ("B", "3"): 9,
    ("C", "1"): 9, ("C", "2"): 5, ("C", "3"): 2
}

# Pasamos a €/MilGb
cost = {(i, j): cost_cents[i, j] / 100.0 for (i, j) in cost_cents}

channel_capacity = 10          # MilGb por canal
base_channel_cost = 50         # € por canal
extra_channel_increment = 15   # € extra si usamos el 5º canal
max_channels_per_pair = 5      # cota superior razonable por par

# --------------------------------------------
# 2. Modelo y variables
# --------------------------------------------

m = gp.Model("DataMind_Ext1")

# Flujo de datos (MilGb)  [IGUAL que en P1]
x = m.addVars(origins, destinations, lb=0.0, name="x")

# NUEVO en P2: número de canales entre i y j
k = m.addVars(
    origins, destinations,
    vtype=GRB.INTEGER, lb=0,
    name="k"
)

# Se mantiene y_ij como indicador binario para privacidad
# (ya no mide "hay 1 canal o no", sino "el par está activo")
y = m.addVars(
    origins, destinations,
    vtype=GRB.BINARY,
    name="y"
)

# Variable binaria para canal extra (igual que en P1)
y_extra = m.addVar(vtype=GRB.BINARY, name="y_extra")

# --------------------------------------------
# 3. Función objetivo
#    Min: costes variables + costes fijos por canal
# --------------------------------------------
# CAMBIO respecto a P1:
#  - antes: 50 * sum(y[i,j])
#  - ahora: 50 * sum(k[i,j])

m.setObjective(
    gp.quicksum(cost[i, j] * x[i, j] for i in origins for j in destinations)
    + base_channel_cost * gp.quicksum(k[i, j] for i in origins for j in destinations)
    + extra_channel_increment * y_extra,
    GRB.MINIMIZE
)

# --------------------------------------------
# 4. Restricciones
# --------------------------------------------

# 4.1 Capacidad por par (CAMBIO respecto a P1)
#     Antes: x[i,j] <= 10 * y[i,j]
#     Ahora: x[i,j] <= 10 * k[i,j]  (capacidad total de todos los canales entre i y j)
for i in origins:
    for j in destinations:
        m.addConstr(
            x[i, j] <= channel_capacity * k[i, j],
            name=f"cap_{i}_{j}"
        )

# 4.2 Enlace entre k_ij y y_ij (NUEVO en P2)
#     Si hay canales (k_ij > 0) entonces y_ij = 1.
for i in origins:
    for j in destinations:
        m.addConstr(
            k[i, j] <= max_channels_per_pair * y[i, j],
            name=f"link_{i}_{j}"
        )

# 4.3 Oferta en cada origen  (IGUAL que en P1)
for i in origins:
    m.addConstr(
        gp.quicksum(x[i, j] for j in destinations) <= supply[i],
        name=f"supply_{i}"
    )

# 4.4 Demanda en cada destino  (IGUAL que en P1)
for j in destinations:
    m.addConstr(
        gp.quicksum(x[i, j] for i in origins) == demand[j],
        name=f"demand_{j}"
    )

# 4.5 Número total de canales  (CAMBIO respecto a P1)
#     Antes: sum y_ij <= 4 + y_extra
#     Ahora: sum k_ij <= 4 + y_extra
m.addConstr(
    gp.quicksum(k[i, j] for i in origins for j in destinations) <= 4 + y_extra,
    name="num_channels"
)

# 4.6 Restricción de privacidad en Berlín  (IGUAL que en P1)
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

    print(f"\n¿Se usa el 5º canal extra? y_extra = {int(y_extra.x)}")
else:
    print("El modelo no ha encontrado solución óptima.")
