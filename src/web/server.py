#!/usr/bin/env python3
"""
Servidor Flask – Interfaz web para el Motor Genérico de Máquina de Turing.
Expone una API REST que conecta el frontend con el motor existente.

Uso:
    python src/web/server.py
    Abrir: http://localhost:5000
"""
import os
import sys
import json
from flask import Flask, render_template, request, jsonify

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
SRC  = os.path.join(ROOT, 'src')
sys.path.insert(0, SRC)

from engine.simulator import TuringMachineEngine
from engine.validator import Validator, ValidationError

app = Flask(__name__, template_folder='templates', static_folder='static')
app.secret_key = 'turing-motor-2026-unipamplona'

MACHINES_DIR = os.path.join(ROOT, 'machines')

_engine: TuringMachineEngine = None
_machine_name: str = ''


# ── Utilidades ────────────────────────────────────────────────────────────────

def list_machines():
    return sorted([f for f in os.listdir(MACHINES_DIR) if f.endswith('.json')])


def tape_to_list(engine: TuringMachineEngine):
    tape = engine.tape
    head = engine.head
    if not tape._cells:
        return [{'pos': 0, 'symbol': tape.blank, 'is_head': True}]
    min_pos = min(min(tape._cells.keys()), head) - 2
    max_pos = max(max(tape._cells.keys()), head) + 2
    return [
        {'pos': pos, 'symbol': tape._cells.get(pos, tape.blank), 'is_head': (pos == head)}
        for pos in range(min_pos, max_pos + 1)
    ]


def config_to_dict(config, tape_cells=None):
    return {
        'step': config.step,
        'state': config.state,
        'head_pos': config.head_pos,
        'head_symbol': config.head_symbol,
        'transition': config.transition_applied or '(inicio)',
        'tape': tape_cells or []
    }


# ── Rutas principales ─────────────────────────────────────────────────────────

@app.route('/')
def index():
    machines = list_machines()
    return render_template('index.html', machines=machines)


@app.route('/api/machines', methods=['GET'])
def api_machines():
    machines = list_machines()
    result = []
    for fname in machines:
        path = os.path.join(MACHINES_DIR, fname)
        try:
            with open(path, encoding='utf-8') as f:
                spec = json.load(f)
            result.append({
                'file': fname,
                'name': spec.get('name', fname),
                'mode': spec.get('mode', '?'),
                'description': spec.get('description', ''),
                'states_count': len(spec.get('states', [])),
                'transitions_count': len(spec.get('transitions', [])),
                'tests_count': len(spec.get('tests', [])),
                'imported': spec.get('_imported', False),
            })
        except Exception as e:
            result.append({'file': fname, 'name': fname, 'error': str(e)})
    return jsonify(result)


@app.route('/api/load', methods=['POST'])
def api_load():
    global _engine, _machine_name
    data = request.get_json()
    filename = data.get('file', '')
    input_str = data.get('input', '')

    path = os.path.join(MACHINES_DIR, filename)
    if not os.path.exists(path):
        return jsonify({'error': f'Archivo no encontrado: {filename}'}), 404

    try:
        _engine = TuringMachineEngine.from_file(path)
        _machine_name = _engine.machine.name
        _engine.initialize(input_str)
    except ValidationError as e:
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        return jsonify({'error': str(e)}), 500

    cfg = _engine.trace[0]
    return jsonify({
        'ok': True,
        'machine': _machine_name,
        'mode': _engine.machine.mode,
        'states': sorted(_engine.machine.states),
        'accept_state': _engine.machine.accept,
        'reject_state': _engine.machine.reject,
        'transitions': [
            {'from': t.from_state, 'read': t.read,
             'to': t.to_state, 'write': t.write, 'move': t.move}
            for t in _engine.machine.transitions.values()
        ],
        'current': config_to_dict(cfg, tape_to_list(_engine)),
        'result': None,
        'step_count': 0,
    })


