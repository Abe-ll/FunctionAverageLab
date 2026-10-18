
"""
=================================================
             FUNCTION AVERAGE LAB
          Proyecto Final - Calculo II
=================================================

OBJETIVO:
Desarrollar un programa que calcule numericamente
el valor promedio de una funcion matematica
dentro de un intervalo definido.

METODO:
Utilizaremos el metodo de Simpson 1/3 compuesto
para aproximar la integral definida.

Posteriormente dividiremos la integral obtenida
entre la longitud del intervalo (b - a).

ENTRADAS:
- Funcion matematica f(x)
- Limite inferior (a)
- Limite superior (b)
- Numero de subdivisiones (n)

SALIDAS:
- Valor aproximado de la integral definida
- Valor promedio de la funcion

PROPOSITO:
Proporcionar una herramienta matematica precisa,
comprensible y facil de utilizar, que permita
resolver diferentes funciones sin modificar
el codigo fuente.
=================================================



FUNCIONALIDADES IMPLEMENTADAS:
- Calculo de integrales con Simpson 1/3 compuesto.
- Calculo numerico del valor promedio.
- Ingreso de funciones matematicas por consola.
- Ingreso de limites numericos o expresiones.
- Interpretacion matematica mediante AST.
- Comparacion de dos aproximaciones de Simpson.
- Resultados mostrados con 6 decimales.
- Manejo de errores comunes sin cerrar el programa.

VARIABLES CONSIDERADAS:
- x: Variable independiente de la funcion.
- a: Limite inferior de integracion.
- b: Limite superior de integracion.
- n: Numero par de subintervalos de Simpson.
- h: Ancho de cada subintervalo.

OPERACIONES Y FUNCIONES ADMITIDAS:
- Suma, resta, multiplicacion y division.
- Potencias y parentesis.
- Polinomios y funciones racionales.
- Radicales: sqrt(x).
- Trigonometricas: sin(x), cos(x), tan(x).
- Exponenciales: exp(x).
- Logaritmicas: log(x), logaritmo natural.
- Valor absoluto: abs(x).
- Combinaciones de las anteriores.

CONSTANTES MATEMATICAS:
- pi, PI, π: Numero pi.
- e: Numero de Euler.
- tau, τ: Equivalente a 2*pi.

VALIDACIONES IMPLEMENTADAS:
- Expresiones vacias o mal escritas.
- Funciones y nombres desconocidos.
- Expresiones de longitud mayor a 200 caracteres.
- Expresiones con mas de 100 nodos AST.
- Operaciones matematicas no permitidas.
- Limites no numericos o infinitos.
- Limites que dependen de x.
- Intervalos donde a >= b.
- Division entre cero en puntos evaluados.
- Errores de dominio matematico detectados.
- Resultados complejos o no finitos.
- Exponentes evaluados mayores a 100 en valor absoluto.
- Advertencia ante diferencias numericas elevadas.

CONFIGURACION ACTUAL:
- n = 200 subintervalos iniciales.
- Segunda aproximacion con n = 400.
- Tolerancia de comparacion: 0.00001 relativa
  con escala minima de 1.
- Precision visual: 6 decimales.


"""





# ==========================================
# 1. DEFINICION DE LA FUNCION E INTERVALO
# ==========================================


import ast #Para analizar y reconocer las expresiones del usuario
import math #Funciones y constantes
import operator #Para operaciones dentro de funciones


# OPERACIONES PERMITIDAS
operaciones = {
    ast.Add: operator.add, #Suma    
    ast.Sub: operator.sub, #Resta
    ast.Mult: operator.mul, #Multiplicacion
    ast.Div: operator.truediv, #Division
    ast.Pow: operator.pow #Potencia
}


# FUNCIONES MATEMATICAS
funciones = {
    "sin": math.sin,
    "cos": math.cos,
    "tan": math.tan,
    "sqrt": math.sqrt,
    "exp": math.exp,
    "log": math.log,
    "abs": abs
}

constantes = {
    "pi": math.pi,
    "PI": math.pi,
    "π": math.pi,
    "e": math.e,
    "tau": math.tau,
    "τ": math.tau
}
#Declaracion de PI y Euler



# ENTRADA DEL USUARIO
# VALIDACION DE ENTRADA DE FUNCIONES

while True:
    expresion = input("Ingrese f(x): ").strip().replace("^", "**")

    try:
        if not expresion:
            raise ValueError("Debe ingresar una funcion")

        if len(expresion) > 200:
            raise ValueError("Expresion demasiado larga")

        arbol = ast.parse(expresion, mode="eval")

        if sum(1 for nodo in ast.walk(arbol)) > 100:
            raise ValueError("Expresion demasiado compleja")

        # VALIDAR FUNCIONES Y NOMBRES, para sen en lugar de sin

        permitidos = {"x"} | set(funciones) | set(constantes)

        for nodo in ast.walk(arbol):

            if isinstance(nodo, ast.Call):
                if not isinstance(nodo.func, ast.Name):
                    raise ValueError("Formato de funcion no permitido")

                if nodo.func.id not in funciones:
                    raise ValueError(f"Funcion desconocida: {nodo.func.id}")

            if isinstance(nodo, ast.Name):
                if nodo.id not in permitidos:
                    raise ValueError(f"Nombre no reconocido: {nodo.id}")

        break

    except (SyntaxError, ValueError) as error:
        print(f"Entrada invalida: {error}")
        print("Intente nuevamente.\n")


