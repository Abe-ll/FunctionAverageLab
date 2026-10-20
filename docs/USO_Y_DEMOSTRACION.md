# Usar y explicar el programa

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
| average_lab/examples.py | Ejemplos con respuesta analítica |
| tests/ | Verificar resultados y comportamiento |
| tools/build_windows.py | Construir y comprobar el EXE |

La configuración de VS Code se hará por separado con el equipo local.
