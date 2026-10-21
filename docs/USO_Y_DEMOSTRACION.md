# Usar y explicar el programa

La versión estable 1.0.0 se descarga desde
[Releases](https://github.com/Abe-ll/FunctionAverageLab/releases/latest).
En Windows de 64 bits no hace falta instalar Python. Si descargás el paquete ZIP,
extraelo antes de abrir el programa.

Abrí CalculoPromedio.exe o ejecutá python main.py desde el proyecto.
No hace falta internet para calcular. Los ejemplos son ayudas de estudio,
no una lista cerrada de funciones.

1. Ingresá f(x), por ejemplo cos(pi*x).
2. Escribí a y b; se permiten -pi, pi/2 y sqrt(2).
3. Elegí la precisión y pulsá **Calcular promedio**.
4. Compará integral, promedio y error estimado. Revisá la gráfica y Procedimiento.
5. Cambiá los datos para otra función; el resultado anterior se limpia.

Los ángulos están en radianes. Usá * para multiplicar y punto decimal.
^ y ** sirven para potencias. sin y sen son equivalentes; ln y log son
logaritmo natural. La pestaña Ayuda conserva la sintaxis y los límites.

El historial guarda hasta 30 resultados de esta sesión. JSON conserva el
resultado y sus condiciones; CSV contiene 501 muestras de visualización,
que no son la malla de integración. Cancelar permite detener el cálculo.
Si aparece un error, revisá el dominio, a<b y los paréntesis. No uses un
resultado rechazado como respuesta válida.

## Modo oscuro y entrada matemática

El botón **Modo oscuro / Modo claro** cambia ventana, controles, texto y gráfica
durante esta sesión, conservando el resultado y el historial.
Al hacer clic en la función o un límite aparece un teclado plegable. También
lo podés abrir y cerrar con ⌨; **Listo** o Escape lo ocultan.

√ inserta sqrt(), π inserta pi, × y ÷ insertan * y /. Los botones x², xʸ y a⁄b
ayudan con potencias y fracciones. Las funciones colocan el cursor dentro del
paréntesis; si seleccionás algo, lo envuelven. Ejemplo: tocá √ y luego 9 para
obtener sqrt(9). Para escribir una fracción, completá los dos paréntesis moviendo
el cursor con las flechas. El teclado físico sigue disponible.
Cuando se insertan dos factores consecutivos, el teclado matemático agrega *
donde corresponde; la escritura física continúa usando * explícito.

## Explorar y guardar la gráfica

- Rueda del ratón: acercar o alejar alrededor del cursor.
- Arrastrar: mover la vista. También funcionan las flechas con la gráfica enfocada.
- Barras inferior y lateral: desplazamiento horizontal y vertical.
- Deslizador lateral y botones +/−: controlar el zoom.
- Cuadrícula y Ejes: mostrar u ocultar las referencias.
- Ajustar o doble clic: recuperar la vista inicial.
- Guardar gráfica PNG: generar una imagen de 1600×1000, con tema y vista actuales.

Al ampliar, vuelvo a muestrear la porción visible dentro de [a,b], sin cambiar
el resultado de integración. Fuera de ese intervalo no se prolonga la curva.
Los rótulos aumentan sus dígitos cuando hace falta. La gráfica muestreada puede
omitir oscilaciones o picos; no demuestra continuidad ni sustituye los controles
del cálculo. El error numérico mostrado se refiere al promedio.

La interacción toma como referencia la [vista gráfica de GeoGebra](https://geogebra.github.io/docs/manual/en/Graphics_View/)
y su [teclado virtual](https://geogebra.github.io/docs/manual/en/View_Menu/).
Esta implementación es local y no integra GeoGebra ni sus servicios.
Para PNG se usa [Pillow ImageDraw](https://pillow.readthedocs.io/en/stable/reference/ImageDraw.html).

## Guion propuesto para un máximo de 20 minutos

| Minutos | Contenido |
| --- | --- |
| 0–3 | Problema, fórmula, condiciones y diferencia entre integral y promedio |
| 3–6 | x² en [0,3]: comparación manual con Zill |
| 6–10 | Simpson y control independiente |
| 10–14 | Función nueva, gráfica, exportación y corrección de un error |
| 14–17 | Pruebas, oscilaciones y límites numéricos |
| 17–20 | Preguntas y margen para la función indicada por el docente |

Es una propuesta; no asigna integrantes ni confirma fecha de exposición.
Cada integrante debería poder explicar la interpretación de la fórmula,
la integración y las limitaciones de la tolerancia.

## Qué falta para entregar

El PDF debe incluir carátula con nombres y carnés de los tres integrantes,
nombre del programa, software usado, introducción, objetivos, código,
conclusiones y recomendaciones. Esos datos y la revisión del equipo siguen
pendientes. Un EXE local o un push no demuestra envío a Canvas.

| Archivo | Función |
| --- | --- |
| main.py | Elegir ventana, consola o comprobación |
| average_lab/expressions.py | Revisar y evaluar la expresión |
| average_lab/numerics.py | Calcular y contrastar el promedio |
| average_lab/gui.py | Mostrar datos, gráfica, ayuda e historial |
| average_lab/plotting.py | Explorar la gráfica y generar PNG |
| average_lab/keyboard.py | Insertar símbolos y plantillas matemáticas |
| average_lab/themes.py | Paletas clara y oscura |
| average_lab/examples.py | Ejemplos con respuesta analítica |
| tests/ | Verificar resultados y comportamiento |
| tools/build_windows.py | Construir y comprobar el EXE |

La configuración de VS Code se hará por separado con el equipo local.

## Presentación y comparación de funciones

La función se escribe a la izquierda, junto a la gráfica; también se acepta y= o f(x)= al principio. La vista previa aparece al terminar de escribir. Calcular promedio ejecuta y verifica el cálculo; no hay promedio numérico durante una vista previa. El bloque del promedio está debajo de los controles.

El botón ? junto al teclado abre los ejemplos. Al seleccionar uno se carga y calcula automáticamente, sin un botón adicional de carga. Fijar curva conserva la función y cambia el color de la siguiente. Se admiten tres referencias además de f(x); × quita una referencia. El promedio siempre pertenece a la función activa f(x).

Pantalla completa o F11 abre la vista de presentación, con entrada de función, teclado, ejemplos y PNG. Escape o Salir vuelve conservando la vista. La interfaz usa superficies negras o blancas y acentos morados; cada curva tiene su color.

Para mover con fluidez reutilizo expresiones y muestras, agrupo segmentos en trayectorias y dejo un solo fotograma pendiente para eventos rápidos. Al soltar el ratón o acercar más actualizo las muestras donde hace falta. PNG incluye las referencias y el promedio de f(x), conservando sus colores.
