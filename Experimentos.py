"""Repite la comparación de trayectorias y exporta una fila por agente y corrida."""

import csv
from pathlib import Path

from Simulacion import TRAYECTORIAS, simular


def main():
    destino = Path(__file__).resolve().parent / "output"
    destino.mkdir(exist_ok=True)
    resultados = []
    for trayectoria in TRAYECTORIAS:
        for cantidad in (1, 4):
            for semilla in range(42, 52):
                carpeta = None
                if trayectoria == "zigzag" and semilla == 42:
                    carpeta = destino / "demo" / ("individual" if cantidad == 1 else "multiple")
                _, datos = simular(
                    semilla=semilla, cantidad_agentes=cantidad, trayectoria=trayectoria,
                    carpeta_salida=carpeta, devolver_estadisticas=True,
                )
                agentes = datos.pop("agentes")
                datos["cantidad_agentes"] = cantidad
                datos["inicio"] = str(datos["inicio"])
                resultados.extend({**datos, **agente} for agente in agentes)

    with (destino / "resultados.csv").open("w", newline="", encoding="utf-8-sig") as archivo:
        escritor = csv.DictWriter(archivo, fieldnames=list(resultados[0]))
        escritor.writeheader()
        escritor.writerows(resultados)


if __name__ == "__main__":
    main()
