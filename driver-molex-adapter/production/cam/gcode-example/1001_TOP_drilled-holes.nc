( pcb2gcode 2.5.0 )
( Software-independent Gcode )

( This file uses 2 drill bit sizes. )
( Bit sizes: [1mm] [1.3mm] )

G94       (Millimeters per minute feed rate.)
G21       (Units == Millimeters.)
G91.1     (Incremental arc distance mode.)
G90       (Absolute coordinates.)
G00 S24000     (RPM spindle speed.)

G00 Z50.00000 (Retract)
T1
M5      (Spindle stop.)
G04 P1.00000
(MSG, Change tool bit to drill size 1mm)
M0      (Temporary machine stop.)
M3      (Spindle on clockwise.)
G0 Z0.30000
G04 P1.00000

G81 R0.30000 Z-2.00000 F540.00000 X129.50000 Y-96.50000
X132.50000 Y-99.50000
X133.44000 Y-102.50000
X129.50000 Y-99.50000
X132.50000 Y-96.50000
X133.44000 Y-93.50000
G80

G00 Z50.00000 (Retract)
T2
M5      (Spindle stop.)
G04 P1.00000
(MSG, Change tool bit to drill size 1.3mm)
M0      (Temporary machine stop.)
M3      (Spindle on clockwise.)
G0 Z0.30000
G04 P1.00000

G81 R0.30000 Z-2.00000 F540.00000 X120.00000 Y-105.40000
X120.00000 Y-100.32000
X120.00000 Y-95.24000
X120.00000 Y-90.16000
X120.00000 Y-85.08000
X120.00000 Y-80.00000
X146.06100 Y-101.56100
X146.06100 Y-96.48100
X146.06100 Y-91.40100
X146.06100 Y-86.32100
X146.06100 Y-81.24100
X146.06100 Y-76.16100
X157.46000 Y-76.16000
X157.46000 Y-81.24000
X157.46000 Y-86.32000
X157.46000 Y-91.40000
X157.46000 Y-96.48000
X157.46000 Y-101.56000
G80

G00 Z50.000 ( All done -- retract )

M5      (Spindle off.)
G04 P1.000000
M9      (Coolant off.)
M2      (Program end.)

