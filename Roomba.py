#Funcionamiento de una aspiradora con posición, obstáculos y acciones
#Agente que va a recorrer el cuarto basicamente

from collections import deque 

class Roomba:
    def __init__(self, estacion_inicial):
        self.estacion_inicial = estacion_inicial #debe saber a donde regresar
        self.posicion = estacion_inicial
        self.bateria = 100
        self.movimientos = 0
        self.regresando = False #Para múltiple agentes cada uno debe tener su estado, regresando o sigue limpiando
        self.celdas_limpiadas = 0
        self.estaciones_conocidas = {estacion_inicial} #default siempre se van a saber su estación incial, después sumas por las que pasan en el conjunto

    def mover(self, destino, states): #para moverse debe tener batería y no ser un obstáculo
        if not 0 <= destino < states.shape[1]:
            return False

        if self.bateria < 1 or states[self.posicion, destino] == 0: 
            return False

        self.posicion = destino
        self.bateria -= 1 #Se resta 1 a la batería por haber realizado el movimiento
        self.movimientos += 1
        return True

    def limpiar(self, suciedad):
        if self.bateria < 1 or suciedad.flat[self.posicion] == 0:
            return False

        suciedad.flat[self.posicion] = 0
        self.bateria -= 1
        self.celdas_limpiadas += 1
        return True

    #BFS, consulta los alrededores hasta encontrar una estación que ya conozca
    def ruta_a_estacion(self, states, origen=None):
        if origen is None:
            origen = self.posicion

        pendientes = deque([origen]) #Si avanzaras a tal celda, cauntos pasos necesitarías para regresar
        anterior = {origen: None}

        while pendientes:
            actual = pendientes.popleft()

            if actual in self.estaciones_conocidas:
                ruta = []
                while anterior[actual] is not None:
                    ruta.append(actual)
                    actual = anterior[actual]

                ruta.reverse()
                return ruta

            for vecino in states[actual].nonzero()[0]:
                if vecino not in anterior:
                    anterior[vecino] = actual
                    pendientes.append(vecino)

        return None

    #Cada llamada que pasa en la estación sube 5 de carga
    def recargar(self):
        if self.posicion not in self.estaciones_conocidas or self.bateria >= 100:
            return False

        self.bateria = min(100, self.bateria + 5)
        return True

if __name__ == "__main__":
    from Tablero import crear_tablero
    #default
    matriz, states, suciedad = crear_tablero(
        filas=8,
        columnas=8,
        porcentaje_obstaculos=10,
        porcentaje_suciedad=40,
        semilla=42
    )
    roomba = Roomba(estacion_inicial=0)

    # Intentar llegar de una sola vez a la esquina opuesta.
    print("¿Pudo ir directo a 293?", roomba.mover(293, states))

    # Buscar los vecinos que siguen disponibles después de colocar obstáculos.
    vecinos = states[roomba.posicion].nonzero()[0]
    print("Vecinos disponibles:", vecinos)

    if vecinos.size > 0:
        destino = vecinos[0]
        roomba.mover(destino, states)

    print("Posición final:", roomba.posicion)
    print("Batería:", roomba.bateria, "%")
    print("Movimientos:", roomba.movimientos)