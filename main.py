"""Sirve una corrida exportada y su reproducción en el navegador."""

import argparse
import ast
import csv
import json
from pathlib import Path

import flask

app = flask.Flask(__name__)
BASE = Path(__file__).resolve().parent
app.config["CARPETA_DATOS"] = BASE


def load_nodes(carpeta=BASE):
    nodes = {}
    with (carpeta / "Nodes.csv").open(newline="", encoding="utf-8") as archivo:
        for row in csv.DictReader(archivo):
            node = int(row["Node"])
            nodes[node] = {
                "node": node,
                "point": ast.literal_eval(row["Points"]),
                "dirt": int(row["Dirt"]),
                "clean_tick": int(row.get("CleanTick", -1)),
                "obstacle": int(row.get("Obstacle", 0)),
                "station": int(row.get("Station", 0)),
            }
    return nodes


def load_routes(carpeta=BASE):
    routes = {}
    with (carpeta / "Routes.csv").open(newline="", encoding="utf-8") as archivo:
        for row in csv.DictReader(archivo):
            agent = int(row["Agent"])
            routes.setdefault(agent, []).append(int(row["Node"]))
    return routes


@app.route("/")
def index():
    return flask.render_template("index.html")


@app.route("/api/data")
def data():
    carpeta = app.config["CARPETA_DATOS"]
    try:
        nodes = load_nodes(carpeta)
        routes = load_routes(carpeta)
    except FileNotFoundError:
        return flask.jsonify(error="Genera los datos de la corrida con Simulacion.py."), 404

    estadisticas = carpeta / "Estadisticas.json"
    resumen = json.loads(estadisticas.read_text(encoding="utf-8")) if estadisticas.is_file() else None
    return flask.jsonify(nodes=nodes, routes=routes, resumen=resumen)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--datos", type=Path, default=BASE)
    parser.add_argument("--puerto", type=int, default=5000)
    args = parser.parse_args()
    app.config["CARPETA_DATOS"] = args.datos
    app.run(port=args.puerto)
