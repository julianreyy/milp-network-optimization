# PREGUNTA 4


import gurobipy as gp
from gurobipy import GRB

# -------------------------
# Conjuntos
# -------------------------

I = ["A", "B", "C", "T"]      # Orígenes: A,B,C,T
J = ["1", "2", "3", "4"]      # Destinos: 1=París, 2=Berlín, 3=Varsovia, 4=Zúrich

I_almacenes = ["A", "B", "C"]   
J_destinos = ["1", "2", "3"] 

# -------------------------
# Parámetros
# -------------------------

# Oferta (mil Gb) en los almacenes
s = {"A": 5, "B": 6, "C": 7}

# Demanda (mil Gb) en los destinos finales
d = {"1": 4, "2": 5, "3": 9}


cents_direct = {
    ("A", "1"): 4, ("A", "2"): 3, ("A", "3"): 6,
    ("B", "1"): 7, ("B", "2"): 4, ("B", "3"): 9,
    ("C", "1"): 9, ("C", "2"): 5, ("C", "3"): 2,
}

c = {}

# Directos A,B,C -> 1,2,3
for (i, j), cij in cents_direct.items():
    c[(i, j)] = cij / 100.0


for i in I_almacenes:
    c[(i, "4")] = 0.05      # i -> Zúrich

for j in J_destinos:
    c[("T", j)] = 0.05      # Zúrich -> j

# Para el resto de pares
for i in I:
    for j in J:
        if (i, j) not in c:
            c[(i, j)] = 0.0

Q = 10       
F = 50  
G = 5000  
F_extra = 15 
max_canales_par = 5 

# -------------------------
# Modelo y variables
# -------------------------

m = gp.Model("P4_modelo")

# Cantidad de datos (mil Gb)
x = m.addVars(I, J, lb=0.0, name="x")         

# nº de canales entre i y j
n = m.addVars(I, J, vtype=GRB.INTEGER, lb=0, name="n")

# par (i,j) activo
y = m.addVars(I, J, vtype=GRB.BINARY, name="y")  

# almacenes activados
z = m.addVars(I_almacenes, vtype=GRB.BINARY, name="z")

# canal adicional
y_plus = m.addVar(vtype=GRB.BINARY, name="y_plus")

# -------------------------
# Función objetivo
# -------------------------

m.setObjective(
    gp.quicksum(c[(i, j)] * x[i, j] for i in I for j in J)
    + F * gp.quicksum(n[i, j] for i in I for j in J)
    + G * gp.quicksum(z[i] for i in I_almacenes)
    + F_extra * y_plus,
    GRB.MINIMIZE
)

# -------------------------
# Restricciones
# -------------------------

# Capacidad del canal
for i in I:
    for j in J:
        m.addConstr(x[i, j] <= Q * n[i, j],
                    name=f"cap_{i}_{j}")

# Oferta de cada almacén
for i in I_almacenes:
    m.addConstr(
        gp.quicksum(x[i, j] for j in J) <= s[i] * z[i],
        name=f"oferta_{i}"
    )

# Demanda de cada destino 
for j in J_destinos:
    m.addConstr(
        gp.quicksum(x[i, j] for i in I) == d[j],
        name=f"demanda_{j}"
    )

# Límite del número total de canales
m.addConstr(
    gp.quicksum(n[i, j] * y[i, j] for i in I for j in J) <= 4 + y_plus,
    name="limite_canales"
)

#Privacidad en Berlín
m.addConstr(
    y["A", "2"] + y["B", "2"] <= 1,
    name="privacidad_Berlin"
)

#Canales máximos por par y enlace
for i in I:
    for j in J:
        m.addConstr(
            n[i, j] <= max_canales_par * y[i, j],
            name=f"enlace_{i}_{j}"
        )

# Zúrich no se envía a sí mismo
m.addConstr(x["T", "4"] == 0, name="zurich_mismo_flujo")
m.addConstr(n["T", "4"] == 0, name="zurich_mismo_canales")

#Balance en Zúrich: entrada = salida

m.addConstr(
    gp.quicksum(x[i, "4"] for i in I_almacenes)
    == gp.quicksum(x["T", j] for j in J_destinos),
    name="balance_Zurich"
)

# Mínimo flujo Zúrich
m.addConstr(
    x["T", "1"] >= 0.5 * y["T", "1"],
    name="min_flujo_T_Paris"
)

# -------------------------
# Optimización y salida
# -------------------------

m.optimize()

if m.status == GRB.OPTIMAL:
    print("\n--- Pregunta 4 ---")
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
    for i in I_almacenes:
        print(f"z[{i}] = {int(z[i].X)}")

    print(f"\ny_plus = {int(y_plus.X)}")

else:
    print("No se encontró solución óptima")