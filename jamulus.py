#!/usr/bin/python3

import socket
import struct


DEFAULT_PORT = 22124
MAX_SIZE_BYTES_NETW_BUF = 20000

FORMAT = {
    # format characters
    # (https://docs.python.org/3/library/struct.html#format-characters)
    # L = 4 bytes (unsigned long)
    # H = 2 bytes (unsigned short)
    # B = 1 byte (unsigned char)
    # custom format characters:
    # A = 4 bytes IPv4 address
    # U = 1 byte length n + n bytes UTF-8 string
    # V = 2 bytes length n + n bytes UTF-8 string
    # v = 2 bytes length n + n bytes data
    # z = all remaining data
    "MAIN_FRAME": (("tag", "H"), ("id", "H"), ("count", "B"), ("data", "v")),
    "AUDIO_FRAME": (("data", "z"),),
    "CRC": (("crc", "H"),),
    "ACKN": (("id", "H"),),
    "SERVER_IP": (("ip", "A"),),
    "JITT_BUF_SIZE": (("blocks", "H"),),
    "CLIENT_ID": (("id", "B"),),
    "CHANNEL_GAIN": (("id", "B"), ("gain", "H")),
    "CHANNEL_PAN": (("id", "B"), ("panning", "H")),
    "MUTE_STATE_CHANGED": (("id", "B"), ("muted", "B")),
    "CONN_CLIENTS_LIST": (
        ("id", "B"),
        ("country", "H"),
        ("instrument", "L"),
        ("skill", "B"),
        ("zero", "L"),
        ("name", "V"),
        ("city", "V"),
    ),
    "CHANNEL_INFOS": (
        ("country", "H"),
        ("instrument", "L"),
        ("skill", "B"),
        ("name", "V"),
        ("city", "V"),
    ),
    "CHAT_TEXT": (("string", "V"),),
    "NETW_TRANSPORT_PROPS": (
        ("base_netw_size", "L"),
        ("block_size_fact", "H"),
        ("num_chan", "B"),
        ("sam_rate", "L"),
        ("audiocod_type", "H"),
        ("flags", "H"),
        ("audiocod_arg", "L"),
    ),
    "LICENCE_REQUIRED": (("licence_type", "B"),),
    "REQ_CHANNEL_LEVEL_LIST": (("data", "B"),),
    "VERSION_AND_OS": (("os", "B"), ("version", "V")),
    "RECORDER_STATE": (("state", "B"),),
    "CLM_PING_MS": (("time", "L"),),
    "CLM_PING_MS_WITHNUMCLIENTS": (("time", "L"), ("clients", "B")),
    "CLM_REGISTER_SERVER": (
        ("port", "H"),
        ("country_id", "H"),
        ("max_clients", "B"),
        ("permanent", "B"),
        ("name", "V"),
        ("internal_address", "V"),
        ("city", "V"),
    ),
    "CLM_SEND_EMPTY_MESSAGE": (("ip", "A"), ("port", "H")),
    "CLM_CHANNEL_LEVEL_LIST": (("levels", "z"),),
    "CLM_REGISTER_SERVER_RESP": (("status", "B"),),
    "CLM_RED_SERVER_LIST": (("ip", "A"), ("port", "H"), ("name", "U")),
}

