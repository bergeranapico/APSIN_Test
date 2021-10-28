from time import sleep
import pyvisa as visa


# Initialisierung
rm = visa.ResourceManager()

speki = rm.open_resource('GPIB1::20::INSTR')  # Verbindung zu Speki erstellen
ip = '192.168.1.100'  # ip-adresse vom DUT
dut = rm.open_resource('TCPIP0::' + ip + '::inst0::INSTR') # Verbindung zu DUT erstellen

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

t = 0.5  # Wartezeit zwischen Befehlen [s]

# --------------------------------------------------------------------------------------------------------------------
q = input('RF OUT testen? (y/n)')
if q == 'y':
    # Test 1: RF OUT
    print('RF OUT mit Speki verbinden und Enter drücken')
    input()
    power = 0  # Leistungsoutput DUT in dBm
    speki.write('disp:trac1:y:rlev ' + str(power + 5) + 'dBm')  # Powerlevel am Speki setzen
    dut.write('POW ' + str(power))  # Poweroutput vom DUT setzen
    dut.write('OUTP ON')  # Output am DUT aktivieren
    testf = [5e4, 5e5, 5e6, 5e7, 5e8, 5e9]  # Testpunkte definieren
    for f in testf:
        speki.write('freq:cent ' + str(f))  # Center einstellen
        speki.write('freq:span ' + str(0.1 * f))  # Span einstellen
        speki.write('swe:time 0.25s')
        dut.write('freq ' + str(f))  # Frequenz DUT einstellen
        sleep(t)
        speki.write('calc:mark1 on')  # Marker einschalten
        speki.write('calc:mark1:max')  # Marker auf Peak setzen
        sleep(t)
        freq_rf = speki.query('calc:mark1:x?')  # Frequenz vom Marker abfragen
        sleep(t)
        dev_rf = (float(freq_rf) - f) / f  # Abweichung von der gemessenen zur eingestellten Frequenz berechnen
        print(freq_rf + ' Hz')
        print('rel. Abweichung: ' + str("{:.3f}".format(dev_rf)))  # relative Abweichung ausgeben mit 3 Dezimalstellen
        if abs(dev_rf) < 0.01:
            print('Frequenzabweichung < 1% bei ' + str(f) + ' Hz')
        else:
            print('Achtung: Frequenzabweichung > 1% bei ' + str(f))
    dut.write('OUTP OFF')  # Output am DUT deaktivieren
    speki.write('calc:mark1 off')  # Marker ausschalten

q = input('REF OUT testen? (y/n)')
if q == 'y':
    # Test 2: REF OUT
    print('REF OUT mit Speki verbinden und Enter drücken')
    input()
    f_ref = 10e6
    speki.write('freq:cent ' + str(f_ref))  # Center einstellen
    speki.write('freq:span ' + str(0.1 * f_ref))  # Span einstellen
    speki.write('disp:trac1:y:rlev 10dBm')  # Powerlevel am Speki setzen
    dut.write('ROSC:OUTP ON')  # Referenzoutput vom DUT aktivieren
    speki.write('calc:mark1 on')  # Marker einschalten
    speki.write('calc:mark1:max')  # Marker auf Peak setzen
    sleep(t)
    freq_refout = speki.query('calc:mark1:x?')  # Frequenz vom Marker abfragen
    print(freq_refout + ' Hz')
    dev_refout = (float(freq_refout) - f_ref) / f_ref
    print('rel. Abweichung: ' + str("{:.3f}".format(dev_refout)))

    # prüfen, ob REF OUT-Frequenz näherungsweise 10 MHz beträgt
    if abs(dev_refout) < 0.005:
        print('REF OUT-Test erfolgreich')
    else:
        print('REF OUT-Test gescheitert')
    dut.write('ROSC:OUTP OFF')
    speki.write('calc:mark1 off')  # Marker ausschalten

# Test 3:

# Test x: frequency sweep

# close visa connections
speki.close()
dut.close()
