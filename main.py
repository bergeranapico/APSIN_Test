import pyvisa as visa

rm = visa.ResourceManager()


# Verbindung zu Speki und DUT erstellen
speki = rm.open_resource('GPIB1::20::INSTR')
ip = '192.168.1.100'
dut = rm.open_resource('TCPIP0::' + ip + '::inst0::INSTR')

# Geräte initialisieren
speki.read_termination = '\n'
speki.write_termination = '\n'
speki.write('*CLS') # clear error queue
err_speki = speki.query('syst:err?')
print('Speki error: ' + err_speki)
print('\n')


dut.read_termination = '\n'
dut.write_termination = '\n'
dut.write('*CLS')  # clear the error queue
dut.write('syst:pres')  # set to the default settings
dut.query('*OPC?')  # wait for commands before to be completed
dut.write('POW:MODE CW')  # select the power mode CW
err_dut = dut.query('syst:err?')
dut.query('*OPC?')
print('DUT error: ' + err_dut)
print('\n')

# Test 1: RF OUT
testf = 100e6  # Testfrequenz setzen
speki.write('disp:trac1:y:rlev 20dBm')  # Powerlevel am Speki einstellen
speki.write('freq:cent' + str(testf))
speki.write('freq:span' + str(2 * testf))


dut.write('POW 0')  # Poweroutput vom DUT einstellen
dut.write('freq' + str(testf))
dut.write('OUTP ON')  # Output am DUT aktivieren

speki.write('calc:delt1:max')  # Marker auf den peak setzen
value = speki.query('calc:delt1:x?')  # Frequenz vom Marker abfragen
print(value)

speki.write('calc:delt:a0ff')

# Test 2:

# Test xx: Frequenz sweep

# close visa connections
speki.close()
dut.close()
