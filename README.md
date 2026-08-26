## Enunciado

Práctica de la asignatura *Investigación Operativa* (Grado en Ingeniería del 
Software), resuelta con GurobiPy.

La empresa ficticia *DataMind Labs* necesita distribuir datos desde 3 almacenes 
de origen (Lisboa, Madrid, Turín) hacia 3 centros de cómputo de destino 
(París, Berlín, Varsovia), minimizando el coste total de transferencia.

El coste total combina:
- **Costes variables**, según la cantidad de datos enviada por cada ruta.
- **Costes fijos**, por activar cada canal de transferencia utilizado.

### Restricciones del problema
- Cada canal tiene una capacidad máxima de transferencia.
- Activar un canal implica un coste fijo; hay un número limitado de canales 
  disponibles, ampliable pagando un coste extra por uno adicional.
- Restricción de privacidad: un destino concreto no puede recibir datos de 
  dos orígenes distintos al mismo tiempo.

### Extensiones del modelo
El ejercicio parte de un modelo base y lo va ampliando en sucesivas preguntas:
1. **Modelo base**: un único canal por par origen-destino.
2. **Múltiples canales**: permitir más de un canal entre un mismo par.
3. **Coste de activación por origen**: activar un almacén conlleva un coste fijo adicional.
4. **Nodo de transbordo**: se añade un nodo intermedio (Zúrich) que puede 
   recibir y reenviar datos, con restricciones de balance de flujo y un 
   mínimo de envío si el canal se activa.

### Objetivo
Formular y resolver, en cada extensión, un modelo de **Programación Lineal 
Entera Mixta (MILP)** que minimice el coste total de transferencia.