@app.route('/api/import', methods=['POST'])
def api_import():
    """
    Importa una máquina desde JSON enviado como texto en el body.
    Realiza validación formal ANTES de guardar el archivo.
    Devuelve errores detallados si la especificación es inválida.
    """
    data = request.get_json()
    if not data or 'content' not in data:
        return jsonify({'error': 'No se proporcionó contenido JSON.'}), 400

    raw_content = data['content']
    filename    = data.get('filename', 'imported_machine.json')

    # Asegurar extensión .json
    if not filename.endswith('.json'):
        filename += '.json'

    # Sanitizar nombre (evitar path traversal)
    filename = os.path.basename(filename)

    # 1. Parsear JSON — detectar errores de sintaxis
    try:
        spec = json.loads(raw_content)
    except json.JSONDecodeError as e:
        return jsonify({
            'ok': False,
            'stage': 'parse',
            'error': f'JSON inválido: {str(e)}',
            'details': [f'Línea {e.lineno}, columna {e.colno}: {e.msg}']
        }), 400

    # 2. Validación formal con el Validator del motor
    validation_errors = []
    try:
        Validator.validate_spec(spec)
    except ValidationError as e:
        validation_errors.append(str(e))

    # 3. Validaciones adicionales de recomendación (warnings)
    warnings = []
    if not spec.get('description'):
        warnings.append('Recomendación: agrega un campo "description" para documentar la máquina.')
    if not spec.get('tests'):
        warnings.append('Recomendación: incluye casos de prueba en el campo "tests" para verificar la máquina.')
    if len(spec.get('transitions', [])) == 0:
        validation_errors.append('La máquina no tiene transiciones definidas.')

    if validation_errors:
        return jsonify({
            'ok': False,
            'stage': 'validation',
            'error': 'La especificación no pasa la validación formal.',
            'details': validation_errors,
            'warnings': warnings
        }), 400

    # 4. Todo válido: marcar como importada y guardar
    spec['_imported'] = True
    dest_path = os.path.join(MACHINES_DIR, filename)

    # Evitar sobreescribir máquinas integradas
    builtin = {'anbn_decider.json', 'palindrome_decider.json', 'binary_enumerator.json'}
    if filename in builtin:
        base, ext = os.path.splitext(filename)
        filename  = f"{base}_imported{ext}"
        dest_path = os.path.join(MACHINES_DIR, filename)
        warnings.append(f'Nombre en conflicto con máquina integrada. Guardado como "{filename}".')

    with open(dest_path, 'w', encoding='utf-8') as f:
        json.dump(spec, f, ensure_ascii=False, indent=2)

    return jsonify({
        'ok': True,
        'filename': filename,
        'name': spec.get('name', filename),
        'mode': spec.get('mode', '?'),
        'states_count': len(spec.get('states', [])),
        'transitions_count': len(spec.get('transitions', [])),
        'warnings': warnings,
        'message': f'Máquina "{spec.get("name", filename)}" importada y validada correctamente.'
    })


@app.route('/api/step', methods=['POST'])
def api_step():
    global _engine
    if _engine is None:
        return jsonify({'error': 'Motor no inicializado. Carga una máquina primero.'}), 400
    if _engine._result in ('accept', 'reject'):
        return jsonify({
            'ok': True, 'status': _engine._result,
            'current': config_to_dict(_engine.trace[-1], tape_to_list(_engine)),
            'step_count': _engine.step_count,
            'metrics': _engine.get_metrics(), 'done': True
        })
    try:
        status = _engine.step()
        cfg    = _engine.trace[-1]
        done   = status in ('accept', 'reject')
        return jsonify({
            'ok': True, 'status': status,
            'current': config_to_dict(cfg, tape_to_list(_engine)),
            'step_count': _engine.step_count,
            'metrics': _engine.get_metrics() if done else None,
            'done': done
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/run', methods=['POST'])
def api_run():
    global _engine
    if _engine is None:
        return jsonify({'error': 'Motor no inicializado.'}), 400
    data = request.get_json() or {}
    max_steps = int(data.get('max_steps', 10000))
    try:
        result  = _engine.run(max_steps=max_steps)
        metrics = _engine.get_metrics()
        return jsonify({
            'ok': True, 'result': result, 'metrics': metrics,
            'tape': tape_to_list(_engine),
            'current': config_to_dict(_engine.trace[-1], tape_to_list(_engine)),
            'step_count': _engine.step_count,
            'trace': [config_to_dict(c) for c in _engine.trace]
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/reset', methods=['POST'])
def api_reset():
    global _engine
    if _engine is None:
        return jsonify({'error': 'Motor no inicializado.'}), 400
    data = request.get_json() or {}
    try:
        _engine.initialize(data.get('input', ''))
        cfg = _engine.trace[0]
        return jsonify({
            'ok': True,
            'current': config_to_dict(cfg, tape_to_list(_engine)),
            'step_count': 0, 'result': None
        })
    except ValidationError as e:
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/tests', methods=['POST'])
def api_tests():
    global _engine
    if _engine is None:
        return jsonify({'error': 'Motor no inicializado.'}), 400
    try:
        results = _engine.run_test_suite()
        passed  = sum(1 for r in results if r['passed'])
        return jsonify({'ok': True, 'results': results, 'passed': passed, 'total': len(results)})
    except Exception as e:
        return jsonify({'error': str(e)}), 500


if __name__ == '__main__':
    print('\n' + '='*55)
    print('  MOTOR GENÉRICO DE MÁQUINA DE TURING – Interfaz Web')
    print('  Universidad de Pamplona – 2026-1')
    print('  http://localhost:5000')
    print('='*55 + '\n')
    app.run(debug=True, port=5000)
