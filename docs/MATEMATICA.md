# Cómo calculo el promedio

Para una función integrable en [a,b], con a<b:

$$f_{\mathrm{prom}}=\frac{1}{b-a}\int_a^b f(x)\,dx.$$

La integral conserva el signo. El promedio tiene las unidades de f; la integral
tiene unidades de f por las de x. No es, en general, (f(a)+f(b))/2.
Si f es continua, existe c en (a,b) con f(c)=f_prom, por el teorema del valor
medio para integrales. El programa calcula el promedio; no busca c.

## Referencia del libro local

Zill, *Cálculo de una variable: trascendentes*, §6.7, impresas 351–355,
visor 376–380 del PDF local de 629 páginas. Se verificó la sección completa,
con ejemplos y figuras. La definición 6.7.1, el teorema 6.7.1 y los ejemplos
1 y 2 están en la impresa 353; el ejemplo 3 y los ejercicios en la 354.
El libro permanece como material local del curso.

El ejemplo 1 usa x² en [0,3]:

$$I=[x^3/3]_0^3=9,\qquad f_{\mathrm{prom}}=9/3=3.$$

La derivada de x³/3 es x². La altura media es 3; el valor de x que produce
esa altura es √3. Son cantidades distintas.
El ejemplo 3 usa x²+1 en [-2,2]: integral 28/3 y promedio 7/3.
Las figuras 6.7.3 y 6.7.4 comparan el área bajo una función no negativa con
la de un rectángulo de altura promedio. Para valores negativos, uso integral
con signo al hacer esta interpretación.

También comparo con estos enunciados exactos de la impresa 354:

| Ejercicio | Función e intervalo | Antiderivada | Promedio |
| --- | --- | --- | --- |
| 5 | 3x²−4x, [-1,3] | x³−2x² | 3 |
| 9 | √x, [0,9] | 2x^(3/2)/3 | 2 |
| 18 | cos(2x), [0,π/4] | sen(2x)/2 | 2/π |
| 25 | T(t)=100+3t−t²/2, [0,6] | 100t+3t²/2−t³/6 | 103 |

Cada antiderivada se comprueba derivando. En el ejercicio 25, el resultado
tiene las unidades de temperatura de T; el texto revisado no especifica
una escala. En la aplicación se ingresa 100+3*x-0.5*x^2, con límites 0 y 6.

## Cómo lo llevo al programa

Acá conservo Simpson 1/3 de la versión del Polanco y cambio la variable:

$$x=a+(b-a)t,\quad dx=(b-a)dt,\quad
f_{\mathrm{prom}}=\int_0^1 f(a+(b-a)t)\,dt.$$

Así controlo directamente el error del promedio, incluso si b−a es pequeño.
Después multiplico por b−a para obtener la integral.
Para g(t)=f(a+(b−a)t), en [u,v] con m=(u+v)/2:

$$S=\frac{v-u}{6}\,[g(u)+4g(m)+g(v)].$$

Comparo con S₂, la suma de Simpson en dos mitades. Para tramos suficientemente
suaves, uso |S₂−S|/15 como estimación y S₂+(S₂−S)/15 como valor corregido.
Subdivido donde hace falta. Inicio con 32 tramos no uniformes para reducir
alineaciones engañosas con funciones oscilatorias.

Contrasto con Gauss-Legendre de ocho puntos sobre otras particiones. Si dos
controles iniciales no coinciden, refino también Gauss donde cambia su
estimación. Acepto cuando las estimaciones y el desacuerdo quedan dentro de
max(tolerancia_absoluta, tolerancia_relativa·|promedio|).

Hay límites de tiempo, profundidad y evaluaciones. La estimación no es una
cota demostrada: una función con picos más estrechos que las muestras puede
engañar a los controles. No calculo integrales impropias ni valores principales.
La referencia complementaria de cuadratura es [NIST DLMF §3.5](https://dlmf.nist.gov/3.5).
El refinamiento y los controles corresponden a esta implementación; no se
atribuyen como una clase confirmada ni como el algoritmo del apartado de Zill.

## Cómo lo compruebo

Las pruebas usan antiderivadas, simetría y aritmética racional exacta para
100 polinomios deterministas; los ocho ejemplos en tres precisiones; los
seis casos de Zill de arriba; dominios, cancelación, exportaciones e interfaz.
cos(800πx) en [0,1] tiene promedio cero: su antiderivada es sen(800πx)/(800π),
cuya derivada recupera el integrando. Algunas mallas uniformes muestrean
cerca de 1 siempre; por eso duplicar una malla y ver coincidencia no basta.
