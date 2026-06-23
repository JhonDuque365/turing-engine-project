# Trazas de Ejecución

Este directorio contiene trazas exportadas de ejecuciones del motor.

## Formato de traza

Cada traza registra la secuencia de configuraciones:

```
Paso | Estado       | Símbolo bajo cabezal | Transición aplicada
  0  | q0           | 'a'                  | (inicio)
  1  | q1           | 'a'                  | (q0, a) -> (q1, X, R)
  2  | q1           | 'b'                  | (q1, a) -> (q1, a, R)
  ...
```

## Traza esperada para ANBN con entrada `aabb`

| Paso | Estado  | Cinta     | Cabezal |
|------|---------|-----------|---------|
| 0    | q0      | aabb      | pos 0   |
| 1    | q1      | Xabb      | pos 1   |
| 2    | q1      | Xabb      | pos 2   |
| 3    | q2      | XaYb      | pos 2   |
| 4-6  | q0      | regresa   | pos 0   |
| 7    | q1      | XXYb      | avanza  |
| 8    | q2      | XXYY      | regresa |
| 9-12 | q0      | no hay a  | blanco  |
| 13-16| q3      | verifica  | inicio  |
| 17   | qaccept | XXYY      | parada  |