PROT = {
    # messages with connection
    "ACKN": {"format": FORMAT["ACKN"]},
    "JITT_BUF_SIZE": {"format": FORMAT["JITT_BUF_SIZE"]},
    "REQ_JITT_BUF_SIZE": {},
    "CLIENT_ID": {"format": FORMAT["CLIENT_ID"]},
    "CHANNEL_GAIN": {"format": FORMAT["CHANNEL_GAIN"]},
    "CHANNEL_PAN": {"format": FORMAT["CHANNEL_PAN"]},
    "MUTE_STATE_CHANGED": {"format": FORMAT["MUTE_STATE_CHANGED"]},
    "CONN_CLIENTS_LIST": {"format": FORMAT["CONN_CLIENTS_LIST"], "repeat": True},
    "REQ_CONN_CLIENTS_LIST": {},
    "CHANNEL_INFOS": {"format": FORMAT["CHANNEL_INFOS"]},
    "REQ_CHANNEL_INFOS": {},
    "CHAT_TEXT": {"format": FORMAT["CHAT_TEXT"]},
    "NETW_TRANSPORT_PROPS": {"format": FORMAT["NETW_TRANSPORT_PROPS"]},
    "REQ_NETW_TRANSPORT_PROPS": {},
    "REQ_SPLIT_MESS_SUPPORT": {},
    "SPLIT_MESS_SUPPORTED": {},
    "LICENCE_REQUIRED": {"format": FORMAT["LICENCE_REQUIRED"]},
    "REQ_CHANNEL_LEVEL_LIST": {"format": FORMAT["REQ_CHANNEL_LEVEL_LIST"]},
    "VERSION_AND_OS": {"format": FORMAT["VERSION_AND_OS"]},
    "OPUS_SUPPORTED": {},
    "RECORDER_STATE": {"format": FORMAT["RECORDER_STATE"]},
    # connection less messages
    "CLM_PING_MS": {"format": FORMAT["CLM_PING_MS"]},
    "CLM_PING_MS_WITHNUMCLIENTS": {"format": FORMAT["CLM_PING_MS_WITHNUMCLIENTS"]},
    "CLM_SERVER_FULL": {},
    "CLM_REGISTER_SERVER": {"format": FORMAT["CLM_REGISTER_SERVER"]},
    "CLM_REGISTER_SERVER_EX": {"format": FORMAT["CLM_REGISTER_SERVER"] + FORMAT["VERSION_AND_OS"]},
    "CLM_UNREGISTER_SERVER": {},
    "CLM_SERVER_LIST": {
        "format": FORMAT["SERVER_IP"] + FORMAT["CLM_REGISTER_SERVER"],
        "repeat": True,
    },
    "CLM_RED_SERVER_LIST": {
        "format": FORMAT["CLM_RED_SERVER_LIST"],
        "repeat": True,
    },
    "CLM_REQ_SERVER_LIST": {},
    "CLM_SEND_EMPTY_MESSAGE": {"format": FORMAT["CLM_SEND_EMPTY_MESSAGE"]},
    "CLM_EMPTY_MESSAGE": {},
    "CLM_DISCONNECTION": {},
    "CLM_VERSION_AND_OS": {"format": FORMAT["VERSION_AND_OS"]},
    "CLM_REQ_VERSION_AND_OS": {},
    "CLM_CONN_CLIENTS_LIST": {"format": FORMAT["CONN_CLIENTS_LIST"], "repeat": True},
    "CLM_REQ_CONN_CLIENTS_LIST": {},
    "CLM_CHANNEL_LEVEL_LIST": {"format": FORMAT["CLM_CHANNEL_LEVEL_LIST"]},
    "CLM_REGISTER_SERVER_RESP": {"format": FORMAT["CLM_REGISTER_SERVER_RESP"]},
}

