# =============================================================================
# validator.py  –  Validación formal de especificaciones y entradas
# =============================================================================
# Antes de ejecutar cualquier máquina, el sistema verifica que su especificación
# sea formalmente correcta. Esto evita errores en tiempo de ejecución y
# garantiza que el motor siempre trabaje sobre máquinas bien definidas.
#
# Se validan dos cosas distintas:
#   1. validate_spec(spec)         – que la máquina esté bien construida
#   2. validate_input(w, alphabet) – que la cadena de entrada sea válida
# =============================================================================


class ValidationError(Exception):
    """Excepción lanzada cuando la especificación o la entrada no son válidas."""
    pass


class Validator:
    """
    Validador formal de especificaciones de Máquinas de Turing.

    Verifica que todos los componentes de la máquina sean consistentes
    antes de permitir cualquier ejecución.
    """

    # Campos obligatorios que todo JSON de máquina debe tener
    REQUIRED_FIELDS = [
        'name', 'mode', 'states', 'input_alphabet',
        'tape_alphabet', 'blank', 'start', 'accept', 'reject', 'transitions'
    ]

    # Modos de máquina reconocidos por el sistema
    VALID_MODES = {'decider', 'recognizer', 'enumerator', 'function'}

    @classmethod
    def validate_spec(cls, spec: dict) -> None:
        """
        Valida la especificación completa de una Máquina de Turing.

        Verificaciones realizadas:
          1. Que existan todos los campos obligatorios.
          2. Que el modo sea uno de los modos válidos.
          3. Que el símbolo blanco pertenezca al alfabeto de cinta.
          4. Que el alfabeto de entrada sea subconjunto del alfabeto de cinta.
          5. Que los estados inicial, de aceptación y de rechazo existan en Q.
          6. Que los estados de aceptación y rechazo sean distintos.
          7. Que cada transición tenga todos sus campos requeridos.
          8. Que los estados y símbolos de las transiciones sean válidos.
          9. Que no haya transiciones duplicadas (determinismo).
        """
        # --- 1. Campos obligatorios ---
        for field in cls.REQUIRED_FIELDS:
            if field not in spec:
                raise ValidationError(f"Campo obligatorio faltante: '{field}'")

        states         = set(spec['states'])
        input_alphabet = set(spec['input_alphabet'])
        tape_alphabet  = set(spec['tape_alphabet'])
        blank          = spec['blank']
        start          = spec['start']
        accept         = spec['accept']
        reject         = spec['reject']
        mode           = spec['mode']

        # --- 2. Modo válido ---
        if mode not in cls.VALID_MODES:
            raise ValidationError(
                f"Modo '{mode}' no válido. Modos aceptados: {cls.VALID_MODES}"
            )

        # --- 3. El blanco debe estar en el alfabeto de cinta ---
        # El símbolo blanco es un símbolo especial de Γ, no puede estar en Σ.
        if blank not in tape_alphabet:
            raise ValidationError(
                f"El símbolo blanco '{blank}' no está en tape_alphabet."
            )
        if blank in input_alphabet:
            raise ValidationError(
                f"El símbolo blanco '{blank}' no puede estar en input_alphabet."
            )

        # --- 4. El alfabeto de entrada debe ser subconjunto del de cinta ---
        # Todo símbolo que puede aparecer en la entrada también debe poder
        # estar en la cinta durante la ejecución.
        extra = input_alphabet - tape_alphabet
        if extra:
            raise ValidationError(
                f"Símbolos en input_alphabet que no están en tape_alphabet: {extra}"
            )

        # --- 5. Los estados especiales deben existir en Q ---
        for label, state in [('start', start), ('accept', accept), ('reject', reject)]:
            if state not in states:
                raise ValidationError(
                    f"El estado '{state}' ({label}) no está en el conjunto de estados."
                )

        # --- 6. Aceptación y rechazo deben ser estados distintos ---
        if accept == reject:
            raise ValidationError(
                "El estado de aceptación y de rechazo no pueden ser el mismo."
            )

        # --- 7, 8 y 9. Validar cada transición ---
        seen_keys = set()  # Para detectar transiciones duplicadas

        for i, t in enumerate(spec.get('transitions', [])):
            # Verificar que la transición tenga todos sus campos
            for field in ['from', 'read', 'to', 'write', 'move']:
                if field not in t:
                    raise ValidationError(
                        f"Transición #{i}: falta el campo '{field}'."
                    )

            from_s = t['from']
            read_s = t['read']
            to_s   = t['to']
            write_s= t['write']
            move_s = t['move']

            # El estado de origen debe existir en Q
            if from_s not in states:
                raise ValidationError(
                    f"Transición #{i}: estado origen '{from_s}' no está en states."
                )

            # El estado destino debe existir en Q
            if to_s not in states:
                raise ValidationError(
                    f"Transición #{i}: estado destino '{to_s}' no está en states."
                )

            # El símbolo leído debe pertenecer al alfabeto de cinta Γ
            if read_s not in tape_alphabet:
                raise ValidationError(
                    f"Transición #{i}: símbolo leído '{read_s}' no está en tape_alphabet."
                )

            # El símbolo escrito debe pertenecer al alfabeto de cinta Γ
            if write_s not in tape_alphabet:
                raise ValidationError(
                    f"Transición #{i}: símbolo escrito '{write_s}' no está en tape_alphabet."
                )

            # La dirección solo puede ser L, R o S
            if move_s not in ('L', 'R', 'S'):
                raise ValidationError(
                    f"Transición #{i}: dirección '{move_s}' inválida. Use L, R o S."
                )

            # Detectar duplicados: en una MT determinista no puede haber dos
            # transiciones para el mismo par (estado, símbolo).
            key = (from_s, read_s)
            if key in seen_keys:
                raise ValidationError(
                    f"Transición duplicada para ({from_s}, '{read_s}'). "
                    f"Una MT determinista no puede tener dos reglas para el mismo par."
                )
            seen_keys.add(key)

    @classmethod
    def validate_input(cls, input_string: str, input_alphabet: set) -> None:
        """
        Valida que la cadena de entrada use solo símbolos del alfabeto de entrada.

        La cadena vacía (epsilon ε) siempre es válida.
        Si algún carácter no pertenece a Σ, se lanza ValidationError.
        """
        # La cadena vacía representa epsilon: siempre es válida
        if input_string == '':
            return

        # Verificar cada caracter individualmente
        for ch in input_string:
            if ch not in input_alphabet:
                raise ValidationError(
                    f"El símbolo '{ch}' no pertenece al alfabeto de entrada {input_alphabet}. "
                    f"Cadena rechazada antes de iniciar la ejecución."
                )
