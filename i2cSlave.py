from machine import mem32, Pin

led = Pin("LED", Pin.OUT)

machine.freq(240000000)



class i2c_slave:
    I2C0_BASE = 0x40044000
    I2C1_BASE = 0x40048000
    IO_BANK0_BASE = 0x40014000

    i = 0
    txc = 0
    readcount = 0
    addrNext = False
    addr = 0
    writecount = 0
    slot0 = bytearray(128)
    transfer_in_progress = 0

    mem_rw = const(0x0000)
    mem_xor = 0x1000
    mem_set = 0x2000
    mem_clr = 0x3000

    IC_CON = 0  # I2C Control Register
    IC_TAR = 4  # I2C Target Address Register
    IC_SAR = 8  # I2C Slave Address Register

    IC_DATA_CMD = 0x10  # I2C Rx/Tx Data Buffer and Command Register

    IC_RAW_INTR_STAT = 0x34  # I2C Raw Interrupt Status Register

    IC_RX_TL = 0x38  # I2C Receive FIFO Threshold Register
    IC_TX_TL = 0x3C  # I2C Transmit FIFO Threshold Register

    IC_CLR_INTR = 0x40  # Clear Combined and Individual Interrupt Register

    IC_CLR_RD_REQ = 0x50
    IC_CLR_TX_ABRT = 0x54

    IC_ENABLE = 0x6c  # I2C ENABLE Register
    IC_STATUS = 0x70  # I2C STATUS Register

    # New register definition for transmitting data
    IC_CLR_TX_DONE = 0x58
    IC_CLR_ACTIVITY = 0x5C

    def write_reg(self, reg, data, method=0):
        mem32[self.i2c_base | method | reg] = data

    def set_reg(self, reg, data):
        self.write_reg(reg, data, method=self.mem_set)

    def clr_reg(self, reg, data):
        self.write_reg(reg, data, method=self.mem_clr)

    def __init__(self, i2cID=0, sda=0, scl=1, slaveAddress=0x4F):
        self.scl = scl
        self.sda = sda
        self.slaveAddress = slaveAddress
        self.i2c_ID = i2cID
        if self.i2c_ID == 0:
            self.i2c_base = self.I2C0_BASE
        else:
            self.i2c_base = self.I2C1_BASE
            

        # set SDA PIN
        mem32[self.IO_BANK0_BASE | self.mem_clr | (4 + 8 * self.sda)] = 0x1f
        mem32[self.IO_BANK0_BASE | self.mem_set | (4 + 8 * self.sda)] = 3
        # set SLA PIN
        mem32[self.IO_BANK0_BASE | self.mem_clr | (4 + 8 * self.scl)] = 0x1f
        mem32[self.IO_BANK0_BASE | self.mem_set | (4 + 8 * self.scl)] = 3

        self.set_reg(self.IC_ENABLE, 1)
        # 1 Disable DW_apb_i2c
        self.clr_reg(self.IC_ENABLE, 1)

        self.write_reg(self.IC_TX_TL, 4);

        # set slave address
        self.clr_reg(self.IC_SAR, 0x1ff)
        self.set_reg(self.IC_SAR, self.slaveAddress & 0x1ff)

        # 3 write IC_CON 7 bit, enable in slave-only
        # bit 9 RX_FULL_HLD_BUS_EN = 1 will clock-stretch on RxFIFO full
        # bit 7 STOP_DET_IFADDRESSED  = stop int only if addressed
        # bit 6 SLAVE = 0
        # bit 3 7BIT ADDR = 0
        # bit 0 SLAVE = 0
        
        #self.set_reg(self.IC_CON, 0x280)
        self.set_reg(self.IC_CON, 0x080)
        self.clr_reg(self.IC_CON, 0x259)
        #self.set_reg(self.IC_CON, 0x04) # speed fast
        #self.set_reg(self.IC_CON, 0x02) # speed 100kHz
        
        #mask all interrupts
        mem32[self.i2c_base | 0x30 ] = 0

        # 4 enable i2c
        self.set_reg(self.IC_ENABLE, 1)

    def ABRT_SOURCE(self) :
        return mem32[self.i2c_base | 0x80]

    def RX_FULL(self):
        return bool(mem32[self.i2c_base | self.IC_RAW_INTR_STAT] & 0x4)

    def RD_REQ(self):
        return bool(mem32[self.i2c_base | self.IC_RAW_INTR_STAT] & 0x20)
    
    def CLR_RD_REQ(self) :
        clr = mem32[self.i2c_base | 0x50]	#clear RD_REQ

    def TX_ABRT(self):
        return bool(mem32[self.i2c_base | self.IC_RAW_INTR_STAT] & 0x40)

    def TFNF(self):
        return bool(mem32[self.i2c_base | self.IC_STATUS] & 2)
        # check RFNE receive FIFO not empty

    def TFE(self):
        return bool(mem32[self.i2c_base | self.IC_STATUS] & 4)

    def CLR_TX_ABRT(self) :
        clr = mem32[self.i2c_base | self.IC_CLR_TX_ABRT]
        
    def CLR_RX_OVER(self) :
        clr = mem32[self.i2c_base | 0x48]

    def CLR_RX_FULL(self) :
        clr = mem32[self.i2c_base | 0x48]
    
    def CLR_RX_DONE(self) :
        clr = mem32[self.i2c_base | 0x58]
    
    def CLR_STOP_DET(self) :
        clr = mem32[self.i2c_base | 0x60]

    def CLR_START_DET(self) :
        clr = mem32[self.i2c_base | 0x64]
        
    def CLR_RESTART_DET(self) :
        clr = mem32[self.i2c_base | 0xA8]
    
    def RFNE(self) :	#Recieve FIFO not empty        
        return bool(mem32[self.i2c_base | self.IC_STATUS] & 8)
    
    

    def getW(self):
        while not self.RFNE():
            pass
        rx  = mem32[self.i2c_base | self.IC_DATA_CMD] 
        return rx
    
    def get(self):
        return self.getW() & 0xFF


    def service(self) :
        done = False
        i = mem32[i2c.i2c_base | i2c.IC_RAW_INTR_STAT]

        if i & (1<<1) :		# RX_OVERRUN
            print("#OVR#", end='')
            self.CLR_RX_OVER()

        if i & (1<<6) : #ABORT LAST TRANSACTION
            #Abort code 0x2000 is expected if the Tx_fifo was pushed with more data than is read
            abrt = self.ABRT_SOURCE()
            self.CLR_TX_ABRT()
            if (abrt & 0xFFFF) != 0x2000 :
                print("ABRT = " + hex(self.ABRT_SOURCE()) + " i="+hex(i))
            done = True