MSG_IDS = {
    "ILLEGAL": 0,  # illegal ID
    "ACKN": 1,  # acknowledge
    "JITT_BUF_SIZE": 10,  # jitter buffer size
    "REQ_JITT_BUF_SIZE": 11,  # request jitter buffer size
    "NET_BLSI_FACTOR": 12,  # OLD (not used anymore)
    "CHANNEL_GAIN": 13,  # set channel gain for mix
    "CONN_CLIENTS_LIST_NAME": 14,  # OLD (not used anymore)
    "SERVER_FULL": 15,  # OLD (not used anymore)
    "REQ_CONN_CLIENTS_LIST": 16,  # request connected client list
    "CHANNEL_NAME": 17,  # OLD (not used anymore)
    "CHAT_TEXT": 18,  # contains a chat text
    "PING_MS": 19,  # OLD (not used anymore)
    "NETW_TRANSPORT_PROPS": 20,  # properties for network transport
    "REQ_NETW_TRANSPORT_PROPS": 21,  # request properties for network transport
    "DISCONNECTION": 22,  # OLD (not used anymore)
    "REQ_CHANNEL_INFOS": 23,  # request channel infos for fader tag
    "CONN_CLIENTS_LIST": 24,  # channel infos for connected clients
    "CHANNEL_INFOS": 25,  # set channel infos
    "OPUS_SUPPORTED": 26,  # tells that OPUS codec is supported
    "LICENCE_REQUIRED": 27,  # licence required
    "REQ_CHANNEL_LEVEL_LIST": 28,  # request the channel level list
    "VERSION_AND_OS": 29,  # version number and operating system
    "CHANNEL_PAN": 30,  # set channel pan for mix
    "MUTE_STATE_CHANGED": 31,  # mute state of your signal at another client has changed
    "CLIENT_ID": 32,  # current user ID and server status
    "RECORDER_STATE": 33,  # contains the state of the jam recorder (ERecorderState)
    "REQ_SPLIT_MESS_SUPPORT": 34,  # request support for split messages
    "SPLIT_MESS_SUPPORTED": 35,  # split messages are supported
    "CLM_START": 1000,  # start of connectionless messages
    "CLM_PING_MS": 1001,  # for measuring ping time
    "CLM_PING_MS_WITHNUMCLIENTS": 1002,  # for ping time and num. of clients info
    "CLM_SERVER_FULL": 1003,  # server full message
    "CLM_REGISTER_SERVER": 1004,  # register server
    "CLM_UNREGISTER_SERVER": 1005,  # unregister server
    "CLM_SERVER_LIST": 1006,  # server list
    "CLM_REQ_SERVER_LIST": 1007,  # request server list
    "CLM_SEND_EMPTY_MESSAGE": 1008,  # an empty message shall be send
    "CLM_EMPTY_MESSAGE": 1009,  # empty message
    "CLM_DISCONNECTION": 1010,  # disconnection
    "CLM_VERSION_AND_OS": 1011,  # version number and operating system
    "CLM_REQ_VERSION_AND_OS": 1012,  # request version number and operating system
    "CLM_CONN_CLIENTS_LIST": 1013,  # channel infos for connected clients
    "CLM_REQ_CONN_CLIENTS_LIST": 1014,  # request the connected clients list
    "CLM_CHANNEL_LEVEL_LIST": 1015,  # channel level list
    "CLM_REGISTER_SERVER_RESP": 1016,  # status of server registration request
    "CLM_REGISTER_SERVER_EX": 1017,  # register server with extended information
    "CLM_RED_SERVER_LIST": 1018,  # reduced server list
}
MSG_KEYS = dict(zip(MSG_IDS.values(), MSG_IDS.keys()))

