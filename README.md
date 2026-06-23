# Motor Genérico de Máquina de Turing

**Asignatura:** Teoría de la Computación  
**Programa:** Ingeniería de Sistemas – Universidad de Pamplona – 2026-1  
**Profesor:** Omar Portilla Jaimes  
**Autor:** Jhon Duque  

---

## Descripción

Plataforma que permite especificar, ejecutar y analizar **Máquinas de Turing** aplicadas a problemas clásicos de ciencias de la computación. Las máquinas se definen en formato JSON declarativo y se ejecutan sobre un motor genérico con trazabilidad completa.

## Estructura del proyecto

```
turing-engine-project/
├── README.md
├── requirements.txt
├── src/
│   ├── engine/
│   │   ├── tape.py          # Cinta infinita (dict)
│   │   ├── machine.py       # Modelo formal M=(Q,Σ,Γ,δ,q0,qa,qr)
│   │   ├── simulator.py     # Motor genérico de simulación
│   │   ├── validator.py     # Validador formal de especificaciones
│   │   └── enumerator.py    # Enumerador de cadenas binarias
│   ├── ui/
│   │   └── app.py           # Interfaz de consola interactiva
│   └── web/
│       ├── server.py        # Servidor Flask (interfaz web)
│       ├── templates/
│       │   └── index.html
│       └── static/
│           ├── style.css
│           └── app.js
├── machines/
│   ├── anbn_decider.json
│   ├── palindrome_decider.json
│   └── binary_enumerator.json
├── tests/
│   ├── test_anbn.py
│   └── test_palindrome.py
├── docs/
│   └── informe.pdf
└── examples/
    └── traces/
```

---

## Instalación

```bash
git clone https://github.com/JhonDuque365/turing-engine-project.git
cd turing-engine-project
pip install -r requirements.txt
```

---

## Uso – Interfaz Web (Flask) ⭐

```bash
python src/web/server.py
```

Luego abrir en el navegador: **http://localhost:5000**

La interfaz web permite:
- Seleccionar cualquier máquina de la biblioteca
- Ver la información formal de la máquina (modo, estados, transiciones)
- Ingresar una cadena de entrada
- Ejecutar **paso a paso** con animación de la cinta
- Ejecutar completo hasta detenerse
- Ver la **traza completa** de configuraciones
- Consultar **métricas** de ejecución
- Ejecutar la **suite de pruebas** integrada
- Ver la **función de transición δ** completa de cada máquina

---

## Uso – Interfaz de consola

```bash
python src/ui/app.py
```

---

## Uso – Pruebas unitarias

```bash
python -m unittest tests/test_anbn.py -v
python -m unittest tests/test_palindrome.py -v
```

---

## Máquinas implementadas

| Máquina | Tipo | Lenguaje/Función |
|---|---|---|
| `anbn_decider` | Decidible | L = { aⁿbⁿ \| n ≥ 0 } |
| `palindrome_decider` | Decidible | PAL = { w \| w = wᴿ } sobre {0,1} |
| `binary_enumerator` | Enumerable | Cadenas binarias por longitud |

## Nota conceptual importante

> Si la máquina no se detiene dentro del límite de pasos, el resultado es `timeout_without_conclusion`, **NO** rechazo. Rechazar y no detenerse son comportamientos formalmente distintos.
