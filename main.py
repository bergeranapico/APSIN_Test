from time import sleep
import pyvisa as visa
import numpy as np
import math

# Initialisierung (Funktion erstellen)
rm = visa.ResourceManager()
speki = rm.open_resource('GPIB1::20::INSTR')  # Verbindung zu Speki erstellen
ip_dut = '192.168.1.186'  # IP-Adresse DUT
dut = rm.open_resource('TCPIP0::' + ip_dut + '::inst0::INSTR')  # Verbindung zu DUT erstellen
ip_geni = '192.168.1.188'  # IP-Adresse Geni
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

t = 0.6  # Wartezeit zwischen Befehlen definieren [s]

# TODO: Abfragen, ob ein APSIN oder ein APULN getestet werden soll
# TODO: Errorhandling sauberer gestalten, falls ein Gerät einen Error aufweist, sollte Programm abgebrochen
#  und Gerät resettet werden


# Funktion, welche alle REF-OUT-Frequenzen eines APSIN/APULN durch automatische Abfrage bestimmt
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
        print('invalid device name')


# Frequenzgrenzen für RF OUT-Test bestimmen
fmin_dut = dut.query('freq? min')
fmax_dut = dut.query('freq? max')
# fmin_speki = speki.query('freq:start? min')
fmax_speki = speki.query('freq:stop? max')
fmin = float(fmin_dut)
if fmax_dut < fmax_speki:
    fmax = float(fmax_dut)
else:
    fmax = float(fmax_speki) - 0.5e9  # 0.5 GHz abziehen, damit noch mit vernünftigem Span gemessen werden kann

# --------------------------------------------------------------------------------------------------------------------
# Test 1: RF OUT
# benötigte Geräte: DUT und Speki
# prüft an verschiedenen Messpunkten, ob Frequenz und Powerlevel eingehalten werden
q = input('RF OUT testen? (y/n)')
if q == 'y':
    print('RF OUT vom DUT mit Speki verbinden und Enter drücken')
    input()
    power = 0  # Poweroutput DUT in dBm
    Messpunkte = 5
    speki.write('disp:trac1:y:rlev ' + str(power + 5) + 'dBm')  # Powerlevel am Speki (5 dB höher als DUT-Power)
    speki.write('swe:time:auto on')  # Sweep time auf automatisch
    dut.write('POW ' + str(power))  # Poweroutput vom DUT setzen
    dut.write('OUTP ON')  # Output am DUT aktivieren
    testf = np.linspace(fmin, fmax, num=Messpunkte)  # Testpunkte definieren

    for f in testf:
        speki.write('freq:cent ' + str(f))  # Center einstellen
        span = 1562.5 * math.pow(f, 0.301)
        speki.write('freq:span ' + str(span))  # Span einstellen
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
        print('rel. Abweichung f: ' + str("{:.4f}".format(dev_rf)) + ' bei ' + str(f) + ' Hz')
        print('Abweichung Power: ' + str("{:.2f}".format(dev_pow)) + ' dB')
        if abs(dev_rf) < 0.01:
            print('RF OUT Test erfolgreich bei ' + str(f) + ' Hz')
        else:
            print('RF OUT Test failed bei ' + str(f) + ' Hz')
    dut.write('OUTP OFF')  # Output am DUT deaktivieren
    speki.write('calc:mark1 off')  # Marker ausschalten
    speki.write('swe:time:auto on')  # Sweep-Modus wieder auf automatisch schalten


# Test 2: REF OUT
# benötigte Geräte: DUT und Speki
# prüft, ob der REFOUT port die Frequenzen korrekt ausgibt

q = input('REF OUT testen? (y/n)')
if q == 'y':
    print('REF OUT vom DUT mit Speki verbinden und Enter drücken')
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
# benötigte Geräte: DUT und zusätzlichen Geni
# prüft, ob Lock mit anderem Geni möglich ist
q = input('REF IN testen? (y/n)')
if q == 'y':
    print('REF IN vom DUT mit REF OUT Geni verbinden und Enter drücken')
    input()
    # f_ref = refout_freq('geni') (alter APSIN20G kennt scheinbar die Abfrage rosc:outp:freq? min/max nicht....)
    f_ref = [100e6]
    for f in f_ref:
        geni.write('rosc:outp on')  # REF OUT vom Geni einschalten
        sleep(t)
        geni.write('rosc:outp:freq ' + str(f) + 'Hz')  # REF OUT Frequenz vom Geni setzen
        dut.write('rosc:sour ext')  # REF IN Quelle vom DUT auf "EXT" setzen
        sleep(t)
        dut.write('rosc:ext:freq ' + str(f))  # REF IN Frequenz vom DUT setzen
        sleep(t)
        dut.write('rosc:lock:test')  # einfügen, um den Lockstatus zu aktualisieren
        sleep(3)  # gemäss Programming Manual muss nach "rosc:lock:test" 3s gewartet werden
        lock_status = dut.query('rosc:lock?')  # Lockstatus abfragen
        sleep(t)
        if lock_status == '0':
            print('REF IN test failed: Lock nicht möglich')
        elif lock_status == '1':
            print('REF IN test erfolgreich: Lock mit Geni ist erfolgt')
        geni.write('rosc:outp off')  # REF OUT vom Geni ausschalten
        dut.write('rosc:sour int')  # REF IN Quelle vom DUT auf INT setzen