COUNTRY_KEYS = {
    0: "-",
    1: "Afghanistan",
    2: "Albania",
    3: "Algeria",
    4: "American Samoa",
    5: "Andorra",
    6: "Angola",
    7: "Anguilla",
    8: "Antarctica",
    9: "Antigua And Barbuda",
    10: "Argentina",
    11: "Armenia",
    12: "Aruba",
    13: "Australia",
    14: "Austria",
    15: "Azerbaijan",
    16: "Bahamas",
    17: "Bahrain",
    18: "Bangladesh",
    19: "Barbados",
    20: "Belarus",
    21: "Belgium",
    22: "Belize",
    23: "Benin",
    24: "Bermuda",
    25: "Bhutan",
    26: "Bolivia",
    27: "Bosnia And Herzegowina",
    28: "Botswana",
    29: "Bouvet Island",
    30: "Brazil",
    31: "British Indian Ocean Territory",
    32: "Brunei",
    33: "Bulgaria",
    34: "Burkina Faso",
    35: "Burundi",
    36: "Cambodia",
    37: "Cameroon",
    38: "Canada",
    39: "Cape Verde",
    40: "Cayman Islands",
    41: "Central African Republic",
    42: "Chad",
    43: "Chile",
    44: "China",
    45: "Christmas Island",
    46: "Cocos Islands",
    47: "Colombia",
    48: "Comoros",
    49: "Congo Kinshasa",
    50: "Congo Brazzaville",
    51: "Cook Islands",
    52: "Costa Rica",
    53: "Ivory Coast",
    54: "Croatia",
    55: "Cuba",
    56: "Cyprus",
    57: "Czech Republic",
    58: "Denmark",
    59: "Djibouti",
    60: "Dominica",
    61: "Dominican Republic",
    62: "East Timor",
    63: "Ecuador",
    64: "Egypt",
    65: "El Salvador",
    66: "Equatorial Guinea",
    67: "Eritrea",
    68: "Estonia",
    69: "Ethiopia",
    70: "Falkland Islands",
    71: "Faroe Islands",
    72: "Fiji",
    73: "Finland",
    74: "France",
    75: "Guernsey",
    76: "French Guiana",
    77: "French Polynesia",
    78: "French Southern Territories",
    79: "Gabon",
    80: "Gambia",
    81: "Georgia",
    82: "Germany",
    83: "Ghana",
    84: "Gibraltar",
    85: "Greece",
    86: "Greenland",
    87: "Grenada",
    88: "Guadeloupe",
    89: "Guam",
    90: "Guatemala",
    91: "Guinea",
    92: "Guinea Bissau",
    93: "Guyana",
    94: "Haiti",
    95: "Heard And McDonald Islands",
    96: "Honduras",
    97: "Hong Kong",
    98: "Hungary",
    99: "Iceland",
    100: "India",
    101: "Indonesia",
    102: "Iran",
    103: "Iraq",
    104: "Ireland",
    105: "Israel",
    106: "Italy",
    107: "Jamaica",
    108: "Japan",
    109: "Jordan",
    110: "Kazakhstan",
    111: "Kenya",
    112: "Kiribati",
    113: "North Korea",
    114: "South Korea",
    115: "Kuwait",
    116: "Kyrgyzstan",
    117: "Laos",
    118: "Latvia",
    119: "Lebanon",
    120: "Lesotho",
    121: "Liberia",
    122: "Libya",
    123: "Liechtenstein",
    124: "Lithuania",
    125: "Luxembourg",
    126: "Macau",
    127: "Macedonia",
    128: "Madagascar",
    129: "Malawi",
    130: "Malaysia",
    131: "Maldives",
    132: "Mali",
    133: "Malta",
    134: "Marshall Islands",
    135: "Martinique",
    136: "Mauritania",
    137: "Mauritius",
    138: "Mayotte",
    139: "Mexico",
    140: "Micronesia",
    141: "Moldova",
    142: "Monaco",
    143: "Mongolia",
    144: "Montserrat",
    145: "Morocco",
    146: "Mozambique",
    147: "Myanmar",
    148: "Namibia",
    149: "Nauru Country",
    150: "Nepal",
    151: "Netherlands",
    152: "Cura Sao",
    153: "New Caledonia",
    154: "New Zealand",
    155: "Nicaragua",
    156: "Niger",
    157: "Nigeria",
    158: "Niue",
    159: "Norfolk Island",
    160: "Northern Mariana Islands",
    161: "Norway",
    162: "Oman",
    163: "Pakistan",
    164: "Palau",
    165: "Palestinian Territories",
    166: "Panama",
    167: "Papua New Guinea",
    168: "Paraguay",
    169: "Peru",
    170: "Philippines",
    171: "Pitcairn",
    172: "Poland",
    173: "Portugal",
    174: "Puerto Rico",
    175: "Qatar",
    176: "Reunion",
    177: "Romania",
    178: "Russia",
    179: "Rwanda",
    180: "Saint Kitts And Nevis",
    181: "Saint Lucia",
    182: "Saint Vincent And The Grenadines",
    183: "Samoa",
    184: "San Marino",
    185: "Sao Tome And Principe",
    186: "Saudi Arabia",
    187: "Senegal",
    188: "Seychelles",
    189: "Sierra Leone",
    190: "Singapore",
    191: "Slovakia",
    192: "Slovenia",
    193: "Solomon Islands",
    194: "Somalia",
    195: "South Africa",
    196: "South Georgia And The South Sandwich Islands",
    197: "Spain",
    198: "Sri Lanka",
    199: "Saint Helena",
    200: "Saint Pierre And Miquelon",
    201: "Sudan",
    202: "Suriname",
    203: "Svalbard And Jan Mayen Islands",
    204: "Swaziland",
    205: "Sweden",
    206: "Switzerland",
    207: "Syria",
    208: "Taiwan",
    209: "Tajikistan",
    210: "Tanzania",
    211: "Thailand",
    212: "Togo",
    213: "Tokelau Country",
    214: "Tonga",
    215: "Trinidad And Tobago",
    216: "Tunisia",
    217: "Turkey",
    218: "Turkmenistan",
    219: "Turks And Caicos Islands",
    220: "Tuvalu Country",
    221: "Uganda",
    222: "Ukraine",
    223: "United Arab Emirates",
    224: "United Kingdom",
    225: "United States",
    226: "United States Minor Outlying Islands",
    227: "Uruguay",
    228: "Uzbekistan",
    229: "Vanuatu",
    230: "Vatican City State",
    231: "Venezuela",
    232: "Vietnam",
    233: "British Virgin Islands",
    234: "United States Virgin Islands",
    235: "Wallis And Futuna Islands",
    236: "Western Sahara",
    237: "Yemen",
    238: "Canary Islands",
    239: "Zambia",
    240: "Zimbabwe",
    241: "Clipperton Island",
    242: "Montenegro",
    243: "Serbia",
    244: "Saint Barthelemy",
    245: "Saint Martin",
    246: "Latin America",
    247: "Ascension Island",
    248: "Aland Islands",
    249: "Diego Garcia",
    250: "Ceuta And Melilla",
    251: "Isle Of Man",
    252: "Jersey",
    253: "Tristan Da Cunha",
    254: "South Sudan",
    255: "Bonaire",
    256: "Sint Maarten",
    257: "Kosovo",
    258: "European Union",
    259: "Outlying Oceania",
    260: "World",
    261: "Europe",
}

INSTRUMENT_KEYS = {
    0: "-",
    1: "Drums",
    2: "Djembe",
    3: "Electric Guitar",
    4: "Acoustic Guitar",
    5: "Bass Guitar",
    6: "Keyboard",
    7: "Synthesizer",
    8: "Grand Piano",
    9: "Accordion",
    10: "Vocal",
    11: "Microphone",
    12: "Harmonica",
    13: "Trumpet",
    14: "Trombone",
    15: "French Horn",
    16: "Tuba",
    17: "Saxophone",
    18: "Clarinet",
    19: "Flute",
    20: "Violin",
    21: "Cello",
    22: "Double Bass",
    23: "Recorder",
    24: "Streamer",
    25: "Listener",
    26: "Guitar Vocal",
    27: "Keyboard Vocal",
    28: "Bodhran",
    29: "Bassoon",
    30: "Oboe",
    31: "Harp",
    32: "Viola",
    33: "Congas",
    34: "Bongo",
    35: "Vocal Bass",
    36: "Vocal Tenor",
    37: "Vocal Alto",
    38: "Vocal Soprano",
    39: "Banjo",
    40: "Mandolin",
    41: "Ukulele",
    42: "Bass Ukulele",
    43: "Vocal Baritone",
    44: "Vocal Lead",
    45: "Mountain Dulcimer",
    46: "Scratching",
    47: "Rapping",
}

SKILL_KEYS = {0: "-", 1: "Beginner", 2: "Intermediate", 3: "Expert"}

OS_KEYS = {0: "Windows", 1: "MacOS", 2: "Linux", 3: "Android", 4: "iOS", 5: "Unix"}


