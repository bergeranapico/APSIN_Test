from time import sleep
import pyvisa as visa
import numpy as np
import math

# Initialisierung
rm = visa.ResourceManager()
speki = rm.open_resource('GPIB1::20::INSTR')  # Verbindung zu Speki erstellen
ip_dut = '192.168.1.100'  # ip-adresse vom DUT
dut = rm.open_resource('TCPIP0::' + ip_dut + '::inst0::INSTR')  # Verbindung zu DUT erstellen
ip_geni = '192.168.1.186'
geni = rm.open_resource('TCPIP0::' + ip_geni + '::inst0::INSTR')

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

geni.read_termination = '\n'
geni.write_termination = '\n'
geni.write('*CLS')  # clear the error queue
geni.write('syst:pres')  # set to the default settings
geni.query('*OPC?')  # wait for commands to be completed
geni.write('POW:MODE CW')  # select the power mode CW
err_geni = dut.query('syst:err?')
geni.query('*OPC?')
print('Geni error: ' + err_geni)

t = 0.5  # Wartezeit zwischen Befehlen definieren [s]


# Funktion, welche alle REF-OUT-Frequenzen eines APSIN/APULN bestimmt
def refout_freq(device):
    if device == 'dut':
        f_ref_min = float(dut.query('rosc:outp:freq? min'))
        f_ref_max = float(dut.query('rosc:outp:freq? max'))
        if f_ref_min == f_ref_max:
            return [f_ref_min]
        else:
            if f_ref_max / f_ref_min == 10:
                return [f_ref_min, f_ref_max]
            else:
                return [f_ref_min, f_ref_min * 10, f_ref_max]
    elif device == 'geni':
        f_ref_min = float(geni.query('rosc:outp:freq? min'))
        f_ref_max = float(geni.query('rosc:outp:freq? max'))
        if f_ref_min == f_ref_max:
            return [f_ref_min]
        else:
            if f_ref_max / f_ref_min == 10:
                return [f_ref_min, f_ref_max]
            else:
                return [f_ref_min, f_ref_min * 10, f_ref_max]
    else:
        print('invalid function input')


# Frequenzgrenzen für RF OUT-Test bestimmen
fmin_dut = dut.query('freq? min')
fmax_dut = dut.query('freq? max')
# fmin_speki = speki.query('freq:start? min')
fmax_speki = speki.query('freq:stop? max')
fmin = float(fmin_dut)
if fmax_dut < fmax_speki:
    fmax = float(fmax_dut)
else:
    fmax = float(fmax_speki)

# --------------------------------------------------------------------------------------------------------------------
# Test 1: RF OUT
# benötigte Geräte: DUT und Speki
# prüft an verschiedenen Messpunkten, ob Frequenz und Powerlevel eingehalten werden
q = input('RF OUT testen? (y/n)')
if q == 'y':
    print('RF OUT mit Speki verbinden und Enter drücken')
    input()
    power = 0  # Poweroutput DUT in dBm
    Messpunkte = 5
    speki.write('disp:trac1:y:rlev ' + str(power + 5) + 'dBm')  # Powerlevel am Speki (5 dB höher als DUT-Power)
    dut.write('POW ' + str(power))  # Poweroutput vom DUT setzen
    dut.write('OUTP ON')  # Output am DUT aktivieren
    testf = np.linspace(fmin, fmax, num=Messpunkte)  # Testpunkte definieren

    for f in testf:
        speki.write('freq:cent ' + str(f))  # Center einstellen
        speki.write('freq:span ' + str(0.1 * f))  # Span einstellen
        speki.write('swe:time 0.25s')  # Sweep time einstellen
        dut.write('freq ' + str(f))  # Frequenz DUT einstellen
        speki.write('calc:mark1 on')  # Marker einschalten
        sleep(t)
        speki.write('calc:mark1:max')  # Marker auf Peak setzen
        sleep(t)
        freq_rf = float(speki.query('calc:mark1:x?'))  # Frequenz vom Marker abfragen
        sleep(t)
        pow_rf = float(speki.query('calc:mark1:y?'))  # Powerlevel vom Marker abfragen
        dev_rf = (freq_rf - f) / f  # Abweichung von der gemessenen zur eingestellten Frequenz berechnen
        dev_pow = pow_rf - power
        print(str(freq_rf) + ' Hz')
        print(str(pow_rf) + 'dBm')
        print('rel. Abweichung f: ' + str("{:.3f}".format(dev_rf)))  # relative Abweichung ausgeben mit 3 Dezimalstellen
        print('Abweichung power: ' + str("{:.2f}".format(dev_pow)) + 'dBm')
        if abs(dev_rf) < 0.01:
            print('Frequenzabweichung < 1% bei ' + str(f) + ' Hz')
        else:
            print('Achtung: Frequenzabweichung > 1% bei ' + str(f))
    dut.write('OUTP OFF')  # Output am DUT deaktivieren
    speki.write('calc:mark1 off')  # Marker ausschalten


