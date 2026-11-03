# Controller BOM — review sheet

- source: `controller.kicad_pro` (4 sheets, 63 fitted BOM lines)
- prices: element14 NZ store, list price, NZD (AUD/GBP where NZ had no stock)
- **estimated total: $205.45** (mixed currency, indicative only)

## Status

| | count |
|---|---|
| lines resolved with confidence | 63 |
| lines changed vs the schematic | 28 |
| lines needing your decision | 0 |
| parts not fitted (DNP / net-tie) | 29 |

Pick-and-place (SMD): $131.17  |  hand solder (THT): $74.28

## Needs your decision

## Changed vs the schematic

These lines are **not** what the schematic's `E14MFR#` field said.

| refs | value | footprint | part | why |
|---|---|---|---|---|
| C2-C3 | 1u/50V | C_0603_1608Metric | `0603B105K500CT` | reviewed: MULTICOMP consolidation: 1uF 50V 0603 X7R, replaces TDK C1608X5R1H105K080AB |
| C4 | 100u/35V | CP_Elec_8x10.5_DOT | `MCVVT035M101FB3L` | reviewed: MULTICOMP consolidation: 100uF 35V SMD electrolytic, 8.0mm dia x 10.5mm - matches the CP_Elec_8x10.5 footprint exactly |
| C7 | 22u/16V | C_1206_3216Metric | `1206X226K160CT` | reviewed: MULTICOMP consolidation (option b, chosen by Bryan): 22uF 16V 1206 X5R. MULTICOMP has no 22uF/25V 1206, so the schematic Value was changed t |
| C8 | 68u/35V | CP_Elec_6.3x7.7_DOT | `MCVVT035M680EA6L` | reviewed: MULTICOMP consolidation: 68uF 35V SMD electrolytic, 6.3mm dia x 7.7mm - matches the CP_Elec_6.3x7.7 footprint exactly |
| C15 | 1u | C_0603_1608Metric | `0603B105K500CT` | reviewed: MULTICOMP consolidation: 1uF 50V 0603 X7R |
| C16,C24-C26 | 100n | C_0603_1608Metric | `MC0603B104K500CT` | reviewed: MULTICOMP consolidation: 100nF 50V 0603 X7R, unified with C1 (same part, cheaper of the two listings) |
| C17-C21 | 100n | C_0402_1005Metric_Pad0.74x0.62mm_H | `0402B104K500CT` | reviewed: MULTICOMP consolidation: 100nF 50V 0402 X7R, replaces Murata GRM155R71H104KE14D |
| D6 | SS24A+ | D_SMA_DOT | `SS24A` | reviewed: Value was 'SS24A+'; the trailing '+' is a lead-free suffix, the element14 MPN is SS24A. 40V 2A SMA matches the D_SMA footprint |
| D7-D8,D11 | BAT54JFILM | D_SOD-523_DOT | `BAT54KFILM` | reviewed: BAT54KFILM is the SOD-523 version of the same BAT54 die (40V 300mA single Schottky). BAT54JFILM is SOD-323 - 1.9mm pad pitch vs the 1.4mm SO |
| D9-D10 | YELLOW | LED_0402_DOT | `150040YS73240` | reviewed: Value was just 'YELLOW'; footprint is LED_0402. Kingbright 150040YS73240 is a yellow 0402 LED |
| J1-J2 | CONN_23W_SOCKET | PinSocket_1x23_P2.54mm_Vertical | `HC-PM254-8.5H-1x23PZ` | not from element14: 23-way 2.54mm single-row socket, 8.5mm insulation height, 3mm tails, gold-flash contacts. 260 in stock, MOQ 5 = $1.15. Socket hang |
| J3 | CONN_23W_PIN | PinHeader_1x23_P2.54mm_Vertical | `TSW-123-17-T-S` | not from element14: 23-way single-row 2.54mm THT header, .025in square posts, tin, lead style 17 = .620in (15.75mm) post above a 2.54mm plastic body,  |
| J7 | DB25_PINS_MountingHoles | DSUB-25_Pins_Horizontal_P2.77x2.84 | `5504F1-25P-02A-03` | reviewed: Male DB25 plug, right angle, THT, 25 contacts - confirmed correct (this was the original schematic part). Gender=Plug, 'Through Hole Mount R |
| J15 | JST_B2B-XH | TerminalBlock_Phoenix_MPT-0,5-4-2. | `1725672` | reviewed: symbol is Conn_01x04 with a Phoenix MPT-0,5/4-2,54 footprint, but Value/MPN were the stale 2-pin JST B2B-XH. Corrected to the 4-way part use |
| J22 | uISP | ISP_SMD_100mil | `2213SM-06G-TB` | reviewed: ISP_SMD_100mil is a 2x3 2.54mm SMD header |
| J23 | ISP | ISP_SMD_100mil | `2213SM-06G-TB` | reviewed: ISP_SMD_100mil is a 2x3 2.54mm SMD header |
| JP1 | Jumper_2_Bridged | PinHeader_2x01_P2.54mm_Vertical | `22-23-2021` | reviewed: PinHeader_2x01_P2.54mm_Vertical - Molex KK 1x02 2.54mm THT. Replaces 640456-2, which has MOQ 100 (bulk) - we want individual parts |
| JP2 | GND_ISO | PinHeader_1x02_P2.54mm_Vertical | `22-23-2021` | reviewed: PinHeader_1x02_P2.54mm_Vertical - same 2-pin header as JP1; MOQ 10 not 100 |
| K1 | OJS-SH-124HMF | Relay_SPST_OJS_24V_10A | `OJ-SS-124HM,000` | reviewed: OJ series, VENTED, 24VDC, SPST-NO 10A, THT solder terminals - the closest in-stock element14 equivalent. Sealing is not required (Bryan). Co |
| L2 | CG0603MLC-05E | R_0805_2012Metric_Pad1.20x1.40mm_H | `VC080505A150DP` | reviewed: 0805 MLV, 5.6V working / 18V clamp - closest 0805 equivalent of the 0603 ChipGuard it replaces. NOTE: the schematic Value still says CG0603M |
| L3 | 10uH | L_0603_1608Metric | `MLZ1608M100WT000` | reviewed: 10uH 0603 multilayer, 250mA, 1.05 ohm. L3 sits between +5VA and the ATmega328P AVCC pin, so the current is only a few mA - the 250mA rating  |
| Q2 | FDD5614P | TO-252-2 | `SUD19P06-60-GE3` | reviewed: FDD5614P (60V P-ch, 15A, 0.1ohm, TO-252) is No Longer Manufactured. SUD19P06-60-GE3 is 60V, 18.3A, 0.06ohm, same TO-252 footprint - meets or |
| R18-R19 | 5K6 | R_0603_1608Metric | `MCSR06X5601FTL` | reviewed: MULTICOMP consolidation: 5K6 0603 1% thick film, replaces the Vishay CRCW06035K60FKEA |
| SW3 | RESET | SW_Push_1P1T_NO_XUNPU_TS-1088-AR02 | `TS-1088-AR02016` | not from element14: 3.9x3.0x2.0mm SMD vertical tactile, SPST-NO 12V/50mA. Footprint SW_Push_1P1T_NO_XUNPU_TS-1088-AR02016 (2 pads 1.05x2.00mm, 3.40mm  |
| U7 | ATmega16U2-A | VQFN-32-1EP_4x4mm_P0.4mm_EP2.8x2.8 | `ATMEGA16U2-MU` | reviewed: Value 'ATmega16U2-A' is the TQFP-32 part but the footprint is VQFN-32; -MU is the VQFN package |
| U8 | ADUM4160 | SOIC-16W_7.5x10.3mm_P1.27mm | `ADUM4160BRWZ` | reviewed: footprint is SOIC-16W (wide); ADuM4160BRIZ is the narrow-SOIC variant and would not fit |
| Y1 | Crystal_SMD_WE_CFPX-104-4Pin_5.0x3.2mm | Crystal_SMD_WE_CFPX-104-4Pin_5.0x3 | `ABM3-16.000MHZ-D2Y-T` | reviewed: Value was unset (it held the footprint name). Footprint is a 5.0x3.2mm 4-pad crystal; ABM3 is 16MHz in exactly that package |
| Y2 | CSTCE16M0V53-R0 16MHZ | Crystal_SMD_WE_CFPX-104-4Pin_5.0x3 | `ABM3-16.000MHZ-D2Y-T` | reviewed: Value was a CSTCE16M0V53-R0 3-terminal resonator (No Longer Manufactured) but the footprint is the same 4-pad 5.0x3.2mm crystal as Y1, so tr |

## Assumptions applied

- Passive substitution allowed (R/C/L/D): package + value + voltage matched.
- ICs/connectors only substituted within the same part family, else flagged.
- Where the schematic Value and its stored MPN disagreed, the **Value and
  footprint** were treated as authoritative and the MPN as stale.
- Quantity is rounded up to each part's MOQ/multiple to give a real order cost.

## Lines by part

`P/N` is the supplier catalogue number: element14 order code, DigiKey part
number, or LCSC number. Prices are element14 NZ list unless the supplier
column says otherwise.

| refs | qty | value | brand | manufacturer P/N | supplier | P/N | stock | MOQ | order | unit | ext | asm | conf |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| C1,C5-C6,C9-C12 | 7 | 100n/50V | MULTICOMP PRO | `MC0603B104K500CT` | element14 | 175912201 | 1364666 | 10 | 10 | $0.023 | $0.23 | SMD | high |
| C2-C3 | 2 | 1u/50V | MULTICOMP PRO | `0603B105K500CT` | element14 | 3764121 | 47462 | 10 | 10 | $0.204 | $2.04 | SMD | high |
| C4 | 1 | 100u/35V | MULTICOMP PRO | `MCVVT035M101FB3L` | element14 | 2611382 | 4803 | 1 | 1 | $0.837 | $0.837 | SMD | high |
| C7 | 1 | 22u/16V | MULTICOMP PRO | `1206X226K160CT` | element14 | 249715401 | 10560 | 5 | 5 | $0.273 | $1.365 | SMD | high |
| C8 | 1 | 68u/35V | MULTICOMP PRO | `MCVVT035M680EA6L` | element14 | 2611393 | 4294 | 1 | 1 | $0.443 | $0.443 | SMD | high |
| C13-C14,C22-C23 | 4 | 22p | MULTICOMP PRO | `MC0402N220J500CT` | element14 | 1758951 | 53540 | 10 | 10 | $0.02 | $0.20 | SMD | high |
| C15 | 1 | 1u | MULTICOMP PRO | `0603B105K500CT` | element14 | 3764121 | 47462 | 10 | 10 | $0.204 | $2.04 | SMD | high |
| C16,C24-C26 | 4 | 100n | MULTICOMP PRO | `MC0603B104K500CT` | element14 | 175912201 | 1364666 | 10 | 10 | $0.023 | $0.23 | SMD | high |
| C17-C21 | 5 | 100n | MULTICOMP PRO | `0402B104K500CT` | element14 | 3764075 | 59400 | 10 | 10 | $0.038 | $0.38 | SMD | high |
| D1-D5 | 5 | SDM20U40-7 | ONSEMI | `NSR0340HT1G` | element14 | 2317404 | 32449 | 5 | 5 | $0.199 | $0.995 | SMD | high |
| D6 | 1 | SS24A+ | MULTICOMP PRO | `SS24A` | element14 | 2748189 | 12008 | 5 | 5 | $0.54 | $2.70 | SMD | high |
| D7-D8,D11 | 3 | BAT54JFILM | STMICROELECTRONICS | `BAT54KFILM` | element14 | 2341638 | 7745 | 5 | 5 | $0.82 | $4.10 | SMD | high |
| D9-D10 | 2 | YELLOW | WURTH ELEKTRONIK | `150040YS73240` | element14 | 2900756 | 3092 | 5 | 5 | $0.58 | $2.90 | SMD | high |
| J1-J2 | 2 | CONN_23W_SOCKET | Hong Cheng | `HC-PM254-8.5H-1x23PZ` | LCSC | C41376162 |  |  | 2 | $0.2297 | $0.4594 | THT | external |
| J3 | 1 | CONN_23W_PIN | Samtec | `TSW-123-17-T-S` | Samtec | TSW-123-17-T-S |  |  | 1 | $1.516 | $1.516 | THT | external |
| J4 | 1 | KYCON_KPJX-4S-S | KYCON | `KPJX-4S-S` | element14 | 283985101 | 2471 | 1 | 1 | $2.40 | $2.40 | THT | high |
| J5 | 1 | MicroFit_2x02 | MOLEX | `43045-0412` | element14 | 101224701 | 25592 | 10 | 10 | $0.913 | $9.13 | THT | high |
| J6 | 1 | 24V/5A OUT | PHOENIX CONTACT | `1715721` | element14 | 304152901 | 7399 | 1 | 1 | $1.40 | $1.40 | THT | high |
| J7 | 1 | DB25_PINS_MountingHoles | MULTICOMP PRO | `5504F1-25P-02A-03` | element14 | 1848370 | 3142 | 5 | 5 | $2.70 | $13.50 | THT | high |
| J8 | 1 | Phoenix MPT | PHOENIX CONTACT | `1725656` | element14 | 304135901 | 9270 | 1 | 1 | $1.45 | $1.45 | THT | high |
| J10 | 1 | Phoenix MPT | PHOENIX CONTACT | `1725698` | element14 | 304142601 | 232 | 1 | 1 | $4.29 | $4.29 | THT | high |
| J11,J13,J16,J20 | 4 | Phoenix MPT | PHOENIX CONTACT | `1725672` | element14 | 304141401 | 4223 | 1 | 4 | $2.85 | $11.40 | THT | high |
| J12,J14,J17 | 3 | MicroFit_2x04 | MOLEX | `43045-0812` | element14 | 101224901 | 16401 | 10 | 10 | $1.53 | $15.30 | THT | high |
| J15 | 1 | JST_B2B-XH | PHOENIX CONTACT | `1725672` | element14 | 304141401 | 4223 | 1 | 1 | $2.85 | $2.85 | THT | high |
| J18-J19 | 2 | MLX_1x03 | MOLEX | `22-23-2031` | element14 | 1462950 | 35731 | 10 | 10 | $0.333 | $3.33 | THT | high |
| J21 | 1 | USB_B_Mini | WURTH ELEKTRONIK | `65100516121` | element14 | 1642036 | 5091 | 1 | 1 | $2.59 | $2.59 | SMD | high |
| J22 | 1 | uISP | MULTICOMP PRO | `2213SM-06G-TB` | element14 | 2847230 | 3513 | 1 | 1 | $0.777 | $0.777 | SMD | high |
| J23 | 1 | ISP | MULTICOMP PRO | `2213SM-06G-TB` | element14 | 2847230 | 3513 | 1 | 1 | $0.777 | $0.777 | SMD | high |
| JP1 | 1 | Jumper_2_Bridged | MOLEX | `22-23-2021` | element14 | 146292601 | 34583 | 10 | 10 | $0.157 | $1.57 | THT | high |
| JP2 | 1 | GND_ISO | MOLEX | `22-23-2021` | element14 | 146292601 | 34583 | 10 | 10 | $0.157 | $1.57 | THT | high |
| K1 | 1 | OJS-SH-124HMF | TE CONNECTIVITY - OEG | `OJ-SS-124HM,000` | element14 | 1891694 | 1015 | 1 | 1 | $4.11 | $4.11 | THT | high |
| L1 | 1 | 100uH 1.5A+ | WURTH ELEKTRONIK | `74477120` | element14 | 163591201 | 2815 | 1 | 1 | $2.53 | $2.53 | SMD | high |
| L2 | 1 | CG0603MLC-05E | KYOCERA AVX | `VC080505A150DP` | element14 | 1189314 | 29439 | 1 | 1 | $0.569 | $0.569 | SMD | high |
| L3 | 1 | 10uH | TDK | `MLZ1608M100WT000` | element14 | 2215635 | 25540 | 10 | 10 | $0.153 | $1.53 | SMD | high |
| Q1,Q4 | 2 | BC847 | NEXPERIA | `BC847C,215` | element14 | 1081235 | 67502 | 5 | 5 | $0.51 | $2.55 | SMD | high |
| Q2 | 1 | FDD5614P | VISHAY | `SUD19P06-60-GE3` | element14 | 210146501 | 6360 | 1 | 1 | $1.98 | $1.98 | SMD | high |
| Q3 | 1 | BC857 | NEXPERIA | `BC857C,215` | element14 | 8734771 | 15271 | 5 | 5 | $0.51 | $2.55 | SMD | high |
| Q5 | 1 | BC857 | NEXPERIA | `BC857C,215` | element14 | 8734771 | 15271 | 5 | 5 | $0.51 | $2.55 | SMD | high |
| R2,R7,R11,R13 | 4 | 1M | MULTICOMP PRO | `MCMR06X1004FTL` | element14 | 2073351 | 30680 | 10 | 10 | $0.024 | $0.24 | SMD | high |
| R3 | 1 | 6K8 | MULTICOMP PRO | `MCSR06X6801FTL` | element14 | 2074296 | 341 | 10 | 10 | $0.018 | $0.18 | SMD | high |
| R4,R12 | 2 | 220K | MULTICOMP PRO | `MCSR06X2203FTL` | element14 | 2074218 | 14128 | 10 | 10 | $0.04 | $0.40 | SMD | high |
| R5 | 1 | 1K | MULTICOMP PRO | `MCSR06X1001FTL` | element14 | 2074166 | 4182 | 10 | 10 | $0.023 | $0.23 | SMD | high |
| R6,R10 | 2 | 130K | MULTICOMP PRO | `MCSR06X1303FTL` | element14 | 2074189 | 5010 | 10 | 10 | $0.04 | $0.40 | SMD | high |
| R8 | 1 | 680K | MULTICOMP PRO | `MCSR06X6803FTL` | element14 | 2074298 | 2147 | 10 | 10 | $0.04 | $0.40 | SMD | high |
| R9 | 1 | 330K | MULTICOMP PRO | `MCSR06X3303FTL` | element14 | 2074244 | 2473 | 10 | 10 | $0.04 | $0.40 | SMD | high |
| R14-R17 | 4 | 330 | MULTICOMP PRO | `MCSR06X3300FTL` | element14 | 2074240 | 1971 | 10 | 10 | $0.04 | $0.40 | SMD | high |
| R18-R19 | 2 | 5K6 | MULTICOMP PRO | `MCSR06X5601FTL` | element14 | 2074283 | 6578 | 10 | 10 | $0.04 | $0.40 | SMD | high |
| R20 | 1 | 10K | MULTICOMP PRO | `MCWR06X1002FTL` | element14 | 244723001 | 542228 | 10 | 10 | $0.006 | $0.06 | SMD | high |
| R21,R24 | 2 | 1M | MULTICOMP PRO | `MCSR04X1004FTL` | element14 | 2073963 | 12014 | 10 | 10 | $0.033 | $0.33 | SMD | high |
| R22 | 1 | 330 | MULTICOMP PRO | `MCSR04X3300FTL` | element14 | 2074057 | 7880 | 10 | 10 | $0.028 | $0.28 | SMD | high |
| R23,R30 | 2 | 10K | MULTICOMP PRO | `MCSR04X1002FTL` | element14 | 2073960 | 272331 | 10 | 10 | $0.033 | $0.33 | SMD | high |
| R25-R29,R31-R32 | 7 | 1K | MULTICOMP PRO | `MCSR04X1001FTL` | element14 | 2073959 | 49041 | 10 | 10 | $0.033 | $0.33 | SMD | high |
| RN1-RN2 | 2 | 1Kx4 | MULTICOMP PRO | `MP005637` | element14 | 3550064 | 920 | 10 | 10 | $0.083 | $0.83 | SMD | high |
| SW3 | 1 | RESET | XUNPU | `TS-1088-AR02016` | LCSC | C720477 |  |  |  |  |  | SMD | external |
| U1 | 1 | MAX5035BUSA | ANALOG DEVICES | `MAX5035BUSA+T` | element14 | 2799102 | 1569 | 1 | 1 | $12.80 | $12.80 | SMD | high |
| U2-U3 | 2 | 74HC245 | ONSEMI | `MM74HC245AWM` | element14 | 1013973 | 785 | 1 | 2 | $1.88 | $3.76 | SMD | high |
| U4-U5 | 2 | ACSL-6310 | BROADCOM | `ACSL-6310-00TE` | element14 | 1223820 | 1436 | 1 | 2 | $13.07 | $26.14 | SMD | high |
| U6 | 1 | USBLC6-2SC6 | STMICROELECTRONICS | `USBLC6-2SC6` | element14 | 1269406 | 13019 | 5 | 5 | $0.52 | $2.60 | SMD | high |
| U7 | 1 | ATmega16U2-A | MICROCHIP | `ATMEGA16U2-MU` | element14 | 2810000 | 428 | 1 | 1 | $5.73 | $5.73 | SMD | high |
| U8 | 1 | ADUM4160 | ANALOG DEVICES | `ADUM4160BRWZ` | element14 | 4032105 | 745 | 1 | 1 | $31.20 | $31.20 | SMD | high |
| U9 | 1 | ATmega328P-AU | MICROCHIP | `ATMEGA328P-AU` | element14 | 1715486 | 108096 | 1 | 1 | $4.81 | $4.81 | SMD | high |
| Y1 | 1 | Crystal_SMD_WE_CFPX-104-4Pin_5.0x3.2mm | ABRACON | `ABM3-16.000MHZ-D2Y-T` | element14 | 2467791 | 54565 | 1 | 1 | $1.03 | $1.03 | SMD | high |
| Y2 | 1 | CSTCE16M0V53-R0 16MHZ | ABRACON | `ABM3-16.000MHZ-D2Y-T` | element14 | 2467791 | 54565 | 1 | 1 | $1.03 | $1.03 | SMD | high |

## Alternate sources

| refs | used | alternate |
|---|---|---|
| K1 | element14 `1891694` | DigiKey OJS-SH-124HMF,00000 (sealed, 200mW, Class F, $4.14) / element14 3764773 = 2071556-2 (sealed 16A/450mW, $4.53, 0 stock, 24wk lead) / element14 OJ-SS-124LMHF,000 (vented, 200mW coil, Class F, but only 8A, $4.97) |

## Descriptions

| refs | description |
|---|---|
| C1,C5-C6,C9-C12 | SMD Multilayer Ceramic Capacitor, 0.1 µF, 50 V, 0603 [1608 Metric], ± 10%, X7R |
| C2-C3 | SMD Multilayer Ceramic Capacitor, 1 µF, 50 V, 0603 [1608 Metric], ± 10%, X7R |
| C4 | SMD Aluminium Electrolytic Capacitor, Radial Can - SMD, 100 µF, 35 V, 2000 hours @ 105°C, Polar |
| C7 | SMD Multilayer Ceramic Capacitor, 22 µF, 16 V, 1206 [3216 Metric], ± 10%, X5R |
| C8 | SMD Aluminium Electrolytic Capacitor, Radial Can - SMD, 68 µF, 35 V, 2000 hours @ 105°C, Polar |
| C13-C14,C22-C23 | SMD Multilayer Ceramic Capacitor, 22 pF, 50 V, 0402 [1005 Metric], ± 5%, C0G / NP0 |
| C15 | SMD Multilayer Ceramic Capacitor, 1 µF, 50 V, 0603 [1608 Metric], ± 10%, X7R |
| C16,C24-C26 | SMD Multilayer Ceramic Capacitor, 0.1 µF, 50 V, 0603 [1608 Metric], ± 10%, X7R |
| C17-C21 | SMD Multilayer Ceramic Capacitor, 0.1 µF, 50 V, 0402 [1005 Metric], ± 10%, X7R |
| D1-D5 | Small Signal Schottky Diode, Single, 40 V, 250 mA, 590 mV, 1 A, 150 °C |
| D6 | Schottky Rectifier, 40 V, 2 A, Single, DO-214AC (SMA), 2 Pins, 550 mV |
| D7-D8,D11 | Small Signal Schottky Diode, 40 V, 300 mA, 900 mV, 1 A, 150 °C |
| D9-D10 | LED, Yellow, SMD, 0402 [1005 Metric], 20 mA, 2 V, 590 nm |
| J1-J2 | 23-way 2.54mm single-row socket, 8.5mm insulation height, 3mm tails, gold-flash contacts. 260 in stock, MOQ 5 = $1.15. Socket hangs below the interface board and receives the 15.75mm posts of J3 across the fixed 20.00mm standoff gap (socket body bottom at 11.5mm, pin tip at 15.75mm). Backup: HC-PM254-8.5H-1x24PZ = C41376163 (15714 stock, cut one position). |
| J3 | 23-way single-row 2.54mm THT header, .025in square posts, tin, lead style 17 = .620in (15.75mm) post above a 2.54mm plastic body, .830in (21.08mm) overall. The long post is what reaches the interface-board sockets across the fixed 20.00mm stack: measured requirement is 16.0 +/-0.25mm above the controller PCB, geometry says 15.75-16.25mm, and 15.75mm is the only stocked lead style in that window (-15 is 13.21mm, -18 is 18.29mm and would bottom out). In stock at Samtec, $1.516 ea. Exact-height alternative if 15.75mm proves marginal: MTSW-123-10-T-S-630 (.630in = 16.00mm post), build-to-order, no stock. Tail is 2.79mm = 1.19mm proud of a 1.6mm board. |
| J4 | High Power Connector, Through Hole RA, KPJX Series, Receptacle, 48 VDC, 7.5 A, PCB Mount |
| J5 | Pin Header, With Polarizing Peg, Wire-to-Board, 3 mm, 2 Rows, 4 Contacts, Through Hole Straight |
| J6 | Wire-To-Board Terminal Block, 5.08 mm, 2 Ways, 26 AWG, 14 AWG, 2.5 mm², Screw |
| J7 | D Sub Connector, Right Angle, DB25, Standard, Plug, 5504, 25 Contacts, DB, Solder |
| J8 | Wire-To-Board Terminal Block, 2.54 mm, 2 Ways, 26 AWG, 20 AWG, 0.5 mm², Screw |
| J10 | Wire-To-Board Terminal Block, 2.54 mm, 6 Ways, 26 AWG, 20 AWG, 0.5 mm², Screw |
| J11,J13,J16,J20 | Wire-To-Board Terminal Block, 2.54 mm, 4 Ways, 26 AWG, 20 AWG, 0.5 mm², Screw |
| J12,J14,J17 | Pin Header, Wire-to-Board, 3 mm, 2 Rows, 8 Contacts, Through Hole Straight |
| J15 | Wire-To-Board Terminal Block, 2.54 mm, 4 Ways, 26 AWG, 20 AWG, 0.5 mm², Screw |
| J18-J19 | Pin Header, Wire-to-Board, 2.54 mm, 1 Rows, 3 Contacts, Through Hole Straight, KK 254 6373 Series |
| J21 | USB Connector, Mini USB Type B, USB 2.0, Receptacle, 5 Ways, Surface Mount, Right Angle |
| J22 | Pin Header, Board-to-Board, 2.54 mm, 2 Rows, 6 Contacts, Surface Mount |
| J23 | Pin Header, Board-to-Board, 2.54 mm, 2 Rows, 6 Contacts, Surface Mount |
| JP1 | Pin Header, Wire-to-Board, 2.54 mm, 1 Rows, 2 Contacts, Through Hole Straight, KK 254 6373 Series |
| JP2 | Pin Header, Wire-to-Board, 2.54 mm, 1 Rows, 2 Contacts, Through Hole Straight, KK 254 6373 Series |
| K1 | General Purpose Relay, OJ Series, Power, Non Latching, SPST-NO, 24 VDC, 10 A |
| L1 | Power Inductor (SMD), 100 µH, 1.53 A, Shielded, 1.7 A, WE-PD Series |
| L2 | TVS Varistor, 4 V, 5.6 V, TransGuard, 18 V, 0805 [2012 Metric], Multilayer Varistor (MLV) |
| L3 | Multilayer Inductor, 10 µH, 1.05 ohm, 17 MHz, 250 mA, 0603 [1608 Metric], MLZ Series |
| Q1,Q4 | Bipolar (BJT) Single Transistor, General Purpose, NPN, 45 V, 100 mA, 250 mW, SOT-23, Surface Mount |
| Q2 | Power MOSFET, P Channel, 60 V, 18.3 A, 0.06 ohm, TO-252 (DPAK), Surface Mount |
| Q3 | Bipolar (BJT) Single Transistor, General Purpose, PNP, 45 V, 100 mA, 250 mW, SOT-23, Surface Mount |
| Q5 | Bipolar (BJT) Single Transistor, General Purpose, PNP, 45 V, 100 mA, 250 mW, SOT-23, Surface Mount |
| R2,R7,R11,R13 | SMD Chip Resistor, Ceramic, 1 Mohm, ± 1%, 100 mW, 0603 [1608 Metric], Thick Film, Sulfur Resistant |
| R3 | SMD Chip Resistor, 6.8 kohm, ± 1%, 100 mW, 0603 [1608 Metric], Thick Film, Sulfur Resistant |
| R4,R12 | SMD Chip Resistor, 220 kohm, ± 1%, 100 mW, 0603 [1608 Metric], Thick Film, Sulfur Resistant |
| R5 | SMD Chip Resistor, 1 kohm, ± 1%, 100 mW, 0603 [1608 Metric], Thick Film, Sulfur Resistant |
| R6,R10 | SMD Chip Resistor, 130 kohm, ± 1%, 100 mW, 0603 [1608 Metric], Thick Film, Sulfur Resistant |
| R8 | SMD Chip Resistor, 680 kohm, ± 1%, 100 mW, 0603 [1608 Metric], Thick Film, Sulfur Resistant |
| R9 | SMD Chip Resistor, 330 kohm, ± 1%, 100 mW, 0603 [1608 Metric], Thick Film, Sulfur Resistant |
| R14-R17 | SMD Chip Resistor, 330 ohm, ± 1%, 100 mW, 0603 [1608 Metric], Thick Film, Sulfur Resistant |
| R18-R19 | SMD Chip Resistor, 5.6 kohm, ± 1%, 100 mW, 0603 [1608 Metric], Thick Film, Sulfur Resistant |
| R20 | SMD Chip Resistor, 10 kohm, ± 1%, 100 mW, 0603 [1608 Metric], Thick Film, General Purpose |
| R21,R24 | SMD Chip Resistor, 1 Mohm, ± 1%, 62.5 mW, 0402 [1005 Metric], Thick Film, Sulfur Resistant |
| R22 | SMD Chip Resistor, 330 ohm, ± 1%, 62.5 mW, 0402 [1005 Metric], Thick Film, Sulfur Resistant |
| R23,R30 | SMD Chip Resistor, 10 kohm, ± 1%, 62.5 mW, 0402 [1005 Metric], Thick Film, Sulfur Resistant |
| R25-R29,R31-R32 | SMD Chip Resistor, 1 kohm, ± 1%, 62.5 mW, 0402 [1005 Metric], Thick Film, Sulfur Resistant |
| RN1-RN2 | Fixed Network Resistor, 1 kohm, Isolated, 4 Resistors, 1206 [3216 Metric], Convex, ± 5% |
| SW3 | 3.9x3.0x2.0mm SMD vertical tactile, SPST-NO 12V/50mA. Footprint SW_Push_1P1T_NO_XUNPU_TS-1088-AR02016 (2 pads 1.05x2.00mm, 3.40mm gap, 4.45mm pitch). Local stock; also available to PCBWay from their catalogue. |
| U1 | Buck (Step Down), Switching Regulator, Fixed, 7.5V to 76V In, 5V/1A Out, 125kHz, NSOIC-8 |
| U2-U3 | Bus Transceiver, 74HC245, 2 V to 6 V, SOIC-20 |
| U4-U5 | Optocoupler, Digital Output, 3 Channel, 2.5 kV, 15 Mbaud, SOIC, 16 Pins |
| U6 | ESD Protection Device, 17 V, SOT-23, 6 Pins, 1.1 V |
| U7 | 8 Bit MCU, AVR ATmega Family ATmega16 Series Microcontrollers, AVR, 16 MHz, 16 KB, 32 Pins, VQFN |
| U8 | Digital Isolator, 2 Channels, 3.1 V, 5.5 V, WSOIC, 16 Pins, 12 Mbps |
| U9 | 8 Bit MCU, AVR ATmega Family ATmega328 Series Microcontrollers, AVR, 20 MHz, 32 KB, 32 Pins, TQFP |
| Y1 | Crystal, ABM3, 16 MHz, 20 ppm, 30 ppm, 18 pF |
| Y2 | Crystal, ABM3, 16 MHz, 20 ppm, 30 ppm, 18 pF |

## Not fitted (excluded from totals)

| ref | value | footprint | reason |
|---|---|---|---|
| C28 | ISOLATION approx. 1.5mm (DNI) | — | DNP flag set |
| H1 | MountingHole_Pad | MountingHole:MountingHole_3.2mm_M3_ISO14580_Pad | exclude_from_bom |
| H2 | MountingHole_Pad | MountingHole:MountingHole_3.2mm_M3_ISO14580_Pad | exclude_from_bom |
| H3 | MountingHole_Pad | MountingHole:MountingHole_3.2mm_M3_ISO14580_Pad | exclude_from_bom |
| H4 | MountingHole_Pad | MountingHole:MountingHole_3.2mm_M3_ISO14580_Pad | exclude_from_bom |
| H5 | MountingHole_Pad | MountingHole:MountingHole_3.2mm_M3_ISO14580_Pad | exclude_from_bom |
| H6 | MountingHole_Pad | MountingHole:MountingHole_3.2mm_M3_ISO14580_Pad | exclude_from_bom |
| H7 | MountingHole_Pad | MountingHole:MountingHole_3.2mm_M3_ISO14580_Pad | exclude_from_bom |
| H8 | MountingHole_Pad | MountingHole:MountingHole_3.2mm_M3_ISO14580_Pad | exclude_from_bom |
| J2B1 | DNI | — | DNP flag set |
| J9 | DNI | — | DNP flag set |
| JP3 | 1x03_2.54 | Connector_PinHeader_2.54mm:PinHeader_1x03_P2.54mm_Vertical | exclude_from_bom |
| JP4 | Jumper_3_Open | Connector_PinHeader_2.54mm:PinHeader_1x03_P2.54mm_Vertical | exclude_from_bom |
| JP5 | Jumper_3_Open | Connector_PinHeader_2.54mm:PinHeader_1x03_P2.54mm_Vertical | exclude_from_bom |
| JP6 | 1x03_2.54 | Connector_PinHeader_2.54mm:PinHeader_1x03_P2.54mm_Vertical | exclude_from_bom |
| JP7 | 1x03_2.54 | Connector_PinHeader_2.54mm:PinHeader_1x03_P2.54mm_Vertical | exclude_from_bom |
| JP8 | Jumper_3_Open | Connector_PinHeader_2.54mm:PinHeader_1x03_P2.54mm_Vertical | exclude_from_bom |
| JX1 | MicroFit_2x04 | Connector_Molex:Molex_Micro-Fit_3.0_43045-0812_2x04_P3.00mm_Vertical | DNP flag set |
| NT1 | NetTie_2 | -Project:NetTie-2_SMD_Pad0.3mm | net-tie (copper link, no part) |
| NT22 | DNI | -Project:NetTie-2_SMD_Pad0.3mm | net-tie (copper link, no part) |
| NT23 | DNI | -Project:NetTie-2_SMD_Pad1.0mm | net-tie (copper link, no part) |
| NT24 | DNI | -Project:NetTie-2_SMD_Pad1.0mm | net-tie (copper link, no part) |
| NT25 | DNI | -Project:NetTie-2_SMD_Pad0.3mm | net-tie (copper link, no part) |
| NT26 | DNI | -Project:NetTie-2_SMD_Pad0.3mm | net-tie (copper link, no part) |
| NT27 | DNI | -Project:NetTie-2_SMD_Pad0.3mm | net-tie (copper link, no part) |
| NT28 | DNI | -Project:NetTie-2_SMD_Pad1.0mm | net-tie (copper link, no part) |
| R1 | DNI | Resistor_SMD:R_0603_1608Metric | DNP flag set |
| SW1 | DNI | — | DNP flag set |
| SW2 | DNI | — | DNP flag set |
