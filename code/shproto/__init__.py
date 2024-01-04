from struct import unpack  # Importing the 'unpack' function from the 'struct' module
import shproto.port  # Importing a module named 'port' from a package named 'shproto'

# Define constant values for protocol bytes and buffer size
SHPROTO_START = 0xFE  # Start of packet
SHPROTO_ESC = 0xFD    # Escape character
SHPROTO_FINISH = 0xA5  # End of packet
BUFFER_SIZE = 4096    # Maximum buffer size

# Define constant values for different modes
MODE_HISTOGRAM = 0x01
MODE_PULSE = 0x02
MODE_TEXT = 0x03
MODE_STAT = 0x04
MODE_BOOTLOADER = 0xF3  # Bootloader mode

# Function to calculate CRC16 checksum
def crc16(crc, data):
    crc ^= data
    for _ in range(8):
        if (crc & 0x0001) != 0:
            crc = ((crc >> 1) ^ 0xA001)
        else:
            crc = (crc >> 1)
    return crc

# Define a class named 'packet' to handle communication packets
class packet:
    # Initialize class attributes
    payload = []
    raw_data = []
    crc = 0xFFFF
    cmd = 0x00
    ready = 0
    len = 0
    esc = 0
    dropped = 0

    # Method to clear/reset packet attributes
    def clear(self):
        self.payload = []
        self.crc = 0xFFFF
        self.ready = 0
        self.len = 0
        self.esc = 0
        self.dropped = 0

    # Method to add a byte to the packet payload with CRC calculation
    def add(self, tx_byte):
        if self.len >= BUFFER_SIZE:
            return
        self.crc = crc16(self.crc, tx_byte)
        if tx_byte == SHPROTO_START or tx_byte == SHPROTO_FINISH or tx_byte == SHPROTO_ESC:
            self.payload.append(SHPROTO_ESC)
            self.payload.append((~tx_byte) & 0xFF)
            self.len = len(self.payload)
        else:
            self.payload.append(tx_byte)
            self.len += 1

    # Method to initialize the start of a packet
    def start(self):
        self.len = 0
        self.crc = 0xFFFF
        self.payload = [0xFF, SHPROTO_START]
        self.len = len(self.payload)
        self.add(self.cmd)

    # Method to finalize the packet and return its length
    def stop(self):
        _crc = self.crc
        self.add(_crc & 0xFF)
        self.add(_crc >> 8)
        if self.len >= BUFFER_SIZE:
            return 0
        self.payload.append(SHPROTO_FINISH)
        self.len = len(self.payload)
        return self.len

    # Method to read a byte from the received data and process it
    def read(self, rx_byte):
        self.raw_data.append(rx_byte)
        if rx_byte == SHPROTO_START:
            self.clear()
            return
        if rx_byte == SHPROTO_ESC:
            self.esc = 1
            return
        if rx_byte == SHPROTO_FINISH:
            self.len -= 3  # Subtract command (1 byte) and CRC16 (2 bytes)
            if not self.crc:
                self.ready = 1
            else:
                self.dropped = 1

            self.raw_data = []
            return
        if self.esc:
            self.esc = 0
            rx_byte = (~rx_byte) & 0xFF
        if self.len:
            self.payload.append(rx_byte)
        else:
            self.cmd = rx_byte
        if self.len < BUFFER_SIZE:
            self.len += 1
            self.crc = crc16(self.crc, rx_byte)
