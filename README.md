# Motor Genérico de Máquina de Turing

**Asignatura:** Teoría de la Computación  
**Programa:** Ingeniería de Sistemas  
**Universidad:** Universidad de Pamplona  
**Periodo:** 2026-1  
**Profesor:** Omar Portilla Jaimes  

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
│   │   ├── tape.py          # Estructura de la cinta
│   │   ├── machine.py       # Modelo formal de la MT
│   │   ├── simulator.py     # Motor de simulación
│   │   └── validator.py     # Validador formal
│   └── ui/
│       └── app.py           # Interfaz de consola
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

## Instalación

```bash
git clone https://github.com/JhonDuque365/turing-engine-project.git
cd turing-engine-project
pip install -r requirements.txt
```

## Uso

### Interfaz interactiva de consola
```bash
python src/ui/app.py
```

### Ejecución directa
```python
from src.engine.simulator import TuringMachineEngine
import json

with open('machines/anbn_decider.json') as f:
    spec = json.load(f)

engine = TuringMachineEngine(spec)
engine.initialize('aabb')
result = engine.run(max_steps=1000)
print(result)  # accept
```

## Máquinas implementadas

| Máquina | Tipo | Lenguaje/Función |
|---|---|---|
| `anbn_decider` | Decidible | L = { aⁿbⁿ \| n ≥ 0 } |
| `palindrome_decider` | Decidible | PAL = { w \| w = wᴿ } sobre {0,1} |
| `binary_enumerator` | Enumerable | Cadenas binarias por longitud |

## Modos de máquina

- `decider` → siempre acepta o rechaza
- `recognizer` → acepta entradas del lenguaje, puede no detenerse en negativas
- `enumerator` → genera cadenas de un lenguaje
- `function` → computa una salida en la cinta

> ⚠️ **Importante:** Si la máquina no se detiene dentro del límite de pasos, el resultado es `timeout_without_conclusion`, **no** rechazo.
