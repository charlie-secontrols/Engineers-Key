### main.py
import utime
import time
from machine import mem32,Pin
from i2cSlave import i2c_slave
import bluetooth
from ble_simple_peripheral import BLESimplePeripheral

### --- pico connect i2c as slave --- ###
s_i2c = i2c_slave(0,sda=0,scl=1,slaveAddress=0x4f)

# Create a Bluetooth Low Energy (BLE) object
ble = bluetooth.BLE()
# Create an instance of the BLESimplePeripheral class with the BLE object
sp = BLESimplePeripheral(ble)

def on_rx(data):
    print("OSLink Command: ", data)  # Print the received data

try:
    while True:
        data = s_i2c.get()
        print(data)

        data_int = int(data)
        
        if sp.is_connected():
            # Create a message string
            sp.on_write(on_rx)
            msg = str(data_int) + "\n"
            sp.send(msg)

except KeyboardInterrupt:
    pass