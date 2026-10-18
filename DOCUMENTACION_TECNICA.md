
# DOCUMENTACION TECNICA

Lenguaje: Python 3



## 1 Bibliotecas utilizadas

    - ast(Abstract Syntax Tree): Analiza la estructura de las expresiones matemáticas introducidas por el usuario. Permite identificar operaciones, variables y llamadas a funciones sin ejecutar directamente el texto ingresado.

    - math: Proporciona funciones matemáticas como seno, coseno, raíz cuadrada y exponenciales, además de constantes como pi y e.

    - operator: Proporciona funciones para ejecutar operaciones aritméticas, como suma, resta, multiplicación, división y potenciación.

Se decidió utilizar estas herramientas para construir un intérprete matemático restringido, que permita controlar las operaciones aceptadas.


### Herramienta de calculo principal

El método de integración de Simpson 1/3 compuesto fue implementado manualmente, sin utilizar librerías que calculen integrales automáticamente.

Dependencias externas: Ninguna en el prototipo actual.



## 2. Configuración del intérprete matemático

El programa utiliza tres diccionarios de Python para definir las operaciones, funciones y constantes que el usuario puede introducir.

### 2.1 Operaciones permitidas (operaciones)

Este diccionario relaciona los operadores identificados por ast con las funciones de la biblioteca operator.
Permite realizar cinco operaciones básicas:

    - Suma (+)
    - Resta (-)
    - Multiplicación (*)
    - División (/)
    - Potenciación (**)

Por ejemplo, cuando el usuario introduce x^2 + 3*x, el programa identifica las operaciones necesarias para evaluar la expresión.

### 2.2 Funciones matemáticas (funciones)

 Este diccionario contiene las funciones matemáticas que el intérprete reconoce:

sin(x), cos(x), tan(x): funciones trigonométricas.

     - sqrt(x): raíz cuadrada.
    - exp(x): función exponencial.
    - log(x): logaritmo natural.
    - abs(x): valor absoluto.

Estas funciones pueden combinarse con operaciones aritméticas para construir expresiones más complejas.
Las funciones trigonométricas trabajan en radianes.

### 2.3 Constantes matemáticas (constantes)
Se definieron tres constantes principales:

    - π: reconocida mediante pi, PI o π.
    - e: reconocida mediante e.
    - τ: reconocida mediante tau o τ, equivalente a 2π.

Estas constantes pueden utilizarse tanto en las funciones como en los límites de integración.

Decisión técnica

El uso de diccionarios permite controlar las herramientas matemáticas disponibles y ampliar las operaciones admitidas sin modificar el algoritmo de Simpson.

La única variable independiente admitida actualmente es x.



## 3. Intérprete matemático — evaluar(nodo, x)

La función `evaluar(nodo, x)` permite interpretar y calcular expresiones matemáticas utilizando el árbol sintáctico generado por la biblioteca `ast`.

### 3.1 Parámetros

- `nodo`: representa una parte de la expresión matemática que se está analizando.
- `x`: valor numérico que se utiliza para evaluar la función.

### 3.2 Funcionamiento

La función analiza los elementos de la expresión y determina cómo procesarlos:

1. **Constantes numéricas (`ast.Constant`):** devuelve directamente números como 2, 5 o 3.5.
2. **Variables (`ast.Name`):** identifica la variable `x` y las constantes matemáticas permitidas.
3. **Signos (`ast.UnaryOp`):** permite utilizar números positivos y negativos
4. **Operaciones (`ast.BinOp`):** realiza sumas, restas, multiplicaciones, divisiones y potencias.
5. **Funciones (`ast.Call`):** ejecuta funciones matemáticas autorizadas como `sin(x)` o `sqrt(x)`.

La evaluación es recursiva: cuando una operación contiene otras expresiones, la función vuelve a llamarse para resolver cada una.

Si encuentra una operación no permitida, genera un error mediante `ValueError`.

### 3.3 Ejemplo

Expresión introducida: `x^2 + 3*x`

Si el valor de x es 2:

- Calcula 2² = 4.
- Calcula 3 × 2 = 6.
- Suma ambos resultados.

**Resultado: 10**