#            else :
#                print("a="+hex(i)) #0x3d0
    
        if i & (1<<12) :  #RESTART, NEVER SEEN
#            print("R", end='')
            self.CLR_RESTART_DET()
            done = True
            
        if i & (1<<10) :	#START_DET
#                print("S", end='')
            self.CLR_START_DET()
#            done = True
            
        
        if(i & (1<<9)):
#           print("P", end='')
           self.CLR_STOP_DET()
           done = True

        if(i & (1<<7)):
            i2c.CLR_RX_DONE()
            done = True
        
        if done and (self.transfer_in_progress != 0):
            self.transfer_in_progress = 0;
            print("Addr="+hex(self.addr)+" WR:"+hex(self.writecount)+" RD:"+hex(self.readcount)+" : "+str(self.txc))
            return True
        
            
        if (i & 0x04) : #i2c.RX_FULL():
            rx = mem32[self.i2c_base | self.IC_DATA_CMD]
            firstByte = (rx & 2048) != 0
            rx = rx & 0xFF
            if firstByte :
#                    print("F", end='')
                self.txc = 0
                self.addr= rx & 0xFF
                self.addrNext = True
                self.readcount = 0
                self.writecount = 0;
            elif self.addrNext :
                self.addr = (self.addr << 8) | rx
                self.addrNext = False
            elif self.writecount < 128 :
                self.slot0[self.writecount] = rx 
                self.transfer_in_progress = 1
                writecount += 1
            else :
                print("overflow")
                
            #print("<",end='')
            #print("<"+hex(rx & 0xFF),end='')
            i2c.CLR_RX_FULL()

        elif (i & 0x20) : #i2c.RD_REQ():
       
            self.transfer_in_progress = 2
            self.CLR_RD_REQ()
            self.readcount += 1
            while self.TFNF() and not self.TX_ABRT() :
                mem32[self.i2c_base | self.IC_DATA_CMD] = self.txc & 0xFF
                self.txc += 1
                
        return False
                
                

    
   
i2c = i2c_slave(0, sda = 0, scl = 1, slaveAddress = 0x52)

def reg():
    print("     CON = " + hex(mem32[i2c.i2c_base | i2c.IC_CON] ))
    print(" RAW INT = " + hex(mem32[i2c.i2c_base | i2c.IC_RAW_INTR_STAT] ))
#    print("     INT = "+hex(mem32[i2c.i2c_base | 0x2C ] ))
#    print("INT MASK = "+hex(mem32[i2c.i2c_base | 0x30 ] ))
    print("  STATUS = " + hex(mem32[i2c.i2c_base | i2c.IC_STATUS] ))
    print("     SAR = " + hex(mem32[i2c.i2c_base | i2c.IC_SAR] ))
    print("  ENABLE = " + hex(mem32[i2c.i2c_base | i2c.IC_ENABLE] ))
    
    if i2c.TX_ABRT() :
        print("ABRT = " + hex(i2c.ABRT_SOURCE()))
#    print("GPIO_SDA = "+hex(mem32[i2c.IO_BANK0_BASE | (4 + 8 * i2c.sda)] ))
#    print("GPIO_SCL = "+hex(mem32[i2c.IO_BANK0_BASE | (4 + 8 * i2c.scl)] ))

def en():
    i2c.set_reg(i2c.IC_ENABLE, 1)

def dis():
    i2c.clr_reg(i2c.IC_ENABLE, 1)

def master() :
    dis()
    i2c.set_reg(i2c.IC_CON, 0x41)
    en()
    reg()
    print("Master Mode")
    return 0

def slave() :
    dis()
    i2c.clr_reg(i2c.IC_CON, 0x41)
    en()
    reg()
    return 0
        


def go():
    slave()
    print("Start I2C")
    counter = 1

    try:
        while True :
            #if i != mem32[i2c.i2c_base | i2c.IC_RAW_INTR_STAT]:
            if i2c.service() :
                print(counter)
                counter += 1
            
    except KeyboardInterrupt:
        pass
    
    if i2c.TX_ABRT() :
        print("ABRT = " + hex(i2c.ABRT_SOURCE()))
   
 
master()
 