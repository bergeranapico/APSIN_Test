from time import sleep
import pyvisa as visa

rm = visa.ResourceManager()


# Verbindung zu Speki und DUT erstellen
speki = rm.open_resource('GPIB1::20::INSTR')
ip = '192.168.1.100'  # ip-adresse vom DUT
dut = rm.open_resource('TCPIP0::' + ip + '::inst0::INSTR')

# Geräte initialisieren
speki.read_termination = '\n'
speki.write_termination = '\n'
speki.write('*CLS') # clear error queue
speki.write('calc:mark:aoff')  # alle Marker entfernen
err_speki = speki.query('syst:err?')
print('Speki error: ' + err_speki)
print('\n')


dut.read_termination = '\n'
dut.write_termination = '\n'
dut.write('*CLS')  # clear the error queue
dut.write('syst:pres')  # set to the default settings
dut.query('*OPC?')  # wait for commands to be completed
dut.write('POW:MODE CW')  # select the power mode CW
err_dut = dut.query('syst:err?')
dut.query('*OPC?')
print('DUT error: ' + err_dut)
print('\n')

# Test 1: RF OUT
testf = 250e6  # Testfrequenz definieren

speki.write('disp:trac1:y:rlev 20dBm')  # Powerlevel am Speki einstellen
speki.write('freq:cent ' + str(testf))
speki.write('freq:span ' + str(2 * testf))


dut.write('POW 0')  # Poweroutput vom DUT einstellen
dut.write('freq ' + str(testf))
dut.write('OUTP ON')  # Output am DUT aktivieren
sleep(0.1)

speki.write('calc:mark1:on')
speki.write('calc:mark1:max')  # Marker auf den peak setzen
value1 = speki.query('calc:mark1:x?')  # Frequenz vom Marker abfragen
sleep(0.1)
value2 = (float(value1)-testf)/testf
print(value1)
print(value2)


# Test 2:

# Test xx: Frequenz sweep

# close visa connections
speki.close()
dut.close()
