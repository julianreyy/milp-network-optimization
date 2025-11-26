
# PREGUNTA 3 

import gurobipy as gp
from gurobipy import GRB

# -------------------------
# Conjuntos
# -------------------------

I = ["A", "B", "C"]          # Orígenes: Lisboa, Madrid, Turín
J = ["1", "2", "3"]        # Destinos: París, Berlín, Varsovia

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

Q = 10       
F = 50    
G = 5000    
F_extra = 15 
max_canales_par = 5

# -------------------------
# Modelo y variables
# -------------------------

m = gp.Model("P3_de_modelo")

# Cantidad de datos (mil Gb)
x = m.addVars(I, J, lb=0.0, name="x")              

# Canales activos (par i,j)
y = m.addVars(I, J, vtype=GRB.BINARY, name="y")   

# Nº canales entre i y j
n = m.addVars(I, J, vtype=GRB.INTEGER, lb=0, name="n")

# Activación de almacén i
z = m.addVars(I, vtype=GRB.BINARY, name="z")          

# Canal adicional
y_plus = m.addVar(vtype=GRB.BINARY, name="y_plus")

# -------------------------
# Función objetivo
# -------------------------

m.setObjective(
    gp.quicksum(c[i, j] * x[i, j] for i in I for j in J)
    + F * gp.quicksum(n[i, j] for i in I for j in J)
    + G * gp.quicksum(z[i] for i in I)
    + F_extra * y_plus,
    GRB.MINIMIZE
)

# -------------------------
# Restricciones
# -------------------------

# Capacidad del canal
for i in I:
    for j in J:
        m.addConstr(
            x[i, j] <= Q * n[i, j],
            name=f"cap_{i}_{j}"
        )

#Oferta de cada almacén:
for i in I:
    m.addConstr(
        gp.quicksum(x[i, j] for j in J) <= s[i] * z[i],
        name=f"oferta_{i}"
    )

# Demanda de cada destino: 
for j in J:
    m.addConstr(
        gp.quicksum(x[i, j] for i in I) <= d[j],
        name=f"demanda_{j}"
    )

#Límite del número de canales
m.addConstr(
    gp.quicksum(n[i, j] * y[i, j] for i in I for j in J) <= 4 + y_plus,
    name="limite_canales"
)

# Privacidad de Berlín
m.addConstr(
    y["A", "2"] + y["B", "2"] <= 1,
    name="privacidad_Berlin"
)

# Canales máximos por sistema
for i in I:
    for j in J:
        m.addConstr(
            n[i, j] <= max_canales_par * y[i, j],
            name=f"enlace_{i}_{j}"
        )

# -------------------------
# Optimización y salida
# -------------------------

m.optimize()

if m.status == GRB.OPTIMAL:
    print("\n--- Pregunta 3 ---")
    print(f"Coste mínimo = {m.objVal:.2f} €")
    
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

    print("\nPares activos y_ij:")
    for i in I:
        for j in J:
            if y[i, j].X > 0.5:
                print(f"y[{i},{j}] = 1")

    print("\nAlmacenes activos z_i:")
    for i in I:
        print(f"z[{i}] = {int(z[i].X)}")

    print(f"\ny_plus = {int(y_plus.X)}")
else:
    print("No se encontró solución óptima")
