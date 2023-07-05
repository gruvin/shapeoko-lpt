( pcb2gcode 2.5.0 )
( Software-independent Gcode )
( This file uses a mill head of 2.00000mm to drill the 1 hole sizes. )
( Hole sizes: [5mm] )

G94       (Millimeters per minute feed rate.)
G21       (Units == Millimeters.)
G91.1     (Incremental arc distance mode.)
G90       (Absolute coordinates.)
S24000    (RPM spindle speed.)

G01 F880.00000 (Feedrate)
G00 Z50.00000 (Retract to tool change height)
T4
M5        (Spindle stop.)
G04 P1.00000
(MSG, Change tool bit to drill size 2.00000mm)
M6        (Tool change.)
M0        (Temporary machine stop.)
M3        (Spindle on clockwise.)
G04 P1.00000
G00 Z0.30000

G0 X135.00000 Y-71.00000
G1 Z0.40000 F240.00000
G1 F880.00000
G2 X135.00000 Y-71.00000 Z-0.00000 I-1.50000 J0.00000
G2 X135.00000 Y-71.00000 Z-0.40000 I-1.50000 J0.00000
G2 X135.00000 Y-71.00000 Z-0.80000 I-1.50000 J0.00000
G2 X135.00000 Y-71.00000 Z-1.20000 I-1.50000 J0.00000
G2 X135.00000 Y-71.00000 Z-1.60000 I-1.50000 J0.00000
G2 X135.00000 Y-71.00000 I-1.50000 J0.00000
G1 Z0.30000 F240.00000

G0 X135.00000 Y-111.00000
G1 Z0.40000 F240.00000
G1 F880.00000
G2 X135.00000 Y-111.00000 Z-0.00000 I-1.50000 J0.00000
G2 X135.00000 Y-111.00000 Z-0.40000 I-1.50000 J0.00000
G2 X135.00000 Y-111.00000 Z-0.80000 I-1.50000 J0.00000
G2 X135.00000 Y-111.00000 Z-1.20000 I-1.50000 J0.00000
G2 X135.00000 Y-111.00000 Z-1.60000 I-1.50000 J0.00000
G2 X135.00000 Y-111.00000 I-1.50000 J0.00000
G1 Z0.30000 F240.00000

G00 Z50.000000 ( All done -- retract )

M5      (Spindle off.)
G04 P1.000000
M9      (Coolant off.)
M2      (Program end.)

