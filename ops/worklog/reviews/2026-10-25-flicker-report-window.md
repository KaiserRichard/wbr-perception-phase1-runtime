# Lab day 2026-10-25 advisory flicker report

Replay frames are limited to each run’s inclusive live packet timestamp range; transition rates use that window length.
Old replay has zero range/height hysteresis; new replay uses 0.10 m range hysteresis and 0.01 m height hysteresis. Approach transition distance/height are the new decision output at the transition frame (metres).

| Run | Window (s) | Old transitions / min⁻¹ | New transitions / min⁻¹ | Live transitions / min⁻¹ |
|---|---:|---:|---:|---:|
| 2-books46 | 59.84 | 1 / 1.0 | 1 / 1.0 | 1 / 1.0 |
| 3-box13 | 59.91 | 2 / 2.0 | 2 / 2.0 | 2 / 2.0 |
| 4-approach | 59.84 | 4 / 4.0 | 4 / 4.0 | 70 / 70.2 |
| 4-approach-r2 | 59.91 | 156 / 156.2 | 2 / 2.0 | 128 / 128.2 |
| 4-approach-r3 | 59.84 | 218 / 218.6 | 25 / 25.1 | 157 / 157.4 |

## New replay transitions

### 2-books46 (1 transitions)
- 0.133s JUMP_CANDIDATE

### 3-box13 (2 transitions)
- 0.934s STOP_CANDIDATE
- 42.499s NONE

### 4-approach (4 transitions)
- 13.942s UNCERTAIN: distance 1.295 m, height 0.505 m
- 14.075s STOP_CANDIDATE: distance 1.297 m, height 0.506 m
- 47.766s JUMP_CANDIDATE: distance 0.329 m, height 0.105 m
- 48.167s STOP_CANDIDATE: distance 0.706 m, height 0.246 m

### 4-approach-r2 (2 transitions)
- 22.616s UNCERTAIN: distance 1.299 m, height 0.519 m
- 22.750s STOP_CANDIDATE: distance 1.304 m, height 0.521 m

### 4-approach-r3 (25 transitions)
- 1.134s UNCERTAIN: distance 1.171 m, height 0.023 m
- 1.268s NONE: distance 1.171 m, height 0.023 m
- 1.935s UNCERTAIN: distance 1.166 m, height 0.024 m
- 2.268s NONE: distance 1.138 m, height 0.028 m
- 6.872s UNCERTAIN: distance 1.119 m, height 0.029 m
- 7.005s NONE: distance 1.119 m, height 0.029 m
- 7.272s UNCERTAIN: distance 1.081 m, height 0.029 m
- 7.405s NONE: distance 1.081 m, height 0.029 m
- 7.606s UNCERTAIN: distance 1.087 m, height 0.026 m
- 7.739s NONE: distance 1.087 m, height 0.026 m
- 9.207s UNCERTAIN: distance 1.075 m, height 0.029 m
- 9.407s NONE: distance 1.205 m, height 0.073 m
- 9.740s UNCERTAIN: distance 1.159 m, height 0.052 m
- 9.941s NONE: distance 1.251 m, height 0.084 m
- 10.274s UNCERTAIN: distance 1.225 m, height 0.059 m
- 10.408s JUMP_CANDIDATE: distance 1.326 m, height 0.109 m
- 10.541s STOP_CANDIDATE: distance 1.360 m, height 0.138 m
- 10.941s JUMP_CANDIDATE: distance 1.247 m, height 0.090 m
- 11.208s STOP_CANDIDATE: distance 1.353 m, height 0.132 m
- 13.877s JUMP_CANDIDATE: distance 1.227 m, height 0.091 m
- 14.210s STOP_CANDIDATE: distance 1.333 m, height 0.131 m
- 18.013s JUMP_CANDIDATE: distance 1.179 m, height 0.090 m
- 18.480s STOP_CANDIDATE: distance 1.286 m, height 0.131 m
- 39.028s JUMP_CANDIDATE: distance 1.255 m, height 0.088 m
- 39.162s STOP_CANDIDATE: distance 1.287 m, height 0.271 m
