import serial
import serial.tools.list_ports
import logging
import re
import sys

logger = logging.getLogger(__name__)

def getallports():
    allports = serial.tools.list_ports.comports()
    nanoports = []
    for port in allports:
        if port.manufacturer == "FTDI" or re.search("^/dev/ttyUSB.*", port.device):
            nanoports.append(port)
    return nanoports

def getallportssn():
    allports = getallports()
    portssn = []
    for port in allports:
        portssn.append(port.serial_number)
    return portssn

def getallportsastext():
    allports = getallports()
    portsastext = []
    for port in allports:
        portsastext.append([port.serial_number, port.device])
    return portsastext

def getportbyserialnumber(sn):
    allports = getallports()
    for port in allports:
        if port.serial_number == sn:
            return port
    return None

def getdevicebyserialnumber(sn):
    port = getportbyserialnumber(sn)
    if port is None:
        return None
    else:
        return getportbyserialnumber(sn).device

def connectdevice(sn=None):
    if sn is None and len(getallports()) > 0:
        nanoport = getallports()[0].device
    else:
        nanoport = getdevicebyserialnumber(sn)
    if nanoport is None:
        logger.info('No serial port device found.\n')
        sys.exit(0)
    tty = serial.Serial(nanoport, baudrate=600000, bytesize=8, parity='N', stopbits=1, timeout=0.01)
    return tty

def send_command(command):
    shproto.dispatcher.process_03(command)
    logger.info(f'Send command {command}\n')
    return