const canvas = document.getElementById("tablero");
const ctx = canvas.getContext("2d");
const info = document.getElementById("info");
const control = document.getElementById("episodio");
const reproducir = document.getElementById("reproducir");
const reiniciar = document.getElementById("reiniciar");
const velocidad = document.getElementById("velocidad");
const detalle = document.getElementById("agentes");

async function cargarImagen(nombre) {
  const imagen = new Image();
  imagen.src = "/static/images/" + nombre + ".png";
  await imagen.decode();
  return imagen;
}

async function iniciar() {
  const respuesta = await fetch("/api/data");
  const { nodes, routes, resumen, error } = await respuesta.json();
  if (!respuesta.ok) throw new Error(error);

  const [robot, sucia, limpia, obstaculo, estacion] = await Promise.all(
    ["robot", "node_full", "node_empty", "bote", "estacion"].map(cargarImagen)
  );
  const celdas = Object.values(nodes);
  const agentes = Object.entries(routes);
  const filas = celdas.reduce((max, n) => Math.max(max, n.point[1] + 1), 0);
  const columnas = celdas.reduce((max, n) => Math.max(max, n.point[0] + 1), 0);
  const piso = celdas.filter(n => !n.obstacle).length;
  const total = agentes.reduce((max, [, ruta]) => Math.max(max, ruta.length - 1), 0);
  const colores = ["#7dd3fc", "#fbbf24", "#f9a8d4", "#a7f3d0"];
  control.max = total;
  let tiempo = 0;
  let ultimo = null;
  let corriendo = total > 0;
  let mostrado = -1;

  function dibujar() {
    const episodio = Math.floor(tiempo);
    const ancho = canvas.clientWidth;
    const alto = canvas.clientHeight;
    const lado = Math.min((ancho - 20) / columnas, (alto - 20) / filas);
    const x0 = (ancho - columnas * lado) / 2;
    const y0 = (alto - filas * lado) / 2;
    ctx.clearRect(0, 0, ancho, alto);
    let limpias = 0;

    for (const nodo of celdas) {
      const [columna, fila] = nodo.point;
      const x = x0 + columna * lado;
      const y = y0 + fila * lado;
      const quedaSucia = nodo.dirt && (nodo.clean_tick < 0 || nodo.clean_tick > episodio);
      ctx.fillStyle = nodo.obstacle ? "#415452" : quedaSucia ? "#664a31" : "#244340";
      ctx.fillRect(x + 1, y + 1, lado - 2, lado - 2);
      const imagen = nodo.obstacle ? obstaculo : quedaSucia ? sucia : limpia;
      ctx.drawImage(imagen, x + lado * .18, y + lado * .18, lado * .64, lado * .64);
      if (nodo.station) ctx.drawImage(estacion, x + lado * .63, y + lado * .04, lado * .32, lado * .32);
      if (!nodo.obstacle && !quedaSucia) limpias++;
    }

    const grupos = new Map();
    for (const [id, ruta] of agentes) {
      const nodo = ruta[Math.min(episodio, ruta.length - 1)];
      if (!grupos.has(nodo)) grupos.set(nodo, []);
      grupos.get(nodo).push(id);
    }
    for (const [nodo, ids] of grupos) {
      const [columna, fila] = nodes[nodo].point;
      const columnasGrupo = Math.ceil(Math.sqrt(ids.length));
      const espacio = lado / columnasGrupo;
      ids.forEach((id, i) => {
        const x = x0 + columna * lado + (i % columnasGrupo) * espacio;
        const y = y0 + fila * lado + Math.floor(i / columnasGrupo) * espacio;
        ctx.fillStyle = colores[(Number(id) - 1) % colores.length];
        ctx.fillRect(x + espacio * .1, y + espacio * .1, espacio * .8, espacio * .8);
        ctx.drawImage(robot, x + espacio * .15, y + espacio * .1, espacio * .7, espacio * .65);
        ctx.fillStyle = "#122c29";
        ctx.font = "bold " + Math.max(6, espacio * .24) + "px system-ui";
        ctx.textAlign = "center";
        ctx.fillText(id, x + espacio * .5, y + espacio * .85);
      });
    }

    if (episodio !== mostrado) {
      mostrado = episodio;
      control.value = episodio;
      const porcentaje = (100 * limpias / piso).toFixed(1);
      const resultado = resumen?.fin === "limpio" ? "Limpieza completa" : resumen ? "Límite de tiempo" : "Fin";
      info.textContent = "Episodio " + episodio + " de " + total + " · " +
        porcentaje + "% del piso limpio" + (episodio === total ? " · " + resultado : "");
      detalle.textContent = episodio === total && resumen
        ? resumen.agentes.map(a => "Agente " + a.agente + " · " + a.movimientos +
          " movimientos · " + a.celdas_limpiadas + " celdas limpiadas").join(" | ")
        : agentes.length + (agentes.length === 1 ? " agente" : " agentes");
    }
  }

  function ajustar() {
    const escala = window.devicePixelRatio || 1;
    canvas.width = Math.round(canvas.clientWidth * escala);
    canvas.height = Math.round(canvas.clientHeight * escala);
    ctx.setTransform(escala, 0, 0, escala, 0, 0);
    dibujar();
  }

  function cambiarEstado(estado) {
    corriendo = estado;
    reproducir.textContent = estado ? "Pausar" : "Reproducir";
  }

  reproducir.onclick = () => {
    if (!corriendo && tiempo >= total) tiempo = 0;
    cambiarEstado(!corriendo && total > 0);
    dibujar();
  };
  reiniciar.onclick = () => {
    tiempo = 0;
    cambiarEstado(total > 0);
    dibujar();
  };
  control.oninput = () => {
    tiempo = Number(control.value);
    cambiarEstado(false);
    dibujar();
  };
  function animar(ahora) {
    if (corriendo && ultimo !== null) {
      tiempo = Math.min(total, tiempo + Math.min((ahora - ultimo) / 1000, .1) * Number(velocidad.value));
      if (tiempo >= total) cambiarEstado(false);
      if (Math.floor(tiempo) !== mostrado) dibujar();
    }
    ultimo = ahora;
    requestAnimationFrame(animar);
  }

  for (const elemento of [control, reproducir, reiniciar]) elemento.disabled = total === 0;
  cambiarEstado(corriendo);
  new ResizeObserver(ajustar).observe(canvas);
  ajustar();
  requestAnimationFrame(animar);
}

iniciar().catch(error => { info.textContent = error.message; });
