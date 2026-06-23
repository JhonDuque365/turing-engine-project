from dataclasses import dataclass
from typing import Optional


@dataclass
class Transition:
    """
    Representa una regla de transición de la Máquina de Turing.
    (q, a) -> (r, b, D)
    """
    from_state: str
    read: str
    to_state: str
    write: str
    move: str  # 'L', 'R' o 'S'

    def __str__(self):
        return f"({self.from_state}, {self.read}) -> ({self.to_state}, {self.write}, {self.move})"


@dataclass
class Configuration:
    """
    Fotografía exacta de la ejecución en un instante.
    Contiene: estado, contenido de cinta, posición del cabezal,
    número de paso y transición aplicada.
    """
    step: int
    state: str
    tape_display: str
    head_pos: int
    transition_applied: Optional[str]
    head_symbol: str

    def __str__(self):
        trans = self.transition_applied if self.transition_applied else "(inicio)"
        return (
            f"  Paso {self.step:>4} | Estado: {self.state:<12} "
            f"| Símbolo bajo cabezal: '{self.head_symbol}' "
            f"| Transición: {trans}"
        )


class TuringMachine:
    """
    Modelo formal de una Máquina de Turing:
    M = (Q, Σ, Γ, δ, q0, qaccept, qreject)
    """

    def __init__(self, spec: dict):
        self.name: str = spec.get('name', 'unnamed')
        self.mode: str = spec.get('mode', 'decider')
        self.description: str = spec.get('description', '')
        self.states: set[str] = set(spec['states'])
        self.input_alphabet: set[str] = set(spec['input_alphabet'])
        self.tape_alphabet: set[str] = set(spec['tape_alphabet'])
        self.blank: str = spec['blank']
        self.start: str = spec['start']
        self.accept: str = spec['accept']
        self.reject: str = spec['reject']
        self.tests: list[dict] = spec.get('tests', [])

        # Construir mapa de transiciones: {(estado, símbolo): Transition}
        self.transitions: dict[tuple, Transition] = {}
        for t in spec.get('transitions', []):
            key = (t['from'], t['read'])
            self.transitions[key] = Transition(
                from_state=t['from'],
                read=t['read'],
                to_state=t['to'],
                write=t['write'],
                move=t['move']
            )

    def get_transition(self, state: str, symbol: str) -> Optional[Transition]:
        return self.transitions.get((state, symbol))

    def is_halting(self, state: str) -> bool:
        return state in (self.accept, self.reject)

    def __repr__(self):
        return (
            f"TuringMachine(name='{self.name}', mode='{self.mode}', "
            f"states={len(self.states)}, transitions={len(self.transitions)})"
        )
