# HID10301-BruteForce-WordListCreator

A command-line utility for generating HID H10301 26-bit Wiegand credential lists for use with the **Flipper Zero RFID fuzzer**. Useful for authorized penetration testing and physical security assessments of legacy proximity card access control systems.

> ⚠️ **Legal & Ethical Notice**
> This tool is intended for use **only on systems you own or have explicit written authorization to test**. Unauthorized use against access control systems may violate the Computer Fraud and Abuse Act (CFAA), state/local laws, and applicable regulations. The author assumes no liability for misuse. Always obtain written permission before conducting any physical security assessment.

---

## Background

The HID H10301 is one of the most widely deployed proximity card formats in the world. It uses the **26-bit Wiegand** protocol, a format designed in the 1980s with no encryption, no mutual authentication, and no rolling codes.

### 26-bit Wiegand Structure

```
Bit:  1        2–9           10–25         26
     [EP] [Facility Code] [Card ID] [OP]
```

| Field | Bits | Range | Notes |
|---|---|---|---|
| Even Parity (EP) | 1 | 0–1 | Covers bits 2–13 |
| Facility Code (FC) | 8 | 0–255 | Shared across all cards at a site |
| Card ID | 16 | 0–65535 | Unique per credential |
| Odd Parity (OP) | 1 | 0–1 | Covers bits 14–25 |

Because the **Facility Code is shared site-wide** and the **Card ID space is only 65,536 values**, a known FC reduces a brute-force attempt to a single, bounded iteration — a well-documented and widely published limitation of this legacy format.

---

## Features

- Accepts Facility Code in **decimal or hex** (`25` or `0x19`)
- Configurable **card ID range** with decimal or hex bounds
- Optional **output to file** or stdout
- Optional **full 26-bit Wiegand parity calculation** (even + odd) producing a ready-to-import 7-nibble hex payload
- Clean stderr status messages so stdout output stays pipe-friendly

---

## Requirements

- Python 3.9+
- No external dependencies — standard library only

---

## Installation

```bash
git clone https://github.com/DefensiveOrigins/HID10301-BruteForce-WordListCreator.git
cd HID10301-BruteForce-WordListCreator
chmod +x HID10301-WordList.py
```

---

## Usage

```
python HID10301-WordList.py --fc FACILITY_CODE --range START END [--output FILE] [--parity]
```

### Arguments

| Argument | Required | Description |
|---|---|---|
| `--fc` | ✅ | Facility code in decimal (`25`) or hex (`0x19`). Valid: 0–255. |
| `--range START END` | ✅ | Card ID range, inclusive. Decimal or hex. Valid: 0–65535. |
| `--output FILE` / `-o` | ❌ | Write output to a file instead of stdout. |
| `--parity` | ❌ | Compute full 26-bit Wiegand parity bits. Outputs 7-nibble hex per entry. |

---

## Examples

### Basic output to stdout (no parity)
```bash
python hid_fuzz_gen.py --fc 25 --range 1000 1999
```

### Facility code as hex
```bash
python hid_fuzz_gen.py --fc 0x19 --range 1000 1999
```

### Save to file
```bash
python hid_fuzz_gen.py --fc 25 --range 1000 1999 -o fuzz_list.txt
```

### Full 26-bit with parity bits, saved to file
```bash
python hid_fuzz_gen.py --fc 25 --range 1000 1999 --parity -o fuzz_parity.txt
```

### Use hex bounds for the card ID range
```bash
python hid_fuzz_gen.py --fc 0x19 --range 0x3E8 0x7CF --parity -o fuzz_parity.txt
```

---

## Output Format

### Without `--parity`
Each line is a 6-character hex string: `FC (2 nibbles)` + `Card ID (4 nibbles)`

```
191388   → FC=0x19 (25),  ID=0x1388 (5000)
191389   → FC=0x19 (25),  ID=0x1389 (5001)
```

### With `--parity`
Each line is a 7-character hex string representing the full **26-bit Wiegand value**:

```
[1-bit Even Parity][8-bit FC][16-bit Card ID][1-bit Odd Parity]
```

```
326270A  → EP=0, FC=25, ID=5000, OP=0  (binary: 00 11001 0001001110001000 0)
```

Parity rules:
- **Even parity**: set so the count of 1s across the top 12 data bits (FC + upper 4 of Card ID) is even
- **Odd parity**: set so the count of 1s across the bottom 12 data bits (lower 12 of Card ID) is odd

---

## Flipper Zero Import

1. Generate your list and save it to a file
2. Copy the file to your Flipper Zero via [qFlipper](https://flipperzero.one/update) or SD card
3. Open the **RFID** app → **Fuzz** → **HID H10301**
4. Select your imported list file and begin the fuzz sequence

> Refer to the [Flipper Zero documentation](https://docs.flipper.net) for the most current fuzzer import format, as firmware updates may affect expected file structure.

---

## Why 26-bit Wiegand Is a Known Risk

The limitations of this format are well-established in the physical security research community:

- No encryption or challenge-response — readers accept any signal with a valid parity
- Facility Code is a site-wide constant, not a per-card secret
- Card ID space (16 bits = 65,536 values) is trivially enumerable
- Standard Wiegand bus is unencrypted on the wire between reader and controller

Organizations relying solely on H10301 credentials should consider migrating to encrypted, mutually-authenticated formats such as **HID iCLASS SE**, **SEOS**, or **MIFARE DESFire** with appropriate reader/controller upgrades.

---

## Disclaimer

This project is provided for **educational purposes and authorized security testing only**. The author is not responsible for any unlawful or unauthorized use of this software. Use responsibly.