# Test 2: REF OUT
# benötigte Geräte: DUT und Speki
# prüft, ob der REFOUT die Frequenzen korrekt ausgibt

q = input('REF OUT testen? (y/n)')
if q == 'y':
    print('REF OUT mit Speki verbinden und Enter drücken')
    input()
    f_ref = refout_freq('dut')

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
        print('f: ' + freq_refout + ' Hz')
        dev_refout = (float(freq_refout) - f) / f
        print('rel. Abweichung: ' + str("{:.3f}".format(dev_refout)))

        # prüfen, ob REF OUT-Frequenz weniger als 0.5% vom Sollwert abweicht
        if abs(dev_refout) < 0.005:
            print('REF OUT-Test erfolgreich')
        else:
            print('REF OUT-Test gescheitert')
    dut.write('ROSC:OUTP OFF')
    speki.write('calc:mark1 off')  # Marker ausschalten

# Test 3: REF IN
q = input('REF IN testen? (y/n)')
if q == 'y':
    print('REF IN DUT mit REF OUT Geni verbinden')
    input()
    f_ref = refout_freq('geni')
    for f in f_ref:
        geni.write('rosc:outp on')  # REF OUT vom Geni einschalten
        sleep(t)
        geni.write('rosc:outp:freq ' + str(f) + 'Hz')  # REF OUT Frequenz vom Geni setzen
        dut.write('rosc:sour ext')  # REF IN Quelle vom DUT auf EXT setzen
        sleep(t)
        dut.write('rosc:ext:freq ' + str(f))  # REF IN Frequenz vom DUT setzen
        sleep(t)
        dut.write('rosc:lock:test')  # muss eingefügt werden, damit der aktuelle lockstatus aktualisiert wird
        sleep(3)  # gemäss Programming manual muss nach rosc:lock:test mind. 3s gewartet werden
        lock_status = dut.query('rosc:lock?')  # lock status abfragen
        if lock_status == '0':
            print('REF IN test failed: Lock war nicht möglich')
        elif lock_status == '1':
            print('REF IN test erfolgreich: Lock mit Geni ist erfolgt')
        geni.write('rosc:outp off')  # REF OUT vom Geni wieder ausschalten
        dut.write('rosc:sour int')  # REF IN Quelle vom DUT wieder auf INT setzen

# TODO: Test 4: FUNC OUT
# benötigte Geräte: DUT und Speki
# prüft bei verschiedenen Frequenzen, ob der FUNC OUT Sinus die korrekte Frequenz und Leistung ausgibt
q = input('FUNC OUT testen? (y/n)')
if q == 'y':
    f_lf = [2e5, 4e5, 6e5, 8e5, 1e6]  # Frequenzen, die getestet werden
    amp = 0.5  # Spannungsamplitude definieren [V]
    amp_dBm = math.ceil(10 * math.log10((amp**2/50)*1000))  # berechne theoretische, gerundete Leistung in dBm
    sleep(t)
    speki.write('disp:trac1:y:rlev ' + str(amp_dBm + 15))  # setze Powerlevel am Speki mit 5dB Marge
    dut.write('lfo:sour lfg')
    dut.write('lfo:shap sine')
    dut.write('lfo:ampl ' + str(amp))  # Spannungsamplitude am DUT setzen
    dut.write('lfo:stat on')
    for f in f_lf:
        speki.write('freq:cent ' + str(f))
        speki.write('freq:span ' + str(0.1 * f))
        dut.write('lfo:freq ' + str(f))
        sleep(t)
        speki.write('calc:mark1 on')  # Marker einschalten
        sleep(t)
        speki.write('calc:mark1:max')  # Marker auf Peak setzen
        sleep(t)
        f_func = speki.query('calc:mark1:x?')
        sleep(t)
        p_func = speki.query('calc:mark1:y?')
        dev_funcout_f = (float(f_func) - f) / f
        print('rel. Abweichung f FUNC OUT: ' + str(dev_funcout_f))
        if dev_funcout_f <= 0.005:
            print('FUNC OUT: Test erfolgreich bei ' + str("{:.3f}".format(f)) + 'Hz')
        else:
            print('FUNC OUT: Test failed bei ' + str("{:.3f}".format(f)) + 'Hz')
    dut.write('lfo:stat off')
    speki.write('calc:mark1:off')



# TODO: Test 5: TRIG IN
# so testen, wie Sony gezeigt hat
# TODO: Test 6: AM PULSE
# noch unklar wie testen
# TODO: Test 7: PHI M
# noch unklar wie testen

# close visa connections
speki.close()
dut.close()

# TODO: alle Tests als Funktionen definieren, und danach die einzelnen Funktionen aufrufen um den Tests durchzuführen
