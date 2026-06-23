# =============================================================================
# machine.py  –  Modelo formal de la Máquina de Turing
# =============================================================================
# Define las tres estructuras de datos fundamentales:
#   - Transition : una regla (q, a) -> (r, b, D)
#   - Configuration : foto instantánea del estado de ejecución
#   - TuringMachine : la máquina completa M = (Q, Σ, Γ, δ, q0, qacc, qrej)
# =============================================================================

from dataclasses import dataclass
from typing import Optional


@dataclass
class Transition:
    """
    Representa una regla de transición de la forma:
        (estado_origen, símbolo_leído) -> (estado_destino, símbolo_escrito, dirección)

    Ejemplo: (q0, 'a') -> (q1, 'X', 'R')
    Significa: si estoy en q0 y leo 'a', voy a q1, escribo 'X' y muevo el cabezal a la derecha.

    La dirección puede ser:
        'R' = mover derecha (right)
        'L' = mover izquierda (left)
        'S' = quedarse (stay, sin movimiento)
    """
    from_state: str   # Estado de origen
    read: str         # Símbolo que debe leer el cabezal para activarse
    to_state: str     # Estado al que pasa la máquina
    write: str        # Símbolo que se escribe en la cinta
    move: str         # Dirección del movimiento: 'L', 'R' o 'S'

    def __str__(self):
        # Representación legible para la traza: (q0, a) -> (q1, X, R)
        return f"({self.from_state}, {self.read}) -> ({self.to_state}, {self.write}, {self.move})"


@dataclass
class Configuration:
    """
    Fotografía exacta de la ejecución en un instante de tiempo.

    Una configuración captura todo lo necesario para reproducir
    o explicar el estado de la máquina en un paso determinado:
        - qué paso es (número secuencial)
        - en qué estado está la máquina
        - qué hay en la cinta (representación visual)
        - dónde está el cabezal
        - qué símbolo lee el cabezal en este momento
        - qué transición se aplicó para llegar aquí
    """
    step: int                        # Número de paso (0 = configuración inicial)
    state: str                       # Estado actual de la máquina
    tape_display: str                # Representación visual de la cinta
    head_pos: int                    # Posición absoluta del cabezal
    transition_applied: Optional[str]# Transición que causó esta configuración
    head_symbol: str                 # Símbolo que el cabezal ve ahora

    def __str__(self):
        trans = self.transition_applied if self.transition_applied else "(inicio)"
        return (
            f"  Paso {self.step:>4} | Estado: {self.state:<12} "
            f"| Símbolo bajo cabezal: '{self.head_symbol}' "
            f"| Transición: {trans}"
        )


class TuringMachine:
    """
    Modelo formal completo de una Máquina de Turing determinista de una cinta:

        M = (Q, Σ, Γ, δ, q0, q_accept, q_reject)

    donde:
        Q          = conjunto de estados
        Σ          = alfabeto de entrada (símbolos que puede recibir como input)
        Γ          = alfabeto de cinta (Σ ⊂ Γ, incluye marcas como X, Y y el blanco)
        δ          = función de transición: Q x Γ -> Q x Γ x {L, R, S}
        q0         = estado inicial
        q_accept   = estado de aceptación
        q_reject   = estado de rechazo

    La máquina se carga desde un archivo JSON. Las transiciones se indexan
    en un diccionario para acceso O(1): {(estado, simbolo) -> Transition}.
    """

    def __init__(self, spec: dict):
        # --- Metadatos descriptivos ---
        self.name: str        = spec.get('name', 'unnamed')
        self.mode: str        = spec.get('mode', 'decider')   # decider / recognizer / enumerator / function
        self.description: str = spec.get('description', '')

        # --- Componentes formales de la MT ---
        self.states: set[str]         = set(spec['states'])          # Q
        self.input_alphabet: set[str] = set(spec['input_alphabet'])  # Σ
        self.tape_alphabet: set[str]  = set(spec['tape_alphabet'])   # Γ
        self.blank: str               = spec['blank']                # símbolo blanco ∈ Γ
        self.start: str               = spec['start']                # q0
        self.accept: str              = spec['accept']               # q_accept
        self.reject: str              = spec['reject']               # q_reject

        # Casos de prueba definidos en el JSON (para la suite de tests)
        self.tests: list[dict] = spec.get('tests', [])

        # --- Construir la función de transición δ como diccionario ---
        # Clave: (estado_origen, simbolo_leido)  →  Valor: Transition
        # Este indexado permite buscar la transición aplicable en O(1)
        # en cada paso de la simulación.
        self.transitions: dict[tuple, Transition] = {}
        for t in spec.get('transitions', []):
            key = (t['from'], t['read'])      # par (estado, simbolo)
            self.transitions[key] = Transition(
                from_state=t['from'],
                read=t['read'],
                to_state=t['to'],
                write=t['write'],
                move=t['move']
            )

    def get_transition(self, state: str, symbol: str) -> Optional[Transition]:
        """
        Busca la transición definida para el par (estado, símbolo).
        Retorna None si no existe ninguna transición aplicable,
        lo que en una MT determinista implica rechazo implícito.
        """
        return self.transitions.get((state, symbol))

    def is_halting(self, state: str) -> bool:
        """Indica si el estado dado es un estado de parada (accept o reject)."""
        return state in (self.accept, self.reject)

    def __repr__(self):
        return (
            f"TuringMachine(name='{self.name}', mode='{self.mode}', "
            f"states={len(self.states)}, transitions={len(self.transitions)})"
        )
