# ============================================
# PREGUNTA 4 - NODO DE TRANSBORDO ZÚRICH
# ============================================

import gurobipy as gp
from gurobipy import GRB

# -------------------------
# Conjuntos
# -------------------------

I = ["A", "B", "C", "T"]      # Orígenes: A,B,C y T=Zúrich
J = ["1", "2", "3", "4"]      # Destinos: 1=París, 2=Berlín, 3=Varsovia, 4=Zúrich

# Conjuntos "originales" (almacenes y destinos reales)
I_almacenes = ["A", "B", "C"]   # almacenes con oferta y coste fijo
J_destinos = ["1", "2", "3"]    # destinos con demanda

# -------------------------
# Parámetros
# -------------------------

# Oferta (mil Gb) solo para A,B,C
s = {"A": 5, "B": 6, "C": 7}

# Demanda (mil Gb) solo para París, Berlín, Varsovia
d = {"1": 4, "2": 5, "3": 9}

# Costes variables en céntimos €/MilGb para arcos directos A,B,C -> 1,2,3
cents_direct = {
    ("A", "1"): 4, ("A", "2"): 3, ("A", "3"): 6,
    ("B", "1"): 7, ("B", "2"): 4, ("B", "3"): 9,
    ("C", "1"): 9, ("C", "2"): 5, ("C", "3"): 2,
}

# Creamos estructura de costes en €/MilGb para TODOS los pares (i,j)
c = {}

# 1) Copiamos los directos A,B,C -> 1,2,3
for (i, j), c_ij in cents_direct.items():
    c[(i, j)] = c_ij / 100.0

# 2) Coste 0.05 €/MilGb para arcos con Zúrich:
#    - de almacenes a Zúrich: A,B,C -> 4
#    - de Zúrich a destinos: T -> 1,2,3
for i in I_almacenes:
    c[(i, "4")] = 0.05   # origen normal -> Zúrich

for j in J_destinos:
    c[("T", j)] = 0.05   # Zúrich -> destino normal

# 3) Para los pares que no hemos definido coste (incluido T->4),
#    les ponemos coste 0, pero luego forzaremos T->4=0 con restricciones.
for i in I:
    for j in J:
        if (i, j) not in c:
            c[(i, j)] = 0.0

Q = 10        # capacidad por canal (mil Gb)
F = 50        # coste fijo por canal
F_extra = 15  # recargo si usamos 5º canal
G = 5000      # coste fijo por almacén
max_canales_par = 5  # cota máxima para n_ij

# -------------------------
# Modelo y variables
# -------------------------

m4 = gp.Model("P4_Zurich")

# Flujos x_ij (mil Gb) para todos los pares (i,j)
x = m4.addVars(I, J, lb=0.0, name="x")

# Número de canales n_ij entre i y j
n = m4.addVars(I, J, vtype=GRB.INTEGER, lb=0, name="n")

# Variables binarias y_ij (par activo)
y = m4.addVars(I, J, vtype=GRB.BINARY, name="y")

# Canal adicional (5º canal)
y_plus = m4.addVar(vtype=GRB.BINARY, name="y_plus")

# Activación de almacenes (solo A,B,C)
z = m4.addVars(I_almacenes, vtype=GRB.BINARY, name="z")

# -------------------------
# Función objetivo
# -------------------------

m4.setObjective(
    # Costes variables para todos los arcos (incluyendo los de Zúrich)
    gp.quicksum(c[(i, j)] * x[i, j] for i in I for j in J)
    # Coste fijo por canal (tanto directos como con Zúrich)
    + F * gp.quicksum(n[i, j] for i in I for j in J)
    # Coste fijo por almacén (solo A,B,C)
    + G * gp.quicksum(z[i] for i in I_almacenes)
    # Recargo si se usa el 5º canal
    + F_extra * y_plus,
    GRB.MINIMIZE
)

# -------------------------
# Restricciones
# -------------------------

# 1) Capacidad de cada par (i,j): x_ij <= Q * n_ij
for i in I:
    for j in J:
        m4.addConstr(
            x[i, j] <= Q * n[i, j],
            name=f"cap_{i}_{j}"
        )

# 2) Oferta de cada almacén A,B,C:
#    sum_{j∈J} x_ij <= s_i * z_i
for i in I_almacenes:
    m4.addConstr(
        gp.quicksum(x[i, j] for j in J) <= s[i] * z[i],
        name=f"oferta_{i}"
    )

# 3) Demanda de cada destino 1,2,3:
#    sum_{i∈I} x_ij = d_j
for j in J_destinos:
    m4.addConstr(
        gp.quicksum(x[i, j] for i in I) == d[j],
        name=f"demanda_{j}"
    )

# 4) Límite global de canales:
#    sum_{i∈I} sum_{j∈J} n_ij <= 4 + y_plus
m4.addConstr(
    gp.quicksum(n[i, j] for i in I for j in J) <= 4 + y_plus,
    name="limite_canales"
)

# 5) Privacidad Berlín (solo afecta a canales A->2 y B->2):
m4.addConstr(
    y["A", "2"] + y["B", "2"] <= 1,
    name="privacidad_Berlin"
)

# 6) Enlace n_ij - y_ij: n_ij <= 5 * y_ij  (para todos los pares)
for i in I:
    for j in J:
        m4.addConstr(
            n[i, j] <= max_canales_par * y[i, j],
            name=f"enlace_{i}_{j}"
        )

# 7) Zúrich no se envía a sí mismo: x_T4 = 0 y n_T4 = 0
m4.addConstr(x["T", "4"] == 0, name="zurich_mismo_flujo")
m4.addConstr(n["T", "4"] == 0, name="zurich_mismo_canales")

# 8) Balance de flujo en Zúrich:
#    lo que entra en Zúrich (destino 4) = lo que sale de Zúrich (origen T)
#    sum_{i∈I_almacenes} x_i4 = sum_{j∈J_destinos} x_Tj
m4.addConstr(
    gp.quicksum(x[i, "4"] for i in I_almacenes)
    == gp.quicksum(x["T", j] for j in J_destinos),
    name="balance_Zurich"
)

# 9) Flujo mínimo Zúrich → París si el canal está activo:
#    x_T1 >= 0.5 * y_T1
m4.addConstr(
    x["T", "1"] >= 0.5 * y["T", "1"],
    name="min_flujo_T_Paris"
)

# -------------------------
# Optimización y salida
# -------------------------

m4.optimize()

if m4.status == GRB.OPTIMAL:
    print("\n--- Pregunta 4 ---")
    print(f"Coste mínimo = {m4.objVal:.2f} €")

    print("\nFlujos x_ij (mil Gb):")
    for i in I:
        for j in J:
            if x[i, j].X > 1e-6:
                print(f"x[{i},{j}] = {x[i, j].X:.2f}")

    print("\nNúmero de canales n_ij:")
    for i in I:
        for j in J:
            if n[i, j].X > 0.5:
                print(f"n[{i},{j}] = {int(round(n[i, j].X))}")

    print("\nAlmacenes activos z_i:")
    for i in I_almacenes:
        print(f"z[{i}] = {int(z[i].X)}")

    print("\nPares activos y_ij:")
    for i in I:
        for j in J:
            if y[i, j].X > 0.5:
                print(f"y[{i},{j}] = 1")

    print(f"\ny_plus = {int(y_plus.X)}")
else:
    print("No se encontró solución óptima en P4.")
