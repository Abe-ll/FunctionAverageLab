# Cálculo del promedio de una función matemática

Proyecto final de Cálculo II, tema 7: valor promedio de una función.

Acá parto del prototipo del Polanco: conservo el intérprete AST y Simpson 1/3.
Separo el motor, la consola y la ventana, y agrego validación y control independiente.
La documentación original permanece en DOCUMENTACION_TECNICA.md.

## Ejecutar

Python 3.12 o posterior. El cálculo usa la biblioteca estándar;
Pillow permite guardar imágenes PNG:

    python -m pip install -r requirements.txt
    python main.py

Se abre una ventana con función editable, límites, tres niveles de precisión,
ocho ejemplos, gráfica, procedimiento e historial de la sesión.
Los resultados se pueden exportar como JSON, las muestras como CSV y la gráfica como PNG.
El cálculo se puede cancelar; al modificar los datos se invalida el resultado anterior.

La entrada f(x) se actualiza como vista previa al escribir. **Calcular promedio**
ejecuta el cálculo numérico; una vista previa no muestra un promedio inventado.
El botón **?**, a la derecha de ⌨, abre los ejemplos: seleccionar uno lo carga y calcula.
El valor promedio aparece debajo de los controles, dejando más espacio a la gráfica.
**Fijar curva** conserva hasta tres referencias para compararlas con la función
activa; su color se puede elegir. El promedio siempre corresponde a f(x).

El botón de arriba alterna modo claro y oscuro. La gráfica admite rueda para
zoom sobre el cursor, arrastre, barras de desplazamiento, deslizador de zoom,
cuadrícula y ejes conmutables y **Ajustar** para volver a la vista inicial.
**Pantalla completa** o F11 abre la presentación con entrada de función, teclado,
ejemplos y exportación. Escape o Salir vuelve a la ventana y conserva la vista.
El PNG guarda la vista y el tema actuales, con función, intervalo, promedio
y error estimado. Se genera a partir de los datos, sin capturar el escritorio.

Al tocar la función o un límite se despliega el teclado matemático. El botón
⌨ lo abre o cierra; **Listo** y Escape lo ocultan. Los botones √, x², xʸ,
fracción, π y funciones insertan sintaxis válida en el cursor. Seleccioná una
expresión para envolverla en una función. Se puede seguir usando el teclado físico.

La interfaz usa negros, morados y blancos con colores independientes para cada
curva. Al mover la vista reutilizo muestras, agrupo el trazado y junto los eventos
rápidos del ratón. Una mejora medida de redibujado no garantiza FPS del monitor.

Consola educativa y comprobaciones:

    python main.py --cli

    python main.py --self-test

    python main.py --smoke-test

## Ejecutable para Windows

El paquete portable contiene CalculoPromedio.exe; se abre con doble clic y
no requiere instalar Python. El modo consola se usa desde el código fuente.
La compilación está preparada para Windows de 64 bits.

Para construirlo desde una terminal del proyecto en Windows:

    python -m venv .venv
    .venv\Scripts\python -m pip install -r requirements-build.txt
    .venv\Scripts\python tools/build_windows.py

El proceso ejecuta las pruebas, construye el EXE, prueba ese mismo archivo
con su interfaz, modo oscuro, teclado y exportación PNG, y crea
dist/CalculoPromedio-Windows.zip con su huella SHA-256.
GitHub Actions verifica los cambios de main y mejoras/* y conserva el paquete
como artefacto durante 30 días. No se guardan entornos ni binarios en el historial.

## Pruebas

    python -m unittest discover -s tests -v

Sintaxis: x^2, 2*x, sin(x), sen(x), cos(x), sqrt(x), exp(x), log(x),
ln(x), abs(x), pi. Los ángulos se interpretan en radianes.

## Alcance numérico

Se requieren límites reales finitos a<b y una función propia e integrable.
Se calcula el promedio en una variable normalizada y luego la integral.
Simpson adaptativo se contrasta con otra regla y particiones diferentes.
El error es **estimado**, no una garantía universal ni una prueba de continuidad.
Polos, dominios inválidos o precisión no resuelta producen un mensaje de rechazo.
No se soportan integrales impropias, números complejos ni código Python arbitrario.
