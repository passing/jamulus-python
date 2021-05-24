#!/usr/bin/python3

import unittest

from jamulus import JamulusConnector


class Test_JamulusConnector(unittest.TestCase):
    def setUp(self):
        self.jc = JamulusConnector(port=None)

    def tearDown(self):
        self.jc.close()

    def test_calc_crc(self):
        crc = self.jc.calc_crc(bytearray.fromhex("0000ef03000000"))
        self.assertEqual(crc, 51992)

    def test_pack(self):
        data = self.jc.pack((("a", "L"), ("b", "H"), ("c", "B")), {"a": 1, "b": 2, "c": 3})
        self.assertEqual(data.hex(), "01000000020003")

        data = self.jc.pack((("text", "U"),), {"text": "xyz"})
        self.assertEqual(data.hex(), "0378797a")

        data = self.jc.pack((("text", "V"),), {"text": "xyz"})
        self.assertEqual(data.hex(), "030078797a")

        data = self.jc.pack((("data", "v"),), {"data": bytearray.fromhex("616263")})
        self.assertEqual(data.hex(), "0300616263")

        data = self.jc.pack((("ip", "A"),), {"ip": "127.0.0.1"})
        self.assertEqual(data.hex(), "0100007f")

    def test_pack_failing(self):
        with self.assertRaises(ValueError):
            # invalid format
            data = self.jc.pack((("a",),), {"a": 1})

        with self.assertRaises(ValueError):
            # value missing
            data = self.jc.pack((("a", "L"),), {})

        with self.assertRaises(ValueError):
            # value with wrong type
            data = self.jc.pack((("a", "L"),), {"a": "string"})

    def test_unpack(self):
        data = (
            bytearray.fromhex("01000000020003")  # {"a": 1, "b": 2, "c": 3}
            + bytearray.fromhex("0378797a")  # {"text": "xyz"}
            + bytearray.fromhex("030078797a")  # {"text": "xyz"})
            + bytearray.fromhex("0300616263")  # {"data": bytearray.fromhex("616263")}
            + bytearray.fromhex("0100007f")  # {"ip": "127.0.0.1"}
        )
        offset = 0

        values, offset = self.jc.unpack((("a", "L"), ("b", "H"), ("c", "B")), data, offset)
        self.assertEqual(values, {"a": 1, "b": 2, "c": 3})

        values, offset = self.jc.unpack((("text", "U"),), data, offset)
        self.assertEqual(values, {"text": "xyz"})

        values, offset = self.jc.unpack((("text", "V"),), data, offset)
        self.assertEqual(values, {"text": "xyz"})

        values, offset = self.jc.unpack((("data", "v"),), data, offset)
        self.assertEqual(values, {"data": bytearray.fromhex("616263")})

        values, offset = self.jc.unpack((("ip", "A"),), data, offset)
        self.assertEqual(values, {"ip": "127.0.0.1"})

        self.assertEqual(offset, len(data))

    def test_prot_pack(self):
        data = self.jc.prot_pack((("a", "B"), ("b", "B"), ("c", "B")), {"a": 1, "b": 2, "c": 3})
        self.assertEqual(data.hex(), "010203")

        data = self.jc.prot_pack((("a", "B"), ("b", "B"), ("c", "B")), [{"a": 1, "b": 2, "c": 3}, {"a": 4, "b": 5, "c": 6}], repeat=True)
        self.assertEqual(data.hex(), "010203040506")

    def test_prot_unpack(self):
        values = self.jc.prot_unpack((("a", "B"), ("b", "B"), ("c", "B")), bytearray.fromhex("010203"))
        self.assertEqual(values, {"a": 1, "b": 2, "c": 3})

        values = self.jc.prot_unpack((("a", "B"), ("b", "B"), ("c", "B")), bytearray.fromhex("010203040506"), repeat=True)
        self.assertEqual(values, [{"a": 1, "b": 2, "c": 3}, {"a": 4, "b": 5, "c": 6}])

    def test_main_pack(self):
        data = self.jc.main_pack("CLM_REQ_SERVER_LIST", values={}, count=0)
        self.assertEqual(data.hex(), "0000ef0300000018cb")

        data = self.jc.main_pack("CLM_PING_MS", values={"time": 0}, count=0)
        self.assertEqual(data.hex(), "0000e903000400000000006f60")

    def test_main_unpack(self):
        key, count, values = self.jc.main_unpack(bytearray.fromhex("0000ef0300000018cb"), ackn=False, addr=None)
        self.assertEqual(key, "CLM_REQ_SERVER_LIST")
        self.assertEqual(count, 0)
        self.assertEqual(values, {})

        key, count, values = self.jc.main_unpack(bytearray.fromhex("0000e903000400000000006f60"), ackn=False, addr=None)
        self.assertEqual(key, "CLM_PING_MS")
        self.assertEqual(count, 0)
        self.assertEqual(values, {"time": 0})


if __name__ == "__main__":
    unittest.main()
