; use millimeters
G21

; set bed temp and turn on heating pads
M140 S27
; home xyz
G28

T2
G90
G0 Z10 F3000
G0 X20 Y200 F3000
G0 Z0 F3000
G91
G1 X0 Y-20 F180 E5 
G0 Z10 F3000

; set bed temp and turn off heating pads
M140 S0