# Test 4: FUNC OUT
# benötigte Geräte: DUT und Speki
# prüft bei verschiedenen Frequenzen, ob der FUNC OUT Sinus die korrekte Frequenz ausgibt
q = input('FUNC OUT testen? (y/n)')
if q == 'y':
    print('FUNC OUT vom DUT mit Speki verbinden und Enter drücken')
    input()
    f_lf = np.linspace(10e4, 3e6, num=5)  # Frequenzen, die getestet werden
    amp = 0.5  # Spannungsamplitude definieren [V]
    amp_dBm = math.ceil(10 * math.log10((amp**2/50)*1000))  # berechne theoretische, gerundete Leistung in dBm
    sleep(t)
    speki.write('disp:trac1:y:rlev ' + str(amp_dBm + 10))  # setze Powerlevel am Speki mit 10dB Sicherheitszuschlag
    dut.write('lfo:sour lfg')  # FUNC OUT auf Low Frequency Generator setzen
    dut.write('lfo:shap sine')  # Form des Outputs auf Sinus setzen
    dut.write('lfo:ampl ' + str(amp))  # Spannungsamplitude am DUT setzen
    dut.write('lfo:stat on')  # FUNC OUT port einschalten
    for f in f_lf:
        speki.write('freq:cent ' + str(f))
        speki.write('freq:span ' + str(0.1 * f))
        dut.write('lfo:freq ' + str(f))
        sleep(t)
        speki.write('calc:mark1 on')  # Marker einschalten
        sleep(t)
        speki.write('calc:mark1:max')  # Marker auf Peak setzen
        sleep(t)
        f_func = speki.query('calc:mark1:x?')  # Frequenz bei Marker abfragen
        sleep(t)
        p_func = speki.query('calc:mark1:y?')  # Power bei Marker abfragen
        dev_funcout_f = (float(f_func) - f) / f  # Frequenzabweichung berechnen
        print('rel. Abweichung f FUNC OUT: ' + str(dev_funcout_f))
        if dev_funcout_f <= 0.005:  # Test bestanden, wenn Frequenz-Abweichung kleiner als 0.5% ist
            print('FUNC OUT: Test erfolgreich bei ' + str("{:.3f}".format(f)) + 'Hz')
        else:
            print('FUNC OUT: Test failed bei ' + str("{:.3f}".format(f)) + 'Hz')
    dut.write('lfo:stat off')  # FUNC OUT port abschalten
    speki.write('calc:mark1:off')  # Marker abschalten

