#!/usr/bin/env python3
"""
HID H10301 26-bit Wiegand Fuzzer List Generator
Generates card ID payloads for use with Flipper Zero RFID fuzzer.

26-bit Wiegand format:
  [1 even parity][8-bit FC][16-bit Card ID][1 odd parity]
"""

import argparse
import sys


def parse_int_or_hex(value: str) -> int:
    """Accept decimal or 0x-prefixed hex strings."""
    try:
        return int(value, 0)  # base 0 auto-detects 0x prefix
    except ValueError:
        raise argparse.ArgumentTypeError(
            f"Invalid integer or hex value: '{value}'. "
            "Use decimal (e.g. 25) or hex with 0x prefix (e.g. 0x19)."
        )


def calc_wiegand_parity(fc: int, card_id: int) -> tuple[int, int]:
    """
    Calculate even and odd parity bits for 26-bit Wiegand.

    Even parity: covers bits 2-13 (the 8 FC bits + top 4 card ID bits)
                 bit 1 (MSB) is set so total 1s in that group is even.
    Odd parity:  covers bits 14-25 (the lower 12 card ID bits)
                 bit 26 (LSB) is set so total 1s in that group is odd.

    Bit layout (1-indexed, MSB first):
      [EP][FC7..FC0][ID15..ID0][OP]
    """
    # Build the 24 data bits (no parity yet): FC (8) + Card ID (16)
    data = (fc << 16) | card_id

    # Even parity: top 12 data bits (bits 23-12 of data, i.e. FC + upper 4 of ID)
    top12 = (data >> 12) & 0xFFF
    even_parity = bin(top12).count('1') % 2  # 0 if already even, 1 to make even

    # Odd parity: bottom 12 data bits (bits 11-0 of data, i.e. lower 12 of ID)
    bot12 = data & 0xFFF
    odd_parity = 1 - (bin(bot12).count('1') % 2)  # 1 if already even (force odd)

    return even_parity, odd_parity


def format_entry(fc: int, card_id: int, with_parity: bool) -> str:
    """Format a single entry as a hex string."""
    if with_parity:
        even_p, odd_p = calc_wiegand_parity(fc, card_id)
        # Full 26-bit value: [EP(1)][FC(8)][ID(16)][OP(1)]
        bits_26 = (even_p << 25) | (fc << 17) | (card_id << 1) | odd_p
        # 26 bits = 7 hex chars (pad to 7 nibbles)
        return format(bits_26, '07X')
    else:
        fc_hex = format(fc, '02X')
        id_hex = format(card_id, '04X')
        return f"{fc_hex}{id_hex}"


def main():
    parser = argparse.ArgumentParser(
        description="Generate HID H10301 26-bit Wiegand fuzzer lists for Flipper Zero.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # FC=25 decimal, card IDs 5000-5999, output to stdout
  python hid_fuzz_gen.py --fc 25 --range 5000 5999

  # FC as hex, save to file
  python hid_fuzz_gen.py --fc 0x19 --range 5000 5999 --output fuzz_list.txt

  # Include full 26-bit Wiegand parity bits
  python hid_fuzz_gen.py --fc 25 --range 5000 5999 --parity --output fuzz_parity.txt
        """
    )

    parser.add_argument(
        "--fc",
        type=parse_int_or_hex,
        required=True,
        metavar="FACILITY_CODE",
        help="Facility code in decimal (e.g. 25) or hex with 0x prefix (e.g. 0x19). "
             "Valid range: 0-255."
    )

    parser.add_argument(
        "--range",
        type=parse_int_or_hex,
        nargs=2,
        required=True,
        metavar=("START", "END"),
        help="Card ID range, inclusive. Decimal or 0x hex. "
             "Valid range: 0-65535. Example: --range 5000 5999"
    )

    parser.add_argument(
        "--output", "-o",
        type=str,
        default=None,
        metavar="FILE",
        help="Optional output file path. If omitted, results are printed to stdout."
    )

    parser.add_argument(
        "--parity",
        action="store_true",
        default=False,
        help="Calculate and include 26-bit Wiegand even/odd parity bits. "
             "Output will be the full 26-bit value as a 7-nibble hex string "
             "instead of the default FC+ID format."
    )

    args = parser.parse_args()

    # --- Validate FC ---
    if not (0 <= args.fc <= 255):
        parser.error(f"Facility code must be 0-255. Got: {args.fc}")

    # --- Validate range ---
    start, end = args.range
    if not (0 <= start <= 65535) or not (0 <= end <= 65535):
        parser.error(f"Card ID range must be within 0-65535. Got: {start}-{end}")
    if start > end:
        parser.error(f"Range START ({start}) must be <= END ({end}).")

    # --- Generate entries ---
    entries = [
        format_entry(args.fc, card_id, args.parity)
        for card_id in range(start, end + 1)
    ]

    count = len(entries)
    output_text = "\n".join(entries)

    # --- Output ---
    if args.output:
        try:
            with open(args.output, "w") as f:
                f.write(output_text + "\n")
            print(
                f"[+] Generated {count} entries "
                f"(FC={args.fc} / 0x{args.fc:02X}, IDs {start}-{end}"
                f"{', with parity' if args.parity else ''}) "
                f"-> '{args.output}'",
                file=sys.stderr
            )
            # Show samples
            print(f"[+] First entry : {entries[0]}", file=sys.stderr)
            print(f"[+] Last entry  : {entries[-1]}", file=sys.stderr)
        except OSError as e:
            print(f"[!] Error writing to '{args.output}': {e}", file=sys.stderr)
            sys.exit(1)
    else:
        print(output_text)
        print(
            f"\n[+] {count} entries | FC={args.fc}/0x{args.fc:02X} | "
            f"IDs {start}-{end}{' | parity included' if args.parity else ''}",
            file=sys.stderr
        )


if __name__ == "__main__":
    main()
