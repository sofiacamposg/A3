"""Ejecuta la limpieza por episodios y exporta la reproducción y sus métricas."""

import argparse
import csv
import json
from collections import deque
from pathlib import Path

import numpy

from Roomba import Roomba
from Tablero import crear_tablero

BASE = Path(__file__).resolve().parent
TRAYECTORIAS = ("aleatoria", "zigzag", "local", "espiral")


def guardar_resultados(carpeta, matriz, suciedad, inicio, rutas, limpieza, resumen):
    """Conserva el formato de los CSV que consume el visor."""
    carpeta.mkdir(parents=True, exist_ok=True)
    with (carpeta / "Nodes.csv").open("w", newline="", encoding="utf-8") as archivo:
        escritor = csv.writer(archivo)
        escritor.writerow(["Node", "Points", "Dirt", "Obstacle", "Station", "CleanTick"])
        for celda in range(matriz.size):
            fila, columna = divmod(celda, matriz.shape[1])
            escritor.writerow([
                celda, (columna, fila, 0), int(suciedad.flat[celda]),
                int(matriz.flat[celda] == 0), int(celda == inicio),
                limpieza.get(celda, -1),
            ])

    with (carpeta / "Routes.csv").open("w", newline="", encoding="utf-8") as archivo:
        escritor = csv.writer(archivo)
        escritor.writerow(["Agent", "Node", "Tick"])
        for agente, ruta in enumerate(rutas, start=1):
            escritor.writerows((agente, celda, tick) for tick, celda in enumerate(ruta))

    (carpeta / "Estadisticas.json").write_text(
        json.dumps(resumen, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )


def orden_barrido(filas, columnas, trayectoria):
    if trayectoria == "zigzag":
        return [
            fila * columnas + columna
            for fila in range(filas)
            for columna in (range(columnas) if fila % 2 == 0
                            else range(columnas - 1, -1, -1))
        ]

    orden = []
    arriba, abajo = 0, filas - 1
    izquierda, derecha = 0, columnas - 1
    while arriba <= abajo and izquierda <= derecha:
        orden.extend(arriba * columnas + c for c in range(izquierda, derecha + 1))
        arriba += 1
        orden.extend(f * columnas + derecha for f in range(arriba, abajo + 1))
        derecha -= 1
        if arriba <= abajo:
            orden.extend(abajo * columnas + c for c in range(derecha, izquierda - 1, -1))
            abajo -= 1
        if izquierda <= derecha:
            orden.extend(f * columnas + izquierda for f in range(abajo, arriba - 1, -1))
            izquierda += 1
    return orden


def mapa_caminos(origen, vecinos, bloqueadas=()):
    """Encuentra la distancia y el primer paso de cada camino mínimo."""
    caminos = {origen: (0, origen)}
    pendientes = deque([origen])
    while pendientes:
        actual = pendientes.popleft()
        distancia, paso = caminos[actual]
        for destino in vecinos[actual]:
            if destino not in caminos and destino not in bloqueadas:
                caminos[destino] = (distancia + 1, destino if distancia == 0 else paso)
                pendientes.append(destino)
    return caminos


def elegir_destino(origen, vecinos, ocupadas, visitas, trayectoria, orden, regreso, bateria, rng):
    # Se reserva energía para el regreso y para limpiar en el destino.
    posibles = [
        celda for celda in vecinos[origen]
        if celda not in ocupadas and bateria >= regreso[celda][0] + 2
    ]
    if not posibles:
        return None
    if trayectoria == "aleatoria":
        return rng.choice(posibles)
    if trayectoria == "local":
        return min(posibles, key=visitas.__getitem__)

    caminos = mapa_caminos(origen, vecinos, ocupadas)
    for celda in orden:
        if celda in caminos and visitas[celda] == 0 and caminos[celda][1] in posibles:
            return caminos[celda][1]
    return min(posibles, key=visitas.__getitem__)


def simular(
    tiempo_maximo=500, semilla=42, cantidad_agentes=1, trayectoria="aleatoria",
    filas=8, columnas=8, porcentaje_obstaculos=10, porcentaje_suciedad=40,
    carpeta_salida=BASE, *, devolver_estadisticas=False,
):
    """Devuelve las rutas y, si se solicita, las estadísticas de la corrida."""
    if tiempo_maximo < 0:
        raise ValueError("El tiempo máximo debe ser mayor o igual a cero.")
    if cantidad_agentes < 1:
        raise ValueError("Se requiere al menos un agente.")
    if trayectoria not in TRAYECTORIAS:
        raise ValueError("Trayectoria no reconocida.")

    rng = numpy.random.default_rng(semilla)
    matriz, conexiones, suciedad = crear_tablero(
        filas, columnas, porcentaje_obstaculos, porcentaje_suciedad, semilla
    )
    inicio = columnas + 1 if cantidad_agentes == 1 else 0
    vecinos = [tuple(map(int, numpy.flatnonzero(fila))) for fila in conexiones]
    regreso = mapa_caminos(inicio, vecinos)
    orden = orden_barrido(filas, columnas, trayectoria) if trayectoria in ("zigzag", "espiral") else []
    roombas = [Roomba(inicio) for _ in range(cantidad_agentes)]
    rutas = [[inicio] for _ in roombas]
    visitas = numpy.zeros(matriz.size, dtype=int)
    visitas[inicio] = 1

    piso = suciedad.copy()
    limpieza = {}
    ultimas_acciones = [0] * cantidad_agentes
    total_sucias = int(suciedad.sum())
    episodio = 0

    while episodio < tiempo_maximo and len(limpieza) < total_sucias:
        episodio += 1
        # La estación admite a todos los agentes. El resto del piso tiene cupo de uno.
        ocupadas = {r.posicion for r in roombas if r.posicion != inicio}
        turnos = sorted(rng.permutation(cantidad_agentes), key=lambda i: not roombas[i].regresando)
        for indice in turnos:
            if len(limpieza) == total_sucias:
                break

            roomba = roombas[indice]
            origen = roomba.posicion
            destino = None
            distancia = regreso[origen][0]
            if roomba.regresando or roomba.bateria <= distancia + 1:
                roomba.regresando = True
                if origen == inicio:
                    if roomba.recargar():
                        ultimas_acciones[indice] = episodio
                    roomba.regresando = roomba.bateria < 100
                else:
                    camino = mapa_caminos(origen, vecinos, ocupadas).get(inicio)
                    if camino and camino[0] <= roomba.bateria:
                        destino = camino[1]
            elif piso.flat[origen]:
                if roomba.limpiar(piso):
                    limpieza[origen] = episodio
                    ultimas_acciones[indice] = episodio
            else:
                destino = elegir_destino(
                    origen, vecinos, ocupadas, visitas, trayectoria, orden,
                    regreso, roomba.bateria, rng,
                )
                if destino is None and not ocupadas.intersection(vecinos[origen]):
                    roomba.regresando = roomba.bateria < 100

            if destino is not None and roomba.mover(destino, conexiones):
                ocupadas.discard(origen)
                if destino != inicio:
                    ocupadas.add(destino)
                visitas[destino] += 1
                ultimas_acciones[indice] = episodio

        for roomba, ruta in zip(roombas, rutas):
            ruta.append(roomba.posicion)

    celdas_libres = int(matriz.sum())
    restantes = total_sucias - len(limpieza)
    resumen = {
        "filas": filas, "columnas": columnas, "semilla": semilla,
        "trayectoria": trayectoria, "tiempo_maximo": tiempo_maximo,
        "inicio": list(divmod(inicio, columnas)),
        "episodios": episodio, "fin": "limpio" if restantes == 0 else "tiempo_maximo",
        "piso": celdas_libres, "obstaculos": matriz.size - celdas_libres,
        "sucias_iniciales": total_sucias, "sucias_restantes": restantes,
        "porcentaje_limpio": 100 * (celdas_libres - restantes) / celdas_libres,
        "movimientos_equipo": sum(r.movimientos for r in roombas),
        "agentes": [
            {"agente": indice, "movimientos": r.movimientos,
             "celdas_limpiadas": r.celdas_limpiadas, "bateria_final": r.bateria,
             "ultimo_episodio_activo": ultima,
             "aporte_porcentaje_piso": 100 * r.celdas_limpiadas / celdas_libres}
            for indice, (r, ultima) in enumerate(zip(roombas, ultimas_acciones), start=1)
        ],
    }

    if carpeta_salida is not None:
        guardar_resultados(Path(carpeta_salida), matriz, suciedad, inicio, rutas, limpieza, resumen)
    return (rutas, resumen) if devolver_estadisticas else rutas


def main():
    parser = argparse.ArgumentParser(description="Simulación de limpieza con Roombas")
    parser.add_argument("--agentes", type=int, default=1)
    parser.add_argument("--trayectoria", choices=TRAYECTORIAS, default="aleatoria")
    parser.add_argument("--tiempo", type=int, default=500, help="Límite en episodios")
    parser.add_argument("--filas", type=int, default=8)
    parser.add_argument("--columnas", type=int, default=8)
    parser.add_argument("--suciedad", type=float, default=40)
    parser.add_argument("--obstaculos", type=float, default=10)
    parser.add_argument("--semilla", type=int, default=42)
    parser.add_argument("--salida", type=Path, default=BASE)
    args = parser.parse_args()
    try:
        _, resumen = simular(
            args.tiempo, args.semilla, args.agentes, args.trayectoria,
            args.filas, args.columnas, args.obstaculos, args.suciedad,
            args.salida, devolver_estadisticas=True,
        )
    except ValueError as error:
        parser.error(str(error))
    print(json.dumps(resumen, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
