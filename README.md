# Function Average Lab

Proyecto final de Cálculo II, tema 7: valor promedio de una función.

Evolución del prototipo de Rodrigo Polanco: intérprete AST y Simpson 1/3,
ahora separados de la consola, con validación y control independiente.
Ver [autoría](AUTHORS.md) y la documentación original DOCUMENTACION_TECNICA.md.

## Ejecutar por consola

Python 3.12 o posterior, sin paquetes externos para el cálculo:

    python main.py --cli

    python main.py --self-test

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
