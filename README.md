# A3 · Limpieza de una habitación

Instala las dependencias desde esta carpeta.

```powershell
python -m pip install -r requirements.txt
```

## Simular y reproducir

```powershell
python Simulacion.py --agentes 1 --trayectoria zigzag --filas 8 --columnas 8 --suciedad 40 --obstaculos 10 --tiempo 500 --semilla 42 --salida output/demo/individual
python Simulacion.py --agentes 4 --trayectoria zigzag --filas 8 --columnas 8 --suciedad 40 --obstaculos 10 --tiempo 500 --semilla 42 --salida output/demo/multiple
python main.py --datos output/demo/individual
```

Abre http://127.0.0.1:5000. Para ver la corrida colectiva, detén el servidor y ejecútalo con `--datos output/demo/multiple`. El visor permite pausar, reiniciar, cambiar la velocidad y recorrer los episodios.

Las trayectorias disponibles son `aleatoria`, `zigzag`, `local` y `espiral`. El límite de tiempo se mide en episodios de la simulación. Cada corrida exporta `Nodes.csv`, `Routes.csv` y `Estadisticas.json`. En el resumen, el último episodio activo de un agente indica su última acción de movimiento, limpieza o carga. El valor 0 indica que no realizó ninguna de esas acciones.

## Repetir el experimento del informe

```powershell
python Experimentos.py
```

El script ejecuta 80 corridas y genera `output/resultados.csv` con una fila por agente y corrida. Las métricas globales se repiten para los agentes de una misma corrida. Para calcular promedios por escenario, toma una sola fila por combinación de trayectoria, cantidad de agentes y semilla (por ejemplo, la fila del agente 1). El script también exporta las dos reproducciones correspondientes a zigzag con semilla 42.
