#!/usr/bin/env python
from typing import List

from exceptions import MalformedPdfException

# PDF supports multiple newline characters (0x0A, 0x0D, 0x0A0D)
NEWLINES = [b'\n', b'\r', b'\r\n']

def find_all(pdf_buffer: bytearray, pattern: bytes, shift: int = 0) -> List[int]:
    offset = pdf_buffer.find(pattern)
    result = []
    while offset != -1:
        result.append(offset+shift)
        offset = pdf_buffer.find(pattern, offset + 1)
    return result

def find_all_header_offsets(pdf_buffer: bytearray) -> List[int]:
    return find_all(pdf_buffer, b'%PDF-', 0)

def find_all_startxref(pdf_buffer: bytearray) -> List[int]:
    startxref_offsets = []
    for nl in NEWLINES:
        startxref_offsets = find_all(pdf_buffer, nl + b'startxref', len(nl))
        if len(startxref_offsets) > 0:
            break
    return startxref_offsets

def find_all_startxref_values(pdf_buffer: bytearray) -> List[int]:
    startxref_offsets = find_all_startxref(pdf_buffer)
    result = []
    for startxref_offset in startxref_offsets:
        startxref_value = startxref_offset + 10
        if pdf_buffer[startxref_value] == b'\n':
            # Case of CR+LF newline
            startxref_value += 1
        result.append(startxref_value)
    return result

def get_all_startxref_values(pdf_buffer: bytearray) -> List[int]:
    startxref_values = find_all_startxref_values(pdf_buffer)
    result = []
    for startxref_value in startxref_values:
        eol_offset_cr = pdf_buffer.find(b'\r', startxref_value)
        eol_offset_lf = pdf_buffer.find(b'\n', startxref_value)
        eol_offset = min(
            eol_offset_cr if eol_offset_cr > 0 else eol_offset_lf, eol_offset_lf if eol_offset_lf > 0 else eol_offset_cr
        )
        result.append(int(pdf_buffer[startxref_value:eol_offset].decode("ascii")))
    return result

def replace_last_startxref_value(pdf_buffer: bytearray, new_value: int):
    last_startxref_value = str(get_all_startxref_values(pdf_buffer)[-1]).encode("ascii")
    new_pdf_buffer = pdf_buffer.replace(last_startxref_value, str(new_value).encode("ascii"))
    return new_pdf_buffer

def find_all_xref(pdf_buffer: bytearray) -> List[int]:
    return find_all(pdf_buffer, b'\nxref', 1)

def find_all_trailer(pdf_buffer: bytearray) -> List[int]:
    return find_all(pdf_buffer, b'\ntrailer', 1)

def get_all_xref_tables(pdf_buffer: bytearray) -> List[str]:
    xref_offsets = find_all_xref(pdf_buffer)
    trailer_offsets = find_all_trailer(pdf_buffer)
    if len(xref_offsets) != len(trailer_offsets):
        raise MalformedPdfException(f"Mismatch between the amount of xref and trailer entries ({len(xref_offsets)} vs {len(trailer_offsets)})")
    result = []
    for i in range(len(xref_offsets)):
        xref_table = pdf_buffer[xref_offsets[i]:trailer_offsets[i]]
        result.append(xref_table.decode("ascii"))
    return result

def deserialize_xref_table(xref_table: str):
    table_list = xref_table.split("\n")
    if table_list[-1] == "":
        # Case of trailing newline
        table_list.pop()
    xref_table_dict = {
        "type": table_list[0],
        "start": int(table_list[1].split()[0]),
        "count": int(table_list[1].split()[1]),
        "objects": []
    }
    if xref_table_dict["type"] != "xref":
        raise MalformedPdfException(f"Expected xref table, got {xref_table_dict['type']}")
    if xref_table_dict["count"] != len(table_list) - 2:
        raise MalformedPdfException(f"Expected {xref_table_dict['count']} objects, got {len(table_list) - 2}")
    for i in range(2, len(table_list)):
        obj = table_list[i].split()
        xref_table_dict["objects"].append({
            "offset": int(obj[0]),
            "generation": int(obj[1]),
            "in_use": obj[2] == "n"
        })
    return xref_table_dict

def serialize_xref_object(xref_object: dict) -> str:
    result = f"{xref_object['type']}\n"
    result += f"{xref_object['start']} {xref_object['count']}\n"
    for obj in xref_object["objects"]:
        offset = str(obj['offset']).zfill(10)
        generation = str(obj['generation']).zfill(5)
        in_use = 'n' if obj['in_use'] else 'f'
        result += f"{offset} {generation} {in_use} \n"
    return result

def apply_offset_to_xref_object(xref_object: dict, offset: int):
    for obj in xref_object["objects"]:
        obj["offset"] += offset

def replace_last_xref_table(pdf_buffer: bytearray, new_xref_table: str):
    xref_tables = get_all_xref_tables(pdf_buffer)
    last_xref_table = xref_tables[-1]
    pdf_buffer = pdf_buffer.replace(last_xref_table.encode("ascii"), new_xref_table.encode("ascii"))
    return pdf_buffer

def fix(pdf_buffer: bytearray) -> bytearray:
    header_offset = find_all_header_offsets(pdf_buffer)[-1]
    last_xref_table = get_all_xref_tables(pdf_buffer)[-1]
    last_xref_object = deserialize_xref_table(last_xref_table)
    apply_offset_to_xref_object(last_xref_object, header_offset)
    new_xref_table = serialize_xref_object(last_xref_object)
    new_pdf_buffer = replace_last_xref_table(pdf_buffer, new_xref_table)
    last_xref_table_offset = find_all_xref(new_pdf_buffer)[-1]
    new_startxref_value = last_xref_table_offset
    new_pdf_buffer = replace_last_startxref_value(new_pdf_buffer, new_startxref_value)
    return new_pdf_buffer

def is_fixable(pdf_buffer: bytearray) -> bool:
    if len(find_all_header_offsets(pdf_buffer)) < 2:
        return False
    xref_count = len(find_all_xref(pdf_buffer))
    if xref_count < 2:
        return False
    if xref_count != len(find_all_trailer(pdf_buffer)):
        return False
    return True
