from time import sleep
import pyvisa as visa
from pyvisa import VisaIOError

# Initialisierung


rm = visa.ResourceManager()

try:
    speki = rm.open_resource('GPIB1::20::INSTR')  # Verbindung zu Speki erstellen
    ip_dut = '192.168.1.100'  # ip-adresse vom DUT
    dut = rm.open_resource('TCPIP0::' + ip_dut + '::inst0::INSTR')  # Verbindung zu DUT erstellen
    ip_geni = '192.168.1.186'
    geni = rm.open_resource('TCPIP0::' + ip_geni + '::inst0::INSTR')
except VisaIOError:
    print('Gerät nicht verbunden oder falsche IP')

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

try:
    geni.read_termination = '\n'
    geni.write_termination = '\n'
    geni.write('*CLS')  # clear the error queue
    geni.write('syst:pres')  # set to the default settings
    geni.query('*OPC?')  # wait for commands to be completed
    geni.write('POW:MODE CW')  # select the power mode CW
    err_geni = dut.query('syst:err?')
    geni.query('*OPC?')
    print('Geni error: ' + err_geni)
except VisaIOError:
    print('Gerät nicht verbunden oder falsche IP')


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
        sleep(0.1)
        speki.write('calc:mark1 on')  # Marker einschalten
        speki.write('calc:mark1:max')  # Marker auf Peak setzen
        sleep(t)
        freq_rf = speki.query('calc:mark1:x?')  # Frequenz vom Marker abfragen
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
    # f_ref bestimmen
    f_ref_min = float(dut.query('rosc:outp:freq? min'))
    f_ref_max = float(dut.query('rosc:outp:freq? max'))
    if f_ref_min == f_ref_max:
        f_ref = [f_ref_min]
    else:
        if f_ref_max/f_ref_min == 10:
            f_ref = [f_ref_min, f_ref_max]
        else:
            f_ref = [f_ref_min, f_ref_min * 10, f_ref_max]
    for f in f_ref:
        speki.write('freq:cent ' + str(f))  # Center einstellen
        speki.write('freq:span ' + str(0.1 * f))  # Span einstellen
        speki.write('swe:time:auto on')
        speki.write('disp:trac1:y:rlev 10dBm')  # Powerlevel am Speki setzen
        dut.write('ROSC:OUTP ON')  # Referenzoutput vom DUT aktivieren
        speki.write('calc:mark1 on')  # Marker einschalten
        sleep(t)
        speki.write('calc:mark1:max')  # Marker auf Peak setzen
        sleep(t)
        freq_refout = speki.query('calc:mark1:x?')  # Frequenz vom Marker abfragen
        print(freq_refout + ' Hz')
        dev_refout = (float(freq_refout) - f) / f
        print('rel. Abweichung: ' + str("{:.3f}".format(dev_refout)))

        # prüfen, ob REF OUT-Frequenz näherungsweise 10 MHz beträgt
        if abs(dev_refout) < 0.005:
            print('REF OUT-Test erfolgreich')
        else:
            print('REF OUT-Test gescheitert')
    dut.write('ROSC:OUTP OFF')
    speki.write('calc:mark1 off')  # Marker ausschalten

# Test 3: REF IN
q = input('REF IN testen? (y/n)')
# if q == 'y':


# Test 4: FUNC OUT

# Test 5: TRIG IN

# Test 6: AM PULSE

# Test 7: PHI M


# close visa connections
speki.close()
dut.close()