# VALIDACION
# INTERPRETE MATEMATICO
def evaluar(nodo, x):

    if isinstance(nodo, ast.Constant) and type(nodo.value) in (int, float):
        return nodo.value

    if isinstance(nodo, ast.Name):
        if nodo.id == "x":
            return x
        if nodo.id in constantes:
            return constantes[nodo.id]

    if isinstance(nodo, ast.UnaryOp) and isinstance(nodo.op, (ast.UAdd, ast.USub)):
        valor = evaluar(nodo.operand, x)
        return -valor if isinstance(nodo.op, ast.USub) else valor

    if isinstance(nodo, ast.BinOp) and type(nodo.op) in operaciones:
        izquierda = evaluar(nodo.left, x)
        derecha = evaluar(nodo.right, x)

        if isinstance(nodo.op, ast.Pow) and abs(derecha) > 100:
            raise ValueError("Exponente demasiado grande")

        return operaciones[type(nodo.op)](izquierda, derecha)

    if isinstance(nodo, ast.Call) and isinstance(nodo.func, ast.Name):
        nombre = nodo.func.id
        if nombre in funciones and len(nodo.args) == 1 and not nodo.keywords:
            return funciones[nombre](evaluar(nodo.args[0], x))

    raise ValueError("Expresion no permitida")



# FUNCION QUE UTILIZARA SIMPSON

def f(x):
    try:
        resultado = evaluar(arbol.body, x)

        if isinstance(resultado, complex) or not math.isfinite(resultado):
            raise ValueError("Resultado no real o infinito")

        return resultado

    except (ValueError, ZeroDivisionError, OverflowError) as error:
        raise ValueError(f"Funcion invalida en x = {x:.6g}: {error}") from error




# Introduccion de datos de los intervalos, USUARIO


#INTERPRETACION DE LIMITES, para poder ingresar "PI" como un limite
#inluye validacion de errore, except. :3
def leer_limite(mensaje):
    while True:
        try:
            texto = input(mensaje).strip().replace("^", "**")

            if len(texto) > 200:
                raise ValueError("Expresion demasiado larga")

            arbol_limite = ast.parse(texto, mode="eval")

            if sum(1 for n in ast.walk(arbol_limite)) > 100:
                raise ValueError("Expresion demasiado compleja")

            if any(isinstance(n, ast.Name) and n.id == "x"
                   for n in ast.walk(arbol_limite)):
                raise ValueError("El limite no puede depender de x")

            valor = evaluar(arbol_limite.body, 0)

            if not isinstance(valor, (int, float)) or not math.isfinite(valor):
                raise ValueError("El limite debe ser un numero real finito")

            return float(valor)

        except (SyntaxError, ValueError, ZeroDivisionError,
                OverflowError, TypeError) as error:
            print(f"\nLimite invalido: {error}")
            print("Intente nuevamente.\n")


while True:
    a = leer_limite("Ingrese el limite inferior (a): ")
    b = leer_limite("Ingrese el limite superior (b): ")

    if a < b:
        break

    print("Intervalo invalido: b debe ser mayor que a.")
    print("Intente nuevamente.\n")

n = 200
# numero de intervalos de Simpson,
# mayores datos, mas precisión pero tambien mas calculos
# menores datos, menor precisión, pero menos calculos


#///////////////////////////////////////////



# ==========================================
# 2. METODO DE SIMPSON 1/3 COMPUESTO
# ==========================================

def simpson(funcion, a, b, n):

# h: Calcula el ancho de cada division 
# Suma: Suma los valoroes de los dos extremos
# Return: el numero de la integral, aproximado si es un dato de mas de 3 decimales
#

    h = (b - a) / n
    suma = funcion(a) + funcion(b)

    for i in range(1, n):
        x = a + i * h

        if i % 2 == 0:
            suma += 2 * funcion(x)
        else:
            suma += 4 * funcion(x)

    integral = (h / 3) * suma

    return integral






#///////////////////////////////////////////



# ==========================================
# 3. CALCULO DEL VALOR PROMEDIO
# ==========================================


#Promedio: Divide el resultado entre b - a, luego devuelve el promedio en el return

def valor_promedio(funcion, a, b, n):

    integral = simpson(funcion, a, b, n)
    promedio = integral / (b - a)

    return promedio



#///////////////////////////////////////////


# RESULTADOS, MANEJO DE ERRORES

try:
    integral = simpson(f, a, b, n)
    integral_refinada = simpson(f, a, b, n * 2)

    diferencia = abs(integral_refinada - integral)
    tolerancia = 0.00001 * max(1, abs(integral_refinada))

    if diferencia > tolerancia:
        raise ValueError(
            "Resultado numerico inestable. "
            "Revise la funcion y el intervalo."
        )

    promedio = integral_refinada / (b - a)

    print("\n=== RESULTADOS ===")
    print(f"Integral: {integral_refinada:.6f}")
    print(f"Valor promedio: {promedio:.6f}")

except (ValueError, ZeroDivisionError, OverflowError) as error:
    print("\n=== NO SE PUDO CALCULAR ===")
    print(f"Detalle: {error}")

