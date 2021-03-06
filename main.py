from time import sleep
import pyvisa as visa
import numpy as np
import math

# IP-Adressen vom User holen
dutip = input('letzte Ziffern der IP vom DUT eingeben:')
geniip = input('letzte Ziffern der IP vom Geni eingeben:')

# Initialisierung (noch eine Funktion daraus machen)
rm = visa.ResourceManager()
res = rm.list_resources()

speki = rm.open_resource('GPIB1::20::INSTR')  # Verbindung zu Speki erstellen
ip_dut = '192.168.1.186'  # IP-Adresse DUT
dut = rm.open_resource('TCPIP0::192.168.1.' + dutip + '::inst0::INSTR')  # Verbindung zu DUT erstellen
ip_geni = '192.168.1.154'  # IP-Adresse Geni
geni = rm.open_resource('TCPIP0::192.168.1.' + geniip + '::inst0::INSTR')

# Speki initialisieren
speki.read_termination = '\n'
speki.write_termination = '\n'
speki.write('*RST')
speki.write('disp:trac1:y:rlev 20')  # Sweep Time auf auto stellen
speki.write('*CLS')  # clear error queue
err_speki = speki.query('syst:err?')
speki.query('*OPC?')
if "No error" in err_speki:
    print('Speki error: ' + err_speki)
else:
    print('Fehler wird gecleart...')
    speki.write('*CLS')
    err_speki = speki.query('syst:err?')
    print(('Speki error: ' + err_speki))

# DUT initialisieren
dut.read_termination = '\n'
dut.write_termination = '\n'
dut.write('*CLS')  # clear the error queue
dut.write('*RST')  # set to the default settings
dut.query('*OPC?')  # wait for commands to be completed
dut.write('POW:MODE CW')  # select the power mode CW
err_dut = dut.query('syst:err?')
dut.query('*OPC?')
if "No error" in err_dut:
    print('DUT error: ' + err_dut)
else:
    print('DUT error wird versucht zu clearen...')
    dut.write('*CLS')
    err_speki = dut.query('syst:err?')
    print(('DUT error: ' + err_dut))

# Geni initialisieren
geni.read_termination = '\n'
geni.write_termination = '\n'
geni.write('*CLS')  # clear the error queue
geni.write('*RST')  # set to the default settings
geni.query('*OPC?')  # wait for commands to be completed
geni.write('POW:MODE CW')  # select the power mode CW
err_geni = geni.query('syst:err?')
geni.query('*OPC?')
if "No error" in err_geni:
    print('Geni error: ' + err_geni)
else:
    print('DUT error wird versucht zu clearen...')
    geni.write('*CLS')
    err_geni = geni.query('syst:err?')
    print(('DUT error: ' + err_geni))


t = 0.6  # Wartezeit zwischen Befehlen definieren [s]

# TODO: Abfragen, ob ein APSIN oder ein APULN getestet werden soll
# TODO: Errorhandling sauberer gestalten, falls ein Ger??t einen Error aufweist, sollte Programm abgebrochen
#  und Ger??t resettet werden


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


# Frequenzgrenzen f??r RF OUT-Test bestimmen
fmin_dut = dut.query('freq? min')
fmax_dut = dut.query('freq? max')
# fmin_speki = speki.query('freq:start? min')
fmax_speki = speki.query('freq:stop? max')
fmin = float(fmin_dut)
if fmax_dut < fmax_speki:
    fmax = float(fmax_dut)
else:
    fmax = float(fmax_speki) - 0.5e9  # 0.5 GHz abziehen, damit noch mit vern??nftigem Span gemessen werden kann

# --------------------------------------------------------------------------------------------------------------------
# Test 1: RF OUT
# ben??tigte Ger??te: DUT und Speki
# pr??ft an verschiedenen Messpunkten, ob Frequenz und Powerlevel eingehalten werden
q = input('RF OUT testen? (y/n)')
if q == 'y':
    print('RF OUT vom DUT mit Speki verbinden und Enter dr??cken')
    input()
    power = 0  # Poweroutput DUT in dBm
    Messpunkte = 5
    speki.write('disp:trac1:y:rlev ' + str(power + 5) + 'dBm')  # Powerlevel am Speki (5 dB h??her als DUT-Power)
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
        if abs(dev_rf) < 0.01 and abs(dev_pow) < 5:
            print('RF OUT Test erfolgreich bei ' + str(f) + ' Hz')
        else:
            print('RF OUT Test failed bei ' + str(f) + ' Hz')
    dut.write('OUTP OFF')  # Output am DUT deaktivieren
    speki.write('calc:mark1 off')  # Marker ausschalten
    speki.write('swe:time:auto on')  # Sweep-Modus wieder auf automatisch schalten


# Test 2: REF OUT
# ben??tigte Ger??te: DUT und Speki
# pr??ft, ob der REFOUT port die Frequenzen korrekt ausgibt

