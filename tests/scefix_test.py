import copy
import json
import unittest

from scefix.core import *

pdf_buffer: bytearray = bytearray()
xref_tables: list[str] = []
xref_object_1 = {}
fixed_pdf_buffer: bytearray = bytearray()

class TestSCEfix(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        global pdf_buffer
        with open('resources/original.pdf', 'rb') as f:
            pdf_buffer = bytearray(f.read())
        global xref_tables
        with open('resources/xref_table_1.txt', 'r') as f:
            xref_tables.append(f.read())
        with open('resources/xref_table_2.txt', 'r') as f:
            xref_tables.append(f.read())
        global xref_object_1
        with open('resources/xref_object_1.json') as f:
            xref_object_1 = json.load(f)
        global fixed_pdf_buffer
        with open('resources/fixed.pdf', 'rb') as f:
            fixed_pdf_buffer = bytearray(f.read())

    def test_find_all_header_offsets(self):
        expected_offsets = [0, 35425]
        actual_offsets = find_all_header_offsets(pdf_buffer)
        self.assertEqual(expected_offsets, actual_offsets)

    def test_find_all_startxref(self):
        expected_offsets = [35403, 80578]
        actual_offsets = find_all_startxref(pdf_buffer)
        self.assertEqual(expected_offsets, actual_offsets)

    def test_find_all_startxref_values(self):
        expected_offsets = [35413, 80588]
        actual_offsets = find_all_startxref_values(pdf_buffer)
        self.assertEqual(expected_offsets, actual_offsets)

    def test_get_all_startxref_values(self):
        expected_values = [34778, 44364]
        actual_values = get_all_startxref_values(pdf_buffer)
        self.assertEqual(expected_values, actual_values)

    def test_replace_last_startxref_value(self):
        old_value = 44364
        header_offset = find_all_header_offsets(pdf_buffer)[-1]
        new_value = old_value + header_offset
        actual_old_value = get_all_startxref_values(pdf_buffer)[-1]
        self.assertEqual(old_value, actual_old_value)
        new_pdf_buffer = replace_last_startxref_value(pdf_buffer, new_value)
        actual_new_value = get_all_startxref_values(new_pdf_buffer)[-1]
        self.assertEqual(new_value, actual_new_value)

    def test_find_all_xref(self):
        expected_offsets = [34778, 79789]
        actual_offsets = find_all_xref(pdf_buffer)
        self.assertEqual(expected_offsets, actual_offsets)

    def test_find_all_trailer(self):
        expected_offsets = [35268, 80459]
        actual_offsets = find_all_trailer(pdf_buffer)
        self.assertEqual(expected_offsets, actual_offsets)

    def test_find_all_xref_tables(self):
        actual_tables = get_all_xref_tables(pdf_buffer)
        self.assertEqual(xref_tables, actual_tables)

    def test_deserialize_xref_table(self):
        actual_object = deserialize_xref_table(xref_tables[0])
        self.assertEqual(xref_object_1, actual_object)

    def test_serialize_xref_object(self):
        actual_output = serialize_xref_object(xref_object_1)
        self.assertEqual(xref_tables[0], actual_output)

    def test_apply_offset_to_xref_object(self):
        offset = 1000
        xref_object_2 = copy.deepcopy(xref_object_1)
        apply_offset_to_xref_object(xref_object_2, offset)
        for i in range(len(xref_object_1["objects"])):
            self.assertEqual(xref_object_1["objects"][i]["offset"] + offset, xref_object_2["objects"][i]["offset"])

    def test_replace_last_xref_table(self):
        new_xref_object = deserialize_xref_table(xref_tables[1])
        header_offset = find_all_header_offsets(pdf_buffer)[-1]
        apply_offset_to_xref_object(new_xref_object, header_offset)
        new_xref_table = serialize_xref_object(new_xref_object)
        self.assertEqual(xref_tables[-1], get_all_xref_tables(pdf_buffer)[-1])
        new_pdf_buffer = replace_last_xref_table(pdf_buffer, new_xref_table)
        actual_xref_table = get_all_xref_tables(new_pdf_buffer)[-1]
        self.assertEqual(new_xref_table, actual_xref_table)

    def test_fix(self):
        fixed = fix(pdf_buffer)
        self.assertEqual(fixed_pdf_buffer, fixed)

if __name__ == '__main__':
    unittest.main()
