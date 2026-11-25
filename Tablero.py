import numpy


def crear_tablero(filas, columnas, porcentaje_obstaculos, porcentaje_suciedad, semilla):
    # Se reservan [0,0] para varios agentes y [1,1] para un agente.
    if filas < 2 or columnas < 2:
        raise ValueError("El tablero debe tener al menos 2 filas y 2 columnas.")

    if not 0 <= porcentaje_obstaculos <= 100:
        raise ValueError("El porcentaje de obstáculos debe estar entre 0 y 100.")

    if not 0 <= porcentaje_suciedad <= 100:
        raise ValueError("El porcentaje de suciedad debe estar entre 0 y 100.")

    rng = numpy.random.default_rng(semilla)

    # Crear la habitación de M filas por N columnas.
    # En matriz: 1 = piso libre, 0 = obstáculo.
    matriz = numpy.ones((filas, columnas), dtype=int)

    # Identificadores de las celdas: desde 0 hasta matriz.size - 1.
    # En states[origen, destino]: 1 = movimiento permitido.
    states = numpy.zeros((matriz.size, matriz.size), dtype=numpy.uint8)

    # Colocar obstáculos en ubicaciones aleatorias.
    # Las posiciones iniciales de ambos escenarios deben quedar libres.
    inicio_multiple = 0
    inicio_individual = numpy.ravel_multi_index((1, 1), matriz.shape)

    celdas_disponibles = [
        celda for celda in range(matriz.size)
        if celda not in (inicio_multiple, inicio_individual)
    ]

    cantidad_obstaculos = round(matriz.size * porcentaje_obstaculos / 100)

    if cantidad_obstaculos > len(celdas_disponibles):
        raise ValueError("Hay demasiados obstáculos para dejar libres las posiciones iniciales.")

    obstaculos = rng.choice(
        celdas_disponibles, size=cantidad_obstaculos, replace=False
    )

    for celda in obstaculos:
        fila, columna = numpy.unravel_index(celda, matriz.shape)
        matriz[fila, columna] = 0

    # Construir las conexiones entre celdas libres.
    for m in range(filas):
        for n in range(columnas):
            if matriz[m, n] == 0:
                continue

            origen = numpy.ravel_multi_index((m, n), matriz.shape)

            # x cambia la fila; y cambia la columna.
            # Por ejemplo, (-1, -1) significa arriba a la izquierda.
            for x in [-1, 0, 1]:
                for y in [-1, 0, 1]:
                    if x == 0 and y == 0:
                        continue

                    nueva_fila = m + x
                    nueva_columna = n + y

                    if not (0 <= nueva_fila < filas and 0 <= nueva_columna < columnas):
                        continue

                    if matriz[nueva_fila, nueva_columna] == 0:
                        continue

                    destino = numpy.ravel_multi_index(
                        (nueva_fila, nueva_columna), matriz.shape
                    )
                    states[origen, destino] = 1

    # Colocar suciedad únicamente sobre piso libre.
    # En suciedad: 1 = celda sucia, 0 = sin suciedad.
    suciedad = numpy.zeros((filas, columnas), dtype=int)
    celdas_libres = numpy.flatnonzero(matriz == 1)

    cantidad_sucias = round(len(celdas_libres) * porcentaje_suciedad / 100)
    celdas_sucias = rng.choice(
        celdas_libres, size=cantidad_sucias, replace=False
    )

    for celda in celdas_sucias:
        fila, columna = numpy.unravel_index(celda, matriz.shape)
        suciedad[fila, columna] = 1

    return matriz, states, suciedad