q = input('REF OUT testen? (y/n)')
if q == 'y':
    print('REF OUT vom DUT mit Speki verbinden und Enter dr??cken')
    input()
    f_ref = refout_freq('dut')

    for f in f_ref:
        speki.write('freq:cent ' + str(f))  # Center einstellen
        speki.write('freq:span ' + str(0.1 * f))  # Span einstellen
        speki.write('swe:time:auto on')
        speki.write('disp:trac1:y:rlev 15dBm')  # Powerlevel am Speki setzen
        dut.write('ROSC:OUTP ON')  # Referenzoutput vom DUT aktivieren
        speki.write('calc:mark1 on')  # Marker einschalten
        sleep(t)
        speki.write('calc:mark1:max')  # Marker auf Peak setzen
        sleep(t)
        freq_refout = speki.query('calc:mark1:x?')  # Frequenz vom Marker abfragen
        print('f: ' + freq_refout + ' Hz')
        dev_refout = (float(freq_refout) - f) / f
        print('rel. Abweichung: ' + str("{:.3f}".format(dev_refout)))

        # pr??fen, ob REF OUT-Frequenz weniger als 0.5% vom Sollwert abweicht
        if abs(dev_refout) < 0.005:
            print('REF OUT-Test erfolgreich')
        else:
            print('REF OUT-Test gescheitert')
    dut.write('ROSC:OUTP OFF')
    speki.write('calc:mark1 off')  # Marker ausschalten

# Test 3: REF IN
# ben??tigte Ger??te: DUT und zus??tzlichen Geni
# pr??ft, ob Lock mit anderem Geni m??glich ist
q = input('REF IN testen? (y/n)')
if q == 'y':
    print('REF IN vom DUT mit REF OUT Geni verbinden und Enter dr??cken')
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
        dut.write('rosc:lock:test')  # einf??gen, um den Lockstatus zu aktualisieren
        sleep(3)  # gem??ss Programming Manual muss nach "rosc:lock:test" 3s gewartet werden
        lock_status = dut.query('rosc:lock?')  # Lockstatus abfragen
        sleep(t)
        if lock_status == '0':
            print('REF IN test failed: Lock nicht m??glich')
        elif lock_status == '1':
            print('REF IN test erfolgreich: Lock mit Geni ist erfolgt')
        geni.write('rosc:outp off')  # REF OUT vom Geni ausschalten
        dut.write('rosc:sour int')  # REF IN Quelle vom DUT auf INT setzen

# Test 4: FUNC OUT / TRIG OUT
# ben??tigte Ger??te: DUT und Speki
# pr??ft bei verschiedenen Frequenzen, ob der FUNC OUT Sinus die korrekte Frequenz ausgibt
q = input('FUNC OUT / TRIG OUT testen? (y/n)')
if q == 'y':
    print('FUNC OUT /TRIG OUT vom DUT mit Speki verbinden und Enter dr??cken')
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
        print('rel. Abweichung f FUNC OUT / TRIG OUT: ' + str("{:.4f}".format(dev_funcout_f)))
        if abs(dev_funcout_f) < 0.005 and float(p_func) > -5:  # Test bestanden, wenn Frequenz-Abweichung < 0.5% ist
            print('FUNC OUT / TRIG OUT: Test erfolgreich bei ' + str("{:.3f}".format(f)) + 'Hz')
        else:
            print('FUNC OUT / TRIG OUT: Test failed bei ' + str("{:.3f}".format(f)) + 'Hz')
    dut.write('lfo:stat off')  # FUNC OUT port abschalten
    speki.write('calc:mark1:off')  # Marker abschalten

# Test 5: TRIG IN
# ben??tigte Ger??te: Geni, DUT, Speki
# pr??ft, ob mit dem TRIG IN port vom DUT ein Frequenzsweep durchgef??hrt werden kann
q = input('TRIG IN testen? (y/n)')
if q == 'y':
    print('TRIG/FUNC OUT vom Geni mit TRIG IN vom DUT verbinden, RF OUT DUT mit Speki verbinden und Enter dr??cken')
    input()
    amp = 0.5  # Spannungsamplitude definieren [V]
    amp_dBm = math.ceil(10 * math.log10((amp ** 2 / 50) * 1000))  # berechne theoretische, gerundete Leistung in dBm
    freq_trig = 20
    freq_start = 1e6
    freq_stop = 2e6
    pts = 100

    # settings speki setzen
    speki.write('disp:trac1:y:rlev ' + str(amp_dBm + 5))  # powerlevel speki einstellen
    speki.write('freq:start ' + str(freq_start))  # start frequenz speki einstellen
    speki.write('freq:stop ' + str(freq_stop))  # stop frequenz speki einstellen

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
    t = input('Ist ein Frequenz-Sweep am Speki erkennbar? (y/n)')
    if t == 'y':
        print('TRIG IN erfolgreich getestet')
    else:
        print('TRIG IN Test failed')

    dut.write('outp off')
    dut.write('freq:mode cw')
    geni.write('lfo:stat off')

