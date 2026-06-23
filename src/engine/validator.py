from .machine import TuringMachine


class ValidationError(Exception):
    pass


class Validator:
    """
    Módulo de validación formal de la especificación de una Máquina de Turing.
    Verifica que la máquina esté bien formada antes de ejecutarla.
    """

    REQUIRED_FIELDS = [
        'name', 'mode', 'states', 'input_alphabet',
        'tape_alphabet', 'blank', 'start', 'accept', 'reject', 'transitions'
    ]
    VALID_MOVES = {'L', 'R', 'S'}
    VALID_MODES = {'decider', 'recognizer', 'enumerator', 'function'}

    @classmethod
    def validate_spec(cls, spec: dict) -> None:
        """Valida la especificación JSON de la máquina."""
        # 1. Campos obligatorios
        for field in cls.REQUIRED_FIELDS:
            if field not in spec:
                raise ValidationError(f"Campo obligatorio ausente: '{field}'")

        # 2. Modo válido
        if spec['mode'] not in cls.VALID_MODES:
            raise ValidationError(
                f"Modo inválido: '{spec['mode']}'. Válidos: {cls.VALID_MODES}"
            )

        states = set(spec['states'])
        tape_alphabet = set(spec['tape_alphabet'])
        input_alphabet = set(spec['input_alphabet'])

        # 3. El alfabeto de entrada debe ser subconjunto del de cinta
        if not input_alphabet.issubset(tape_alphabet):
            diff = input_alphabet - tape_alphabet
            raise ValidationError(
                f"Símbolos en input_alphabet no presentes en tape_alphabet: {diff}"
            )

        # 4. El símbolo blanco debe estar en el alfabeto de cinta
        if spec['blank'] not in tape_alphabet:
            raise ValidationError(
                f"El símbolo blanco '{spec['blank']}' no está en tape_alphabet"
            )

        # 5. El símbolo blanco NO debe estar en el alfabeto de entrada
        if spec['blank'] in input_alphabet:
            raise ValidationError(
                f"El símbolo blanco '{spec['blank']}' no debe estar en input_alphabet"
            )

        # 6. Estado inicial debe existir
        if spec['start'] not in states:
            raise ValidationError(f"Estado inicial '{spec['start']}' no está en states")

        # 7. Estados de parada deben existir
        if spec['accept'] not in states:
            raise ValidationError(f"Estado de aceptación '{spec['accept']}' no está en states")
        if spec['reject'] not in states:
            raise ValidationError(f"Estado de rechazo '{spec['reject']}' no está en states")

        # 8. Validar cada transición
        seen_keys = set()
        for i, t in enumerate(spec['transitions']):
            for field in ('from', 'read', 'to', 'write', 'move'):
                if field not in t:
                    raise ValidationError(
                        f"Transición {i}: falta el campo '{field}'"
                    )

            if t['from'] not in states:
                raise ValidationError(
                    f"Transición {i}: estado origen '{t['from']}' no está en states"
                )
            if t['to'] not in states:
                raise ValidationError(
                    f"Transición {i}: estado destino '{t['to']}' no está en states"
                )
            if t['read'] not in tape_alphabet:
                raise ValidationError(
                    f"Transición {i}: símbolo leído '{t['read']}' no está en tape_alphabet"
                )
            if t['write'] not in tape_alphabet:
                raise ValidationError(
                    f"Transición {i}: símbolo escrito '{t['write']}' no está en tape_alphabet"
                )
            if t['move'] not in cls.VALID_MOVES:
                raise ValidationError(
                    f"Transición {i}: movimiento '{t['move']}' inválido. Use L, R o S"
                )

            # Detectar transiciones duplicadas (máquinas deterministas)
            key = (t['from'], t['read'])
            if key in seen_keys:
                raise ValidationError(
                    f"Transición duplicada para (estado='{t['from']}', símbolo='{t['read']}')"
                )
            seen_keys.add(key)

    @classmethod
    def validate_input(cls, input_string: str, input_alphabet: set) -> None:
        """Valida que la cadena de entrada use solo símbolos del alfabeto de entrada."""
        for ch in input_string:
            if ch not in input_alphabet:
                raise ValidationError(
                    f"Símbolo '{ch}' en la entrada no pertenece al alfabeto de entrada: {input_alphabet}"
                )
