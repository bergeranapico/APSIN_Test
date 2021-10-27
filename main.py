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
speki.write('*CLS')  # clear error queue
speki.write('calc:mark:aoff')  # alle Marker entfernen
err_speki = speki.query('syst:err?')
print('Speki error: ' + err_speki)


dut.read_termination = '\n'
dut.write_termination = '\n'
dut.write('*CLS')  # clear the error queue
dut.write('syst:pres')  # set to the default settings
dut.query('*OPC?')  # wait for commands to be completed
dut.write('POW:MODE CW')  # select the power mode CW
err_dut = dut.query('syst:err?')
dut.query('*OPC?')
print('DUT error: ' + err_dut)


# Test 1: RF OUT
power = 0  # Leistungsoutput DUT in dBm
t = 0.5  # Wartezeit in Sekunden
testf = [5e4, 5e5, 5e6, 5e7, 5e8, 5e9]
for f in testf:
    speki.write('disp:trac1:y:rlev ' + str(power + 5) + 'dBm')  # Powerlevel am Speki einstellen
    speki.write('freq:cent ' + str(f))
    speki.write('freq:span ' + str(2 * f))
    dut.write('POW ' + str(power))  # Poweroutput vom DUT einstellen
    dut.write('freq ' + str(f))
    dut.write('OUTP ON')  # Output am DUT aktivieren
    sleep(t)
    speki.write('calc:mark1:on')
    sleep(t)
    speki.write('calc:mark1:max')  # Marker auf den peak setzen
    sleep(t)
    freq = speki.query('calc:mark1:x?')  # Frequenz vom Marker abfragen
    sleep(t)
    dut.write('OUTP OFF')  # Output am DUT deaktivieren
    dev = (float(freq) - f) / f  # Abweichung von der gemessenen zur eingestellten Frequenz berechnen
    print(freq + ' Hz')
    print('rel. Abweichung: ' + str(dev))
    if abs(dev) < 0.015:
        print('Frequenzabweichung < 1.5% bei ' + str(f) + ' Hz')
    else:
        print('Achtung: Frequenzabweichung > 1.5% bei ' + str(f))
        break

# Test 2:

# Test xx: Frequenz sweep

# close visa connections
speki.close()
dut.close()