# Test 6: MOD IN / ??M
# ben??tigte Ger??te: Geni, DUT, Speki
# pr??ft, ob mit dem DUT eine Frequenzmodulation durchgef??hrt werden kann
# Der LF-Output des Genis dient mit eine Rechtecksignal als Quelle
q = input('MOD IN / ??M testen? (y/n)')
if q == 'y':
    print('TRIG/FUNC OUT vom Geni mit MOD IN / ??M vom DUT verbinden, RF OUT DUT mit Speki verbinden und Enter dr??cken')
    input()
    freq_modin = 1e6
    # Settings Speki
    speki.write('disp:trac1:y:rlev 20')  # powerlevel speki einstellen
    speki.write('freq:cent ' + str(freq_modin))  # center Frequenz Speki einstellen
    speki.write('freq:span ' + str(freq_modin/10))  # span frequenz speki einstellen

    # Settings Geni
    geni.write('lfo:sour lfg')  # TRIG OUT/FUNC OUT Geni auf low frequency generator setzen
    geni.write('lfo:shap sine')  # TRIG OUT/FUNC OUT Form auf square setzen
    geni.write('lfo freq 10e3')  # TRIG OUT Frequenz auf 10kHz setzen
    geni.write('lfo:ampl 1')  # TRIG OUT/FUNC OUt Amplitude auf 1V setzen

    # Settings DUT
    dut.write('pow:mode CW')  # CW-Modus am Dut einstellen
    dut.write('freq ' + str(freq_modin))  # CW-Frequenz am DUT setzen
    dut.write('POW 0')  # Poweroutput vom DUT auf 0dBm setzen
    dut.write('fm:sour ext')  # FM-Quelle auf extern setzen
    dut.write('fm:sens 5000')  # FM-Sensitivit??t auf 5kHz/V setzen

    # Geni und DUT einschalten
    dut.write('OUTP ON')  # Output am DUT aktivieren
    dut.write('fm:stat on')
    geni.write('lfo:stat on')  # LF-Signal am Geni einschalten

    t = input('Ist eine Frequenzmodulation am Speki erkennbar? (y/n)')
    if t == 'y':
        print('MOD IN / ??M erfolgreich getestet')
    else:
        print('MOD IN / ??M Test failed')

    # Geni und DUT wieder ausschalten
    dut.write('OUTP OFF')
    dut.write('fm:stat off')
    geni.write('lfo:stat off')

# Test 7: PULSE IN / AM PULSE
# ben??tigte Ger??te: Geni, DUT, Speki
# pr??ft, ob mit dem DUT eine Pulsmodulation
q = input('PULSE IN / AM PULSE testen? (y/n)')
if q == 'y':
    print('''TRIG / FUNC OUT vom Geni mit PULSE IN / AM PULSE vom DUT verbinden
          RF OUT DUT mit Speki verbinden und Enter dr??cken''')
    input()
    freq_p_modin = 10e6
    # Settings Speki
    speki.write('disp:trac1:y:rlev 20')  # powerlevel Speki einstellen
    speki.write('freq:cent ' + str(freq_p_modin))  # center Frequenz Speki einstellen
    speki.write('freq:span ' + str(freq_p_modin/10))  # span frequenz Speki einstellen

    # Settings Geni
    geni.write('lfo:sour lfg')  # TRIG OUT/FUNC OUT Geni auf low frequency generator setzen
    geni.write('lfo:shap square')  # TRIG OUT/FUNC OUT Form auf Rechteck setzen
    geni.write('lfo freq 10')  # TRIG OUT/FUNC OUT Frequenz auf 10Hz setzen
    geni.write('lfo:ampl 1')  # TRIG OUT/FUNC OUT Amplitude auf 1V setzen

    # Settings DUT
    dut.write('pow:mode CW')  # CW-Modus am Dut einstellen
    dut.write('freq ' + str(freq_p_modin))  # CW-Frequenz am DUT setzen
    dut.write('POW 0')  # Poweroutput vom DUT auf 0dBm setzen
    dut.write('pulm:sour ext')  # Pulsemodulations-Quelle auf extern setzen

    # Geni und DUT einschalten
    dut.write('OUTP ON')  # Output am DUT aktivieren
    dut.write('pulm:stat on')  # Pulsmodulation am DUT einschalten
    geni.write('lfo:stat on')  # LF-Signal am Geni einschalten

    t = input('Ist eine Pulsmodulation am Speki erkennbar? (y/n)')
    if t == 'y':
        print('PULSE IN / AM PULSE erfolgreich getestet')
    else:
        print('PULSE IN / AM PULSE Test failed')

    # Geni und DUT wieder ausschalten
    dut.write('OUTP OFF')
    dut.write('pulm:stat off')
    geni.write('lfo:stat off')

# schliesse die VISA Verbindungen
speki.close()
dut.close()
