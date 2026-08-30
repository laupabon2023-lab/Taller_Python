# Hallazgos — Parte A

**Grupo:** <número> · **Integrantes:** <nombre 1>, <nombre 2>, <nombre 3>

> No borren la fila de ejemplo hasta haber comprobado que su tabla se parsea.
> El formato es rígido: siete columnas, en este orden. Una tabla torcida se
> rechaza indicando la línea, no se «entiende igual».
>
> **Tuberías dentro de una celda:** si su comando lleva `|` —y varios lo llevarán,
> por `grep`, `head` o `jq`— escríbanlo `\|`. Sin escapar, Markdown lo lee como
> separador de columna y su fila pasa a tener ocho.

| ID | Síntoma observable | Causa | Módulo · Sección | SHA donde se observa | Comando de evidencia | Salida obtenida | Corrección aplicada |
|----|--------------------|-------|------------------|----------------------|----------------------|-----------------|---------------------|
| H1 | *(ejemplo de FORMATO, no un defecto de este repositorio)* `GET /ping` responde sin cabecera `Cache-Control` | El handler no declara política de caché | M2 · 2. El protocolo HTTP y la autenticación | `v0-semilla` | `curl -sI localhost:8000/ping \| grep -ci cache-control` | `0` | Se añade la cabecera en la respuesta |
| H2 |requirements.txt lista los paquetes sin número de versión |Sin ==, pip install resuelve siempre la versión más reciente, que varía según cuándo y dónde se instale |M1 · Módulo 2: Entornos Virtuales | v0-semilla |grep -c "==" requirements.txt |0 |Se fija la versión exacta de cada paquete instalado corriendo pip freeze > requirements.txt dentro del entorno virtual, reemplazando el archivo actual por uno con el formato paquete==versión.|
| H3 |config.py contiene API_KEY y CLAVE_FIRMA escritas como texto visible en el código"|Las claves se escriben directo en el código en vez de leerse desde variables de entorno, quedando expuestas en el repositorio. |M1 · Módulo 4: Git y GitHub para Investigadores |v0-semilla |grep -c "API_KEY" config.py |1 |Se mueve el valor a una variable de entorno (leída con os.environ), y el archivo con el valor real se agrega a .gitignore para que nunca se suba |
| H4 |El servicio envía mensaje 200 ok pero silenciosamente hay un error en la solicitud que no es fácilmente visible. |Se utiliza return {"error": ...} en vez de raise HTTPException(...), por lo que FastAPI responde con 200 por defecto sin importar el contenido  |M2 · 2. El protocolo HTTP y la autenticación | |v0-semilla | curl -s -o /dev/null -w "%{http_code}" -X POST localhost:8000/score -H "Content-Type: application/json" -d '{"monto": 5000}'|200 |Se reemplaza el dict por ScorePayload (Pydantic); FastAPI valida el payload automáticamente y responde 422 por defecto si falta un campo, sin necesidad de un raise manual|
| H5 |Genera error 500 al indicar un monto negativo |assert sin controlar lanza AssertionError no manejado; además se desactiva con la bandera -O de Python |M2 · 2. El protocolo HTTP y la autenticación |v0-semilla |curl -s -o /dev/null -w "%{http_code}" -X POST localhost:8000/score -H "Content-Type: application/json" -d '{"poliza": "POL-001", "monto": -500, "antiguedad": 2}' |500 |Reemplazar assert por validación explícita (Pydantic Field o raise HTTPException(422, ...))|
| H6 |GET /exportar responde application/octet-stream (binario pickle), no JSON|Usa pickle.dumps() en vez de devolver JSON; pickle no es seguro ni interoperable para un cliente externo |M2 · 3. JSON frente a Pickle|v0-semilla |curl -s -i localhost:8000/exportar | grep -ia content-type|content-type: application/octet-stream|Reemplazar por return datos (FastAPI serializa a JSON automáticamente)|
| H7 |El modelo se carga con pickle.load dentro del handler /score, en cada petición |No se carga una sola vez al iniciar el servicio. Se relee en cada requerimiento |M5 · 8. Resumen y mejores prácticas |v0-semilla |grep -n "pickle.load" main.py |29: modelo = pickle.load(fh) (dentro de la función) |Cargar el modelo una sola vez al iniciar (evento startup o variable global al importar) |
| H8 |GET /health no existe |El servicio no expone ningún endpoint de salud para monitoreo/orquestación|M5 · 2. Introducción: por qué necesitas saber esto |v0-semilla |curl -s -o /dev/null -w "%{http_code}" localhost:8000/health|404|Agregar @app.get("/health") que responda 200|
| H9 |README documenta --reload como comando de arranque y dice que "sirve en producción"; main.py tiene reload=True hardcodeado |--reload es para desarrollo (vigila archivos y reinicia), añade sobrecarga y no determinismo en producción |M5 · 3. El servidor web y WSGI |v0-semilla |grep -c "reload" README.md |2 | Arranque de producción: uvicorn main:app --host 0.0.0.0 --port 8000 --workers 4|
| H10 |El decorador con_registro atrapa cualquier excepción de puntuar() y devuelve None en silencio|try/except Exception genérico oculta fallos reales; además envoltura no usa functools.wraps, perdiendo la identidad de la función original |M1 · Módulo 5: Decoradores Estadísticos |v0-semilla |python3 -c "from utilidades import con_registro; f = con_registro(lambda: 1/0); print(f())" |None (en vez de propagar el error) | El try/except se conserva para seguir registrando el fallo con print, pero en vez de return None ahora hace raise (propaga la excepción); además se añade @functools.wraps(func) para conservar la identidad de la función original|




**Reglas que se verifican automáticamente:**

- `Módulo · Sección` debe citar una lección que exista en los módulos 1 a 5, con el
  título tal como aparece en el menú lateral del material.
- **`SHA donde se observa`** es el commit donde el defecto todavía está: normalmente
  `v0-semilla`, la etiqueta del repositorio tal como se lo entregamos. El calificador hace
  *checkout* de ese commit para reproducir la evidencia. Si lo dejan en el commit final —donde
  ya está corregido— el comando no reproducirá nada y la fila no cuenta.
- `Comando de evidencia` se ejecuta ahí. Escríbanlo contra `localhost:8000`; el calificador
  sustituye el puerto por el que use.
- `Salida obtenida` es literal, copiada de su terminal. **Se compara con lo que salga de
  verdad**, así que una salida inventada se detecta.
- Entre 6 y 12 hallazgos. Una fila que no corresponda a un defecto real resta la mitad de lo
  que suma una correcta: el máximo se alcanza con precisión, no con volumen.

---

# Parte C — Interpretación de las mediciones

> Un párrafo por endpoint. Expliquen **los tiempos que ustedes obtuvieron**, no la
> teoría general. Si un resultado los sorprendió, dígan­lo: eso se premia.

## `/ping`

## `/consulta-archivo`

## `/servicio-externo`

## `/calculo-pesado`
