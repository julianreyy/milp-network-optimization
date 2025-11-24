# ============================================
# PREGUNTA 1 - MODELO BASE
# ============================================

import gurobipy as gp
from gurobipy import GRB

# -------------------------
# Datos
# -------------------------

I = ["A", "B", "C"]          # Orígenes: A=Lisboa, B=Madrid, C=Turín
J = ["1", "2", "3"]          # Destinos: 1=París, 2=Berlín, 3=Varsovia

# Oferta (mil Gb)
s = {"A": 5, "B": 6, "C": 7}

# Demanda (mil Gb)
d = {"1": 4, "2": 5, "3": 9}

# Costes variables en céntimos €/MilGb
cents = {
    ("A", "1"): 4, ("A", "2"): 3, ("A", "3"): 6,
    ("B", "1"): 7, ("B", "2"): 4, ("B", "3"): 9,
    ("C", "1"): 9, ("C", "2"): 5, ("C", "3"): 2,
}

# Conversión a €/MilGb
c = {(i, j): cents[i, j] / 100.0 for (i, j) in cents}

Q = 10        # mil Gb por canal
F = 50        # coste fijo por canal
F_extra = 15  # recargo si usamos el 5º canal (pasa a 65)

# -------------------------
# Modelo y variables
# -------------------------

m1 = gp.Model("P1_ModeloBase")

x = m1.addVars(I, J, lb=0.0, name="x")                # x_ij
y = m1.addVars(I, J, vtype=GRB.BINARY, name="y")      # y_ij
y_plus = m1.addVar(vtype=GRB.BINARY, name="y_plus")   # y^+

# -------------------------
# Función objetivo
# -------------------------

m1.setObjective(
    gp.quicksum(c[i, j] * x[i, j] for i in I for j in J)
    + F * gp.quicksum(y[i, j] for i in I for j in J)
    + F_extra * y_plus,
    GRB.MINIMIZE
)

# -------------------------
# Restricciones
# -------------------------

# Capacidad de cada canal: x_ij <= Q * y_ij
for i in I:
    for j in J:
        m1.addConstr(x[i, j] <= Q * y[i, j],
                     name=f"cap_{i}_{j}")

# Oferta de cada almacén: sum_j x_ij <= s_i
for i in I:
    m1.addConstr(
        gp.quicksum(x[i, j] for j in J) <= s[i],
        name=f"oferta_{i}"
    )

# Demanda de cada destino: sum_i x_ij = d_j
for j in J:
    m1.addConstr(
        gp.quicksum(x[i, j] for i in I) == d[j],
        name=f"demanda_{j}"
    )

# Límite número de canales: sum y_ij <= 4 + y_plus
m1.addConstr(
    gp.quicksum(y[i, j] for i in I for j in J) <= 4 + y_plus,
    name="limite_canales"
)

# Privacidad Berlín: y_A2 + y_B2 <= 1
m1.addConstr(
    y["A", "2"] + y["B", "2"] <= 1,
    name="privacidad_Berlin"
)

# -------------------------
# Optimización y salida
# -------------------------

m1.optimize()

if m1.status == GRB.OPTIMAL:
    print("\n--- Pregunta 1 ---")
    print(f"Coste mínimo = {m1.objVal:.2f} €")
    print("\nFlujos x_ij (mil Gb):")
    for i in I:
        for j in J:
            if x[i, j].X > 1e-6:
                print(f"x[{i},{j}] = {x[i, j].X:.2f}")
    print("\nCanales activos y_ij:")
    for i in I:
        for j in J:
            if y[i, j].X > 0.5:
                print(f"y[{i},{j}] = 1")
    print(f"\ny_plus = {int(y_plus.X)}")
else:
    print("No se encontró solución óptima en P1.")