# TODO: Test 5: TRIG OUT
# benötigte Geräte: DUT und Speki
# prüft bei verschiedenen Frequenzen, ob der TRIG OUT Sinus die korrekte Frequenz ausgibt
q = input('TRIG OUT testen? (y/n)')
if q == 'y':
    print('TRIG OUT vom DUT mit Speki verbinden und Enter drücken')
    input()
    f_trig = np.linspace(10e4, 3e6, num=5)  # Frequenzen, die getestet werden
    amp = 0.5  # Spannungsamplitude definieren [V]
    amp_dBm = math.ceil(10 * math.log10((amp ** 2 / 50) * 1000))  # berechne theoretische, gerundete Leistung in dBm
    sleep(t)
    speki.write('disp:trac1:y:rlev ' + str(amp_dBm + 10))  # setze Powerlevel am Speki mit 10dB Sicherheitszuschlag
    dut.write('lfo:sour lfg')  # TRIG OUT auf Low Frequency Generator setzen
    dut.write('lfo:shap sine')  # Form des Outputs auf Sinus setzen
    dut.write('lfo:ampl ' + str(amp))  # Spannungsamplitude am DUT setzen
    dut.write('lfo:stat on')  # TRIG OUT port einschalten
    for f in f_trig:
        speki.write('freq:cent ' + str(f))
        speki.write('freq:span ' + str(0.1 * f))
        dut.write('lfo:freq ' + str(f))
        sleep(t)
        speki.write('calc:mark1 on')  # Marker einschalten
        sleep(t)
        speki.write('calc:mark1:max')  # Marker auf Peak setzen
        sleep(t)
        f_func = speki.query('calc:mark1:x?')  # Frequenz bei Marker abfragen
        sleep(t)
        p_func = speki.query('calc:mark1:y?')  # Power bei Marker abfragen
        dev_trigout_f = (float(f_func) - f) / f  # Frequenzabweichung berechnen
        print('rel. Abweichung f TRIG OUT: ' + str(dev_trigout_f))
        if dev_trigout_f <= 0.005:  # Test bestanden, wenn Frequenz-Abweichung kleiner als 0.5% ist
            print('TRIG OUT: Test erfolgreich bei ' + str("{:.3f}".format(f)) + 'Hz')
        else:
            print('TRIG OUT: Test failed bei ' + str("{:.3f}".format(f)) + 'Hz')
    dut.write('lfo:stat off')  # TRIG OUT port abschalten
    speki.write('calc:mark1:off')  # Marker abschalten

# TODO: Test 6: TRIG IN
# benötigte Geräte: Geni, DUT, Speki
# prüft, ob mit dem TRIG IN port vom DUT ein Frequenzsweep durchgeführt werden kann
# Geni settings setzen: 5000 Hz, Amplitude auf 0.5V, Square-Shape, LFGenerator mode (nicht Trig out!)
q = input('TRIG IN testen? (y/n)')
if q == 'y':
    print('TRIG/FUNC OUT vom Geni mit TRIG IN vom DUT verbinden, RF OUT DUT mit Speki verbinden und Enter drücken')
    input()
    amp = 0.5  # Spannungsamplitude definieren [V]
    amp_dBm = math.ceil(10 * math.log10((amp ** 2 / 50) * 1000))  # berechne theoretische, gerundete Leistung in dBm
    freq_trig = 20
    freq_start = 1e6
    freq_stop = 2e6
    pts = 100

    # settings speki setzen
    speki.write('disp:trac1:y:rlev ' + str(amp_dBm + 5))  # powerlevel speki einstellen
    speki.write('freq:start ' + str(freq_start))  # center frequenz speki einstellen
    speki.write('freq:stop ' + str(freq_stop))  # span frequenz speki einstellen

    # settings geni setzen
    geni.write('lfo:sour lfg')  # TRIG OUT Geni auf low frequency generator setzen
    geni.write('lfo:shap squ')  # TRIG OUT Form auf square setzen
    geni.write('lfo freq ' + str(freq_trig))  # TRIG OUT Frequenz setzen
    geni.write('lfo:ampl ' + str(amp))  # TRIG OUT Amplitude setzen

    # settings dut setzen
    dut.write('init:cont on')  # Trigger-Modus am DUT setzen
    dut.write('trig:sour ext')  # Trigger-Quelle am DUT auf "ext" setzen
    dut.write('trig:type point')  # Trigger-Typ am DUT auf "point" setzen

    # DUT freq sweep einstellen von 1 MHz bis 1 GHz, 100punkte, 50 ms dwell time, sweep und RF output einschalten
    # dut.write('swe:coun 1')
    dut.write('swe:poin ' + str(pts))
    dut.write('swe:dwel 0.2')
    dut.write('freq:star ' + str(freq_start))
    dut.write('freq:stop ' + str(freq_stop))
    dut.write('swe:blan on')
    dut.write('outp on')
    dut.write('freq:mode swe')

    # LF generator von Geni einschalten, um sweep zu starten
    geni.write('lfo:stat on')
    t = input('Ist der Sweep am Speki erkennbar? (y/n)')
    if t == 'y':
        print('TRIG IN erfolgreich getestet')
    else:
        print('TRIG IN Test failed')

    dut.write('outp off')
    dut.write('freq:mode cw')
    geni.write('lfo:stat off')

# TODO: Test 7: AM PULSE
# noch unklar wie testen, ist ein Input
# TODO: Test 8: PHI M
# noch unklar wie testen, ist ein Input

# schliesse die visa Verbindungen
speki.close()
dut.close()

# TODO: alle Tests als Funktionen definieren, danach die einzelnen Funktionen aufrufen um die Tests durchzuführen
