import gurobipy as gp
from gurobipy import GRB

print("Versión Gurobi:", gp.gurobi.version())

m = gp.Model("demo")
x = m.addVar(lb=0, name="x")
y = m.addVar(lb=0, name="y")

m.setObjective(x + y, GRB.MAXIMIZE)
m.addConstr(x + 2*y <= 4, "c1")
m.addConstr(3*x + y <= 5, "c2")

m.optimize()

for v in m.getVars():
    print(v.VarName, round(v.X, 4))
print("Obj =", round(m.ObjVal, 4))

##FUNCIONA!##