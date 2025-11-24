# ============================================
# PREGUNTA 3 - COSTE FIJO POR ALMACÉN
# ============================================

import gurobipy as gp
from gurobipy import GRB

# -------------------------
# Datos
# -------------------------

I = ["A", "B", "C"]
J = ["1", "2", "3"]

s = {"A": 5, "B": 6, "C": 7}
d = {"1": 4, "2": 5, "3": 9}

cents = {
    ("A", "1"): 4, ("A", "2"): 3, ("A", "3"): 6,
    ("B", "1"): 7, ("B", "2"): 4, ("B", "3"): 9,
    ("C", "1"): 9, ("C", "2"): 5, ("C", "3"): 2,
}
c = {(i, j): cents[i, j] / 100.0 for (i, j) in cents}

Q = 10
F = 50
F_extra = 15
G = 5000          # coste fijo por almacén
max_canales_par = 5

# -------------------------
# Modelo y variables
# -------------------------

m3 = gp.Model("P3_Almacenes")

x = m3.addVars(I, J, lb=0.0, name="x")                 # x_ij
y = m3.addVars(I, J, vtype=GRB.BINARY, name="y")       # y_ij
n = m3.addVars(I, J, vtype=GRB.INTEGER, lb=0, name="n")# n_ij
y_plus = m3.addVar(vtype=GRB.BINARY, name="y_plus")    # y^+
z = m3.addVars(I, vtype=GRB.BINARY, name="z")          # z_i

# -------------------------
# Función objetivo
# -------------------------

m3.setObjective(
    gp.quicksum(c[i, j] * x[i, j] for i in I for j in J)
    + F * gp.quicksum(n[i, j] for i in I for j in J)
    + G * gp.quicksum(z[i] for i in I)
    + F_extra * y_plus,
    GRB.MINIMIZE
)

# -------------------------
# Restricciones
# -------------------------

# Capacidad: x_ij <= Q * n_ij
for i in I:
    for j in J:
        m3.addConstr(x[i, j] <= Q * n[i, j],
                     name=f"cap_{i}_{j}")

# Oferta con almacén activado: sum_j x_ij <= s_i * z_i
for i in I:
    m3.addConstr(
        gp.quicksum(x[i, j] for j in J) <= s[i] * z[i],
        name=f"oferta_{i}"
    )

# Demanda: sum_i x_ij = d_j
for j in J:
    m3.addConstr(
        gp.quicksum(x[i, j] for i in I) == d[j],
        name=f"demanda_{j}"
    )

# Límite canales: sum n_ij <= 4 + y_plus
m3.addConstr(
    gp.quicksum(n[i, j] for i in I for j in J) <= 4 + y_plus,
    name="limite_canales"
)

# Privacidad Berlín: y_A2 + y_B2 <= 1
m3.addConstr(
    y["A", "2"] + y["B", "2"] <= 1,
    name="privacidad_Berlin"
)

# Enlace n_ij - y_ij: n_ij <= 5 y_ij
for i in I:
    for j in J:
        m3.addConstr(
            n[i, j] <= max_canales_par * y[i, j],
            name=f"enlace_{i}_{j}"
        )

# -------------------------
# Optimización y salida
# -------------------------

m3.optimize()

if m3.status == GRB.OPTIMAL:
    print("\n--- Pregunta 3 ---")
    print(f"Coste mínimo = {m3.objVal:.2f} €")
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
    for i in I:
        print(f"z[{i}] = {int(z[i].X)}")
    print("\nPares activos y_ij:")
    for i in I:
        for j in J:
            if y[i, j].X > 0.5:
                print(f"y[{i},{j}] = 1")
    print(f"\ny_plus = {int(y_plus.X)}")
else:
    print("No se encontró solución óptima en P3.")