Esta función permite que el método de Simpson evalúe diferentes expresiones matemáticas sin modificar su algoritmo de integración.



## 4. Entrada y validaciones

### 4.1 Función f(x)

La función `f(x)` conecta el intérprete matemático con el método de Simpson.

Recibe un valor de `x`, utiliza `evaluar()` para calcular la expresión ingresada por el usuario y devuelve el resultado numérico.

También comprueba que el resultado sea real y finito. Si ocurre un error matemático, genera un mensaje indicando el valor de `x` donde sucedió.

### 4.2 Función leer_limite(mensaje)

Permite introducir los límites de integración `a` y `b` desde la terminal.

Utiliza nuestro intérprete para aceptar números y expresiones como `pi/2` o `2*pi`.

Incluye validaciones para rechazar entradas incorrectas, resultados infinitos y límites que dependan de `x`.

El ciclo `while True` permite volver a solicitar los datos cuando se detecta un error.

### 4.3 Validaciones generales

El prototipo también comprueba:

    - Funciones desconocidas o expresiones mal escritas.
    - Expresiones demasiado largas o complejas.
    - Intervalos donde `a >= b`.
    - Divisiones entre cero y errores de dominio en puntos evaluados.
    - Diferencias excesivas entre dos aproximaciones numéricas de Simpson.

Estas validaciones reducen los errores comunes, aunque no garantizan detectar todas las discontinuidades matemáticas.



## 5. Núcleo matemático

### 5.1 Función simpson(funcion, a, b, n)

Implementa el método de Simpson 1/3 compuesto para aproximar una integral definida.

**Parámetros:**
- `funcion`: función matemática que se desea integrar.
- `a`, `b`: límites de integración.
- `n`: número par de subintervalos.

**Funcionamiento:**

1. Calcula el ancho de cada subintervalo: `h = (b-a)/n`.
2. Suma los valores de la función en ambos extremos.
3. Recorre los puntos interiores mediante un ciclo `for`.
4. Multiplica por 4 los valores de índice impar y por 2 los de índice par.
5. Multiplica la suma total por `h/3` para obtener la integral aproximada.

El algoritmo fue implementado manualmente, sin utilizar bibliotecas de integración numérica.

### 5.2 Función valor_promedio(funcion, a, b, n)

Utiliza `simpson()` para obtener la integral definida y posteriormente la divide entre la longitud del intervalo.

**Fórmula matemática:**

Valor promedio = Integral definida / (b - a)

**Ejemplo:**

Para `f(x) = x^2`, entre 0 y 2:

- Integral: aproximadamente 2.666667.
- Longitud del intervalo: 2.
- Valor promedio: aproximadamente 1.333333.

Esta separación permite reutilizar el algoritmo de Simpson para diferentes funciones y aplicaciones.



## 6. Resultados y limitaciones

### 6.1 Presentación de resultados

El programa calcula la integral mediante Simpson utilizando `n = 200` subintervalos y repite el cálculo con `n = 400`.

Compara ambos resultados para identificar posibles diferencias numéricas importantes.

Si la diferencia supera la tolerancia establecida, muestra una advertencia. En caso contrario, utiliza la segunda aproximación para calcular el valor promedio.

Los resultados se presentan en la terminal con seis decimales.

### 6.2 Manejo de errores

Se utiliza `try/except` para capturar errores matemáticos comunes y mostrar mensajes comprensibles en lugar de finalizar con un error técnico de Python.

### 6.3 Limitaciones actuales

- Solo permite resolver un problema por ejecución.
- Funciona mediante terminal, sin interfaz gráfica.
- No genera gráficas matemáticas.
- El número de subintervalos se modifica directamente en el código.
- No garantiza detectar todas las discontinuidades.
- La comparación de Simpson no garantiza exactitud absoluta.

### 6.4 Desarrollo futuro

El prototipo está diseñado como base para continuar el proyecto mediante:

- Mejor organización y separación de componentes.
- Interfaz gráfica con Tkinter.
- Visualización de funciones mediante Matplotlib.
- Posibilidad de realizar múltiples cálculos consecutivos.
- Mejoras de precisión y validación matemática.

El objetivo es conservar el núcleo matemático desarrollado y ampliar sus funcionalidades sin reemplazar el método de integración.