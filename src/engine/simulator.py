import json
from .tape import Tape
from .machine import TuringMachine, Configuration
from .validator import Validator, ValidationError


class TuringMachineEngine:
    """
    Motor genérico de simulación de Máquinas de Turing.
    Implementa ejecución paso a paso con trazabilidad completa.

    Resultados posibles:
      - 'accept'                    : la máquina llegó al estado de aceptación
      - 'reject'                    : la máquina llegó al estado de rechazo
      - 'timeout_without_conclusion': no se detuvo dentro del límite de pasos
        (NO equivale a rechazo en reconocedores)
    """

    def __init__(self, spec: dict):
        Validator.validate_spec(spec)
        self.machine = TuringMachine(spec)
        self._initialized = False

        # Estado de ejecución
        self.tape: Tape = None
        self.head: int = 0
        self.state: str = ''
        self.step_count: int = 0
        self.trace: list[Configuration] = []

        # Métricas
        self._left_moves: int = 0
        self._right_moves: int = 0
        self._result: str = ''

    @classmethod
    def from_file(cls, filepath: str) -> 'TuringMachineEngine':
        """Carga un motor desde un archivo JSON."""
        with open(filepath, 'r', encoding='utf-8') as f:
            spec = json.load(f)
        return cls(spec)

    def initialize(self, input_string: str) -> None:
        """Inicializa la cinta y el estado para una nueva ejecución."""
        Validator.validate_input(input_string, self.machine.input_alphabet)
        self.tape = Tape(blank=self.machine.blank)
        self.tape.write_input(input_string)
        self.head = 0
        self.state = self.machine.start
        self.step_count = 0
        self.trace = []
        self._left_moves = 0
        self._right_moves = 0
        self._result = ''
        self._initialized = True

        # Guardar configuración inicial
        self.trace.append(Configuration(
            step=0,
            state=self.state,
            tape_display=self.tape.get_display(self.head),
            head_pos=self.head,
            transition_applied=None,
            head_symbol=self.tape.read(self.head)
        ))

    def step(self) -> str:
        """
        Ejecuta una sola transición.
        Retorna: 'accept', 'reject' o 'running'.
        """
        if not self._initialized:
            raise RuntimeError("Llama a initialize() antes de step()")

        if self.state == self.machine.accept:
            self._result = 'accept'
            return 'accept'
        if self.state == self.machine.reject:
            self._result = 'reject'
            return 'reject'

        symbol = self.tape.read(self.head)
        transition = self.machine.get_transition(self.state, symbol)

        if transition is None:
            # No hay transición definida: rechazar implícitamente
            self.state = self.machine.reject
            self._result = 'reject'
            return 'reject'

        # Aplicar la transición
        self.tape.write(self.head, transition.write)
        prev_state = self.state
        self.state = transition.to_state

        if transition.move == 'R':
            self.head += 1
            self._right_moves += 1
        elif transition.move == 'L':
            self.head -= 1
            self._left_moves += 1
        # 'S' -> el cabezal no se mueve

        self.step_count += 1

        # Registrar la configuración
        self.trace.append(Configuration(
            step=self.step_count,
            state=self.state,
            tape_display=self.tape.get_display(self.head),
            head_pos=self.head,
            transition_applied=str(transition),
            head_symbol=self.tape.read(self.head)
        ))

        if self.state == self.machine.accept:
            self._result = 'accept'
            return 'accept'
        if self.state == self.machine.reject:
            self._result = 'reject'
            return 'reject'

        return 'running'

    def run(self, max_steps: int = 10000) -> str:
        """
        Ejecuta la máquina hasta detenerse o alcanzar el límite de pasos.
        IMPORTANTE: 'timeout_without_conclusion' NO equivale a rechazo.
        """
        if not self._initialized:
            raise RuntimeError("Llama a initialize() antes de run()")

        while self.step_count < max_steps:
            status = self.step()
            if status in ('accept', 'reject'):
                return status

        self._result = 'timeout_without_conclusion'
        return 'timeout_without_conclusion'

    def get_metrics(self) -> dict:
        """Retorna las métricas de la ejecución actual."""
        return {
            'resultado': self._result,
            'pasos_ejecutados': self.step_count,
            'celdas_visitadas': self.tape.cells_visited() if self.tape else 0,
            'celdas_no_blancas': self.tape.count_non_blank() if self.tape else 0,
            'movimientos_izquierda': self._left_moves,
            'movimientos_derecha': self._right_moves,
            'cinta_final': self.tape.get_final_content() if self.tape else '',
            'longitud_entrada': len(self.trace[0].head_symbol) if self.trace else 0,
        }

    def print_trace(self, max_steps: int = None) -> None:
        """Imprime la traza de ejecución."""
        steps = self.trace if max_steps is None else self.trace[:max_steps + 1]
        print(f"\n{'='*70}")
        print(f"  TRAZA DE EJECUCIÓN - Máquina: {self.machine.name}")
        print(f"{'='*70}")
        for config in steps:
            print(config)
            print(config.tape_display)
            print()
        print(f"  Resultado final: {self._result.upper()}")
        print(f"{'='*70}\n")

    def run_test_suite(self) -> list[dict]:
        """Ejecuta todos los casos de prueba definidos en la especificación JSON."""
        results = []
        for test in self.machine.tests:
            input_str = test['input']
            expected = test['expected']
            try:
                self.initialize(input_str)
                actual = self.run(max_steps=10000)
            except Exception as e:
                actual = f'error: {e}'
            passed = actual == expected
            results.append({
                'input': repr(input_str),
                'expected': expected,
                'actual': actual,
                'passed': passed
            })
        return results
