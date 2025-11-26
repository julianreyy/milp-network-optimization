# PREGUNTA 2

import gurobipy as gp
from gurobipy import GRB

# -------------------------
# Conjuntos
# -------------------------

I = ["A", "B", "C"]   # Orígenes: Lisboa, Madrid, Turín
J = ["1", "2", "3"]   # Destinos: París, Berlín, Varsovia

# -------------------------
# Parámetros
# -------------------------

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

# Pasamos a €/MilGb
c = {(i, j): cents[i, j] / 100.0 for (i, j) in cents}

Q = 10        # capacidad de cada canal (mil Gb)
F = 50        # coste fijo por canal
F_extra = 15  # sobrecoste si se usa el 5 canal
max_canales_par = 5  # tope de canales por par 

# -------------------------
# Modelo y variables
# -------------------------

m = gp.Model("P2_tu_modelo")

# datos enviados de i a j (mil Gb)
x = m.addVars(I, J, lb=0.0, name="x")

# 1 si el par (i,j) está activo
y = m.addVars(I, J, vtype=GRB.BINARY, name="y")

# 1 si se usa el canal extra
y_plus = m.addVar(vtype=GRB.BINARY, name="y_plus")

# número de canales abiertos entre i y j
n = m.addVars(I, J, vtype=GRB.INTEGER, lb=0, name="n")

# -------------------------
# Función objetivo
# -------------------------

m.setObjective(
    gp.quicksum(c[i, j] * x[i, j] for i in I for j in J)
    + F * gp.quicksum(n[i, j] for i in I for j in J)
    + F_extra * y_plus,
    GRB.MINIMIZE
)

# -------------------------
# Restricciones
# -------------------------

# Capacidad de los canales
for i in I:
    for j in J:
        m.addConstr(x[i, j] <= Q * n[i, j],
                    name=f"cap_{i}_{j}")

# Oferta en cada origen
for i in I:
    m.addConstr(
        gp.quicksum(x[i, j] for j in J) <= s[i],
        name=f"oferta_{i}"
    )

# Demanda en cada destino
for j in J:
    m.addConstr(
        gp.quicksum(x[i, j] for i in I) == d[j],
        name=f"demanda_{j}"
    )

# Número total de canales
m.addConstr(
    gp.quicksum(n[i, j] for i in I for j in J) <= 4 + y_plus,
    name="limite_canales"
)

# Restricción de privacidad en Berlín
m.addConstr(
    y["A", "2"] + y["B", "2"] <= 1,
    name="privacidad_Berlin"
)

# Relación entre canales y par activo
for i in I:
    for j in J:
        m.addConstr(
            n[i, j] <= max_canales_par * y[i, j],
            name=f"enlace_{i}_{j}"
        )

# IIntegridad de Canales
sum_y = gp.quicksum(y[i, j] for i in I for j in J)
sum_n = gp.quicksum(n[i, j] for i in I for j in J)
m.addConstr(
    sum_y - sum_n == 0,
    name="igual_suma_y_n"
)

# -------------------------
# Optimización y salida
# -------------------------

m.optimize()

if m.status == GRB.OPTIMAL:
    print("\n--- Pregunta 2")
    print(f"Coste mínimo = {m.objVal:.2f} €")

    print("\nFlujos x_ij:")
    for i in I:
        for j in J:
            if x[i, j].X > 1e-6:
                print(f"x[{i},{j}] = {x[i, j].X:.2f}")

    print("\nNúmero de canales:")
    for i in I:
        for j in J:
            if n[i, j].X > 0.5:
                print(f"n[{i},{j}] = {int(round(n[i, j].X))}")

    print("\nPares activos:")
    for i in I:
        for j in J:
            if y[i, j].X > 0.5:
                print(f"y[{i},{j}] = 1")

    print(f"\ny_plus = {int(y_plus.X)}")

else:
    print("No se encontró solución óptima")