class JamulusConnector:
    def __init__(self, host="", port=DEFAULT_PORT, log=True, log_data=False, log_audio=True):
        self.log = log
        self.log_data = log_data
        self.log_audio = log_audio
        self.host = host
        self.port = port
        if self.port is not None:
            self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            print("listening to port {}".format(self.port))
            self.sock.bind((self.host, self.port))

    def close(self):
        if self.port is not None:
            print("closing socket")
            self.sock.close()

    def calc_crc(self, data):
        """
        CRC calculation as implemented in Jamulus

        Parameters
        ----------
        data : bytearray
            data to calculate CRC

        Returns
        -------
        int
            calculated CRC value
        """
        crc = 0xFFFF
        bmask = 0x10000
        poly = 0x1020

        for b in data:
            b = 0xFF & b
            for i in range(8):
                crc <<= 1
                if crc & bmask:
                    crc |= 1
                if b & (1 << (7 - i)):
                    crc ^= 1
                if crc & 1:
                    crc ^= poly
                crc &= 0xFFFF

        return ~crc & 0xFFFF

    def pack(self, format, values, mode="<"):
        """
        Encode data values according to the given protocol format

        Parameters
        ----------
        format : tuple
            sequence of multiple data keys and their value's format
        values : dict
            data keys and values
        mode : str
            byte order, size and alignment of the packed data
            https://docs.python.org/3/library/struct.html#byte-order-size-and-alignment

        Returns
        -------
        bytearray
            encoded data
        """
        data = b""
        for key, format_char in format:
            try:
                value = values[key]
            except KeyError as error:
                raise ValueError("error packing '{}': missing key in values".format(key))

            try:
                if format_char == "A":
                    # A = 4 bytes / IPv4 address
                    ip = socket.inet_aton(value)
                    data += struct.pack("{}{}".format(mode, "L"), struct.unpack("!L", ip)[0])
                elif format_char in ["U", "V", "v"]:
                    # U = 1 byte length n + n bytes UTF-8 string
                    # V = 2 bytes length n + n bytes UTF-8 string
                    # v = 2 bytes length n + n bytes data
                    if format_char in ["U", "V"]:
                        value = value.encode()

                    length_format = "B" if format_char == "U" else "H"
                    length = len(value)

                    data += struct.pack("{}{}{}{}".format(mode, length_format, length, "s"), length, value)
                elif format_char == "z":
                    # z = all remaining data
                    length = len(value)
                    data += struct.pack("{}{}".format(length, "s"), value)
                else:
                    # standard format characters
                    data += struct.pack("{}{}".format(mode, format_char), value)
            except struct.error as error:
                raise ValueError("error packing '{}': {}".format(key, error))

        return data

    def unpack(self, format, data, offset=0, mode="<"):
        """
        Decode data values according to the given protocol format

        Parameters
        ----------
        format : tuple
            sequence of multiple data keys and their value's format
        data : bytearray
            encoded data
        offset : int
            position in data bytearray where the decoding should start
        mode : str
            byte order, size and alignment of the packed data
            https://docs.python.org/3/library/struct.html#byte-order-size-and-alignment

        Returns
        -------
        dict
            decoded data keys and values
        """
        values = {}

        for key, format_char in format:
            try:
                if format_char == "A":
                    # A = 4 bytes / IPv4 address
                    ip = struct.pack("!L", *struct.unpack_from("{}{}".format(mode, "L"), data, offset))
                    values[key] = socket.inet_ntoa(ip)
                    offset += 4
                elif format_char in ["U", "V", "v"]:
                    # U = 1 byte length n + n bytes UTF-8 string
                    # V = 2 bytes length n + n bytes UTF-8 string
                    # v = 2 bytes length n + n bytes data
                    length_format = "B" if format_char == "U" else "H"
                    (length,) = struct.unpack_from("{}{}".format(mode, length_format), data, offset)
                    offset += struct.calcsize(length_format)

                    (value,) = struct.unpack_from("{}{}{}".format(mode, length, "s"), data, offset)
                    offset += length

                    utf8_enc = True if format_char in ["U", "V"] else False
                    values[key] = value.decode() if utf8_enc else value
                elif format_char == "z":
                    # z = all remaining data
                    length = len(data) - offset
                    (values[key],) = struct.unpack_from("{}{}{}".format(mode, length, "s"), data, offset)
                    offset += length
                else:
                    # standard format characters
                    (values[key],) = struct.unpack_from("{}{}".format(mode, format_char), data, offset)
                    offset += struct.calcsize("{}{}".format(mode, format_char))

            except struct.error as error:
                raise ValueError("error unpacking '{}': {}".format(key, error))

        return values, offset

    def prot_pack(self, format, values=None, repeat=False):
        """
        Encode single or multiple data sets according to the given protocol format

        Parameters
        ----------
        format : tuple
            sequence of multiple data keys and their value's format
        values : dict / list(dict)
            data keys and values (needs to be a list when repeat is true)
        repeat : bool
            if true, encode a list of data sets

        Returns
        -------
        bytearray
            encoded data
        """
        if repeat:
            data = b""
            for v in values:
                data += self.pack(format, v)
        else:
            data = self.pack(format, values)

        return data

    def prot_unpack(self, format, data, repeat=False):
        """
        Decode single or multiple data sets according to the given protocol format

        Parameters
        ----------
        format : tuple
            sequence of multiple data keys and their value's format
        data : bytearray
            encoded data
        repeat : bool
            if true, decode a list of data sets

        Returns
        -------
        dict / list(dict)
            decoded data keys and values (a list when repeat is true)
        """
        offset = 0

        if repeat:
            values = []
            while offset != len(data):
                v, offset = self.unpack(format, data, offset)
                values.append(v)
        else:
            values, offset = self.unpack(format, data, offset)

        if offset != len(data):
            raise ValueError("invalid message length ({}/{}) {}".format(offset, len(data), values))

        return values

    def main_pack(self, key, values, count):
        """
        Encode a Jamulus 'main frame'

        Parameters
        ----------
        key : str
            key of the protocol message ID
        values : dict / list(dict)
            data keys and values (needs to be a list when repeat is true)
        count : int
            message count

        Returns
        -------
        bytearray
            encoded data
        """
        prot = PROT[key]
        format = prot.get("format", ())
        repeat = prot.get("repeat", False)

        # pack main frame and data
        data = self.pack(
            FORMAT["MAIN_FRAME"],
            {
                "id": MSG_IDS[key],
                "tag": 0,
                "count": count,
                "data": self.prot_pack(format, values, repeat),
            },
        )

        # add crc checksum
        data += self.pack(FORMAT["CRC"], {"crc": self.calc_crc(data)})

        return data

    def main_unpack(self, data):
        """
        Decode a Jamulus 'main frame'

        Parameters
        ----------
        data : bytearray
            encoded data

        Returns
        -------
        str
            key of the protocol message ID
        int
            message count
        dict / list(dict)
            data keys and values (needs to be a list when repeat is true)
        """
        # get crc attached to data
        crc_values = self.unpack(FORMAT["CRC"], data, offset=len(data) - 2)[0]
        data = data[:-2]
        # calculate crc from data
        crc_check = self.calc_crc(data)
        if crc_values["crc"] != crc_check:
            raise ValueError("invalid message crc ({}/{})".format(crc_values["crc"], crc_check))

        # unpack main frame
        main_values, offset = self.unpack(FORMAT["MAIN_FRAME"], data)

        # verify there's no data left
        if offset != len(data):
            raise ValueError("invalid message length ({}/{}) {}".format(offset, len(data)))

        # verify ID is valid
        id = main_values["id"]
        if id not in MSG_KEYS.keys() or id == 0:
            raise ValueError("invalid message ID ({})".format(id))

        key = MSG_KEYS[id]
        prot = PROT[key]
        format = prot.get("format", ())
        repeat = prot.get("repeat", False)

        # unpack data
        values = self.prot_unpack(format, main_values["data"], repeat=repeat)

        return key, main_values["count"], values

    def send_ack(self, addr, key, count):
        """
        Send an acknowledgement message

        acknowledgement message is only sent if required for the given key

        Parameters
        ----------
        addr : tuple(str, int)
            host/port to send to
        key : str
            key of message that gets acknowledged
        count : int
            count of the message that gets acknowledged
        """
        id = MSG_IDS.get(key, 0)
        if id > MSG_IDS["ACKN"] and id < MSG_IDS["CLM_START"]:
            self.sendto(
                addr=addr,
                key="ACKN",
                values={"id": id},
                count=count,
            )

    def log_message(self, addr, key, count="-", length="", values=None, recv=True):
        """
        Write a formatted log line with message information

        Parameters
        ----------
        addr : tuple(str, int)
            host/port the message was sent to or received from
        key : str
            key of message ID
        count : int
            message count
        length : int
            message length
        values : dict / list(dict)
            data keys and values
        recv : bool
            True for received / False for sent
        """
        if self.log and (key != "AUDIO" or self.log_audio):
            output = "{} {} #{} {} ({})".format(
                addr,
                " >" if recv else "< ",
                count,
                key,
                length,
            )
            if self.log_data and key != "ACKN" and values is not None and len(values) > 0:
                output += " {}".format(values)
            print(output)

    def sendto(self, addr, key, values=None, count=0):
        """
        Encode a Jamulus message and send it to a host

        Parameters
        ----------
        addr : tuple(str, int)
            host/port to send to
        key : str
            key of the protocol message ID
        values : dict / list(dict)
            data keys and values
        count : int
            message count
        """
        if key == "AUDIO":
            # pack audio frame
            data = self.pack(FORMAT["AUDIO_FRAME"], values)
            self.log_message(addr, key, length=len(data), values=values, recv=False)

        else:
            # pack protocol frame
            data = self.main_pack(key, values, count)
            self.log_message(addr, key, count=count, length=len(data), values=values, recv=False)

        # send data
        if data is not None and len(data) <= MAX_SIZE_BYTES_NETW_BUF:
            self.sock.sendto(data, addr)
        else:
            print("error: no valid data to send")

    def recvfrom(self, timeout=None, ackn=True, bufsize=MAX_SIZE_BYTES_NETW_BUF):
        """
        Receive and decode a Jamulus message

        Parameters
        ----------
        timeout : int
            seconds to wait for message, None = no timeout
        ackn : bool
            send acknowledgement messages when needed
        bufsize : int
            receive buffer size

        Returns
        -------
        tuple(str, int)
            host/port the message was received from
        str
            key of the protocol message ID
        int
            message count
        dict / list(dict)
            data keys and values
        """
        # set timeout
        self.sock.settimeout(timeout)

        # receive data
        try:
            data, addr = self.sock.recvfrom(bufsize)
        except socket.timeout:
            raise TimeoutError

        key = "INVALID"
        count = None
        values = None

        try:
            # detect protocol messages
            if len(data) >= 9 and data[:2] == b"\x00\x00":
                key, count, values = self.main_unpack(data)
                self.log_message(addr, key, count=count, length=len(data), values=values, recv=True)
                if ackn:
                    self.send_ack(addr, key, count)

            # assume audio messages
            elif len(data) >= 1:
                key = "AUDIO"
                values = self.unpack(FORMAT["AUDIO_FRAME"], data)[0]
                self.log_message(addr, key, length=len(data), values=values, recv=True)

        except ValueError as error:
            print("error decoding message from {}: {} - {}".format(addr, error, data))

        return (addr, key, count, values)


def server_argument(string):
    server = string.split(":")
    if len(server) == 2:
        port = int(server[1])
    elif len(server) == 1:
        port = DEFAULT_PORT
    else:
        raise ValueError
    host = socket.gethostbyname(server[0])
    return host, port


def silent_audio(base_netw_size):
    return {"data": b"\x00\xff\xfe" + b"\x00" * (base_netw_size - 3)}
