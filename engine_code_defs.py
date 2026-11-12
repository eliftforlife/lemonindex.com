# Engine code meanings (11-10). Written in our own words.
# Generic codes follow the standard SAE J2012 / ISO 15031-6 code titles (the titles are standard facts); the plain-English
# explanations, severities and causes are ours, checked against reference descriptions. Manufacturer codes (P1xxx, B1/C1/U1-U3 ...)
# are only explained where the meaning for that make was verified (see MAKE below); otherwise the site says the meaning depends on the make.
# Severity: 1 = drive on, get it checked; 2 = get it fixed soon; 3 = stop driving / fix now.

D = {}
def add(code, title, meaning, sev, causes):
    D[code] = dict(t=title, m=meaning, s=sev, c=causes)

ORD = {1: 'one', 2: 'two', 3: 'three', 4: 'four', 5: 'five', 6: 'six', 7: 'seven', 8: 'eight', 9: 'nine', 10: 'ten', 11: 'eleven', 12: 'twelve'}

# --- Misfires, ignition, injectors -----------------------------------------------------------------------------------------
add('P0300', 'Random/Multiple Cylinder Misfire Detected', 'The engine computer sees misfires that move around between cylinders instead of staying in one. The engine may shake, stumble or feel down on power. If the check engine light flashes, the misfire is bad enough to overheat the catalytic converter: slow down and get it checked right away.', 2,
    ['Worn spark plugs or ignition coils', 'Vacuum leak', 'Low fuel pressure or dirty injectors', 'Engine mechanical problem (compression, valve timing)'])
for n in range(1, 13):
    add(f'P03{n:02d}', f'Cylinder {n} Misfire Detected', f'Cylinder {n} is not firing properly, so the engine runs rough and loses some power. A flashing check engine light means the misfire is serious enough to damage the catalytic converter, so slow down and get it checked right away.', 2,
        [f'Spark plug or ignition coil on cylinder {n}', f'Fuel injector on cylinder {n}', 'Vacuum leak near that cylinder', 'Low compression (valve or piston ring problem)'])
add('P0316', 'Misfire Detected on Startup (First 1000 Revolutions)', 'The engine misfired in the first moments after starting. It often shows up as a rough or shaky cold start.', 2,
    ['Spark plugs or coils', 'Leaking fuel injector', 'Coolant leaking into a cylinder', 'Carbon buildup on the valves'])
for n in range(1, 13):
    add(f'P0{350 + n}', f'Ignition Coil {chr(64 + n)} Primary/Secondary Circuit', f'The computer sees an electrical fault in ignition coil {chr(64 + n)} (usually the coil for cylinder {n}). That cylinder may misfire. If the check engine light flashes, ease off and get it checked right away.', 2,
        ['Failed ignition coil', 'Damaged coil wiring or connector', 'Worn spark plug overloading the coil'])
    add(f'P02{n:02d}', f'Cylinder {n} Injector Circuit/Open', f'The fuel injector circuit for cylinder {n} is open or faulty, so that cylinder may get no fuel and misfire.', 2,
        [f'Failed injector on cylinder {n}', 'Broken wiring or connector', 'Engine computer driver fault'])

# --- Cam / crank timing ------------------------------------------------------------------------------------------------------
for code, b, cam, what, sev in [('P0010', 1, 'intake', 'Actuator Circuit', 2), ('P0011', 1, 'intake', 'Timing Over-Advanced or System Performance', 2), ('P0012', 1, 'intake', 'Timing Over-Retarded', 2),
                                 ('P0013', 1, 'exhaust', 'Actuator Circuit', 2), ('P0014', 1, 'exhaust', 'Timing Over-Advanced or System Performance', 2), ('P0015', 1, 'exhaust', 'Timing Over-Retarded', 2),
                                 ('P0020', 2, 'intake', 'Actuator Circuit', 2), ('P0021', 2, 'intake', 'Timing Over-Advanced or System Performance', 2), ('P0022', 2, 'intake', 'Timing Over-Retarded', 2),
                                 ('P0023', 2, 'exhaust', 'Actuator Circuit', 2), ('P0024', 2, 'exhaust', 'Timing Over-Advanced or System Performance', 2), ('P0025', 2, 'exhaust', 'Timing Over-Retarded', 2)]:
    add(code, f'{"A" if cam == "intake" else "B"} Camshaft Position {what} ({cam.title()}, Bank {b})',
        f'The variable valve timing for the {cam} camshaft on bank {b} isn\'t where the computer asked it to be. The engine can idle rough, lose power or use more fuel. Low or dirty oil is a common trigger, because oil pressure moves the timing.', sev,
        ['Low, old or wrong-grade engine oil', 'Sticking oil control (VVT) solenoid', 'Worn or stretched timing chain', 'Faulty cam phaser'])
for code, b, s in [('P0016', 1, 'A'), ('P0017', 1, 'B'), ('P0018', 2, 'A'), ('P0019', 2, 'B')]:
    add(code, f'Crankshaft Position - Camshaft Position Correlation (Bank {b} Sensor {s})', f'The crankshaft and the bank {b} camshaft aren\'t lined up the way the computer expects. That usually points to timing chain or belt problems, so it\'s worth checking early before it gets worse.', 3,
        ['Stretched timing chain or jumped belt', 'Worn chain guides or tensioner', 'Faulty cam or crank sensor', 'Oil control (VVT) problem'])
add('P0008', 'Engine Position System Performance (Bank 1)', 'The engine computer sees the cam and crank timing drifting out of line on bank 1. On many engines this is an early sign of a stretched timing chain.', 3,
    ['Stretched timing chain', 'Worn chain guides or tensioner', 'Faulty cam phaser or VVT solenoid'])
add('P0009', 'Engine Position System Performance (Bank 2)', 'The cam and crank timing is drifting out of line on bank 2, often from a stretched timing chain.', 3,
    ['Stretched timing chain', 'Worn chain guides or tensioner', 'Faulty cam phaser or VVT solenoid'])
add('P000A', 'Intake Camshaft Position Slow Response (Bank 1)', 'The bank 1 intake cam timing changes slower than commanded.', 2, ['Dirty or low oil', 'Sticking VVT solenoid', 'Worn cam phaser'])
add('P000B', 'Exhaust Camshaft Position Slow Response (Bank 1)', 'The bank 1 exhaust cam timing changes slower than commanded.', 2, ['Dirty or low oil', 'Sticking VVT solenoid', 'Worn cam phaser'])
add('P000D', 'Exhaust Camshaft Position Slow Response (Bank 2)', 'The bank 2 exhaust cam timing changes slower than commanded.', 2, ['Dirty or low oil', 'Sticking VVT solenoid', 'Worn cam phaser'])
add('P0335', 'Crankshaft Position Sensor A Circuit', 'The computer lost or can\'t read the crankshaft position signal. Without it the engine can stall and may not restart.', 3, ['Failed crankshaft position sensor', 'Damaged wiring or connector', 'Damaged tone ring'])
add('P0336', 'Crankshaft Position Sensor A Range/Performance', 'The crankshaft position signal is erratic. The engine can stumble, stall or be hard to start.', 3, ['Failing crank sensor', 'Loose or chafed wiring', 'Damaged tone ring'])
add('P0339', 'Crankshaft Position Sensor A Circuit Intermittent', 'The crankshaft position signal drops out now and then, which can cause sudden stalling.', 3, ['Failing crank sensor', 'Loose connector', 'Chafed wiring'])
add('P0340', 'Camshaft Position Sensor A Circuit (Bank 1)', 'The computer can\'t read the bank 1 camshaft position sensor. Expect hard starting, stalling or a rough run.', 2, ['Failed cam sensor', 'Wiring or connector fault', 'Timing problem'])
add('P0341', 'Camshaft Position Sensor A Range/Performance (Bank 1)', 'The bank 1 camshaft signal doesn\'t match what the computer expects.', 2, ['Failing cam sensor', 'Stretched timing chain or jumped belt', 'Wiring fault'])
add('P0344', 'Camshaft Position Sensor A Circuit Intermittent (Bank 1)', 'The bank 1 camshaft signal drops out now and then.', 2, ['Failing cam sensor', 'Loose connector', 'Chafed wiring'])
add('P0345', 'Camshaft Position Sensor A Circuit (Bank 2)', 'The computer can\'t read the bank 2 camshaft position sensor.', 2, ['Failed cam sensor', 'Wiring or connector fault'])
add('P0365', 'Camshaft Position Sensor B Circuit (Bank 1)', 'The computer can\'t read the second (usually exhaust) cam sensor on bank 1.', 2, ['Failed cam sensor', 'Wiring or connector fault'])
add('P0366', 'Camshaft Position Sensor B Range/Performance (Bank 1)', 'The second cam sensor signal on bank 1 doesn\'t look right.', 2, ['Failing cam sensor', 'Timing chain wear', 'Wiring fault'])
add('P0369', 'Camshaft Position Sensor B Circuit Intermittent (Bank 1)', 'The second cam sensor signal on bank 1 drops out now and then.', 2, ['Failing cam sensor', 'Loose connector'])
add('P0320', 'Ignition/Distributor Engine Speed Input Circuit', 'The computer lost the engine speed signal it uses to time the spark. The engine can stall or not start.', 3, ['Failed crank or distributor pickup sensor', 'Wiring fault'])
add('P0324', 'Knock Control System Error', 'The knock detection system found a fault, so the computer may pull timing and the engine feels weaker.', 2, ['Faulty knock sensor', 'Wiring fault', 'Real engine knock'])
add('P0325', 'Knock Sensor 1 Circuit (Bank 1)', 'The knock sensor signal is missing or out of range, so the computer plays it safe and the engine may feel sluggish.', 1, ['Failed knock sensor', 'Wiring or connector fault'])
add('P0326', 'Knock Sensor 1 Range/Performance (Bank 1)', 'The knock sensor signal is outside its expected range.', 1, ['Failing knock sensor', 'Loose sensor mounting', 'Real engine knock'])

# --- Fuel and air ---------------------------------------------------------------------------------------------------------------
add('P0087', 'Fuel Rail/System Pressure Too Low', 'The engine isn\'t getting the fuel pressure it needs. That can cause hesitation, loss of power and stalling, especially under load.', 3, ['Weak or failing fuel pump', 'Clogged fuel filter', 'Faulty fuel pressure sensor or regulator', 'High-pressure pump wear (direct injection)'])
add('P0088', 'Fuel Rail/System Pressure Too High', 'Fuel pressure is higher than the computer wants.', 2, ['Faulty pressure regulator', 'Faulty pressure sensor', 'Restricted return line'])
add('P0089', 'Fuel Pressure Regulator 1 Performance', 'The fuel pressure regulator isn\'t holding the pressure the computer asks for. Stalling and hesitation are common.', 3, ['Faulty regulator or high-pressure pump', 'Faulty pressure sensor', 'Wiring fault'])
add('P0090', 'Fuel Pressure Regulator 1 Control Circuit', 'The circuit that controls fuel pressure has an electrical fault.', 2, ['Failed regulator/control valve', 'Wiring or connector fault'])
add('P0091', 'Fuel Pressure Regulator 1 Control Circuit Low', 'The fuel pressure control circuit reads too low (often a short to ground).', 2, ['Shorted wiring', 'Failed regulator'])
add('P00C6', 'Fuel Rail Pressure Too Low - Engine Cranking', 'Fuel pressure is too low while the engine is cranking, so it may be slow or unable to start.', 3, ['Weak fuel pump', 'Faulty high-pressure pump', 'Leaking fuel system'])
add('P0100', 'Mass or Volume Air Flow Sensor A Circuit', 'The air flow sensor isn\'t reporting properly, so the computer guesses how much fuel to add.', 2, ['Failed or dirty MAF sensor', 'Wiring or connector fault', 'Air leak after the sensor'])
add('P0101', 'Mass or Volume Air Flow Sensor A Range/Performance', 'The air flow reading doesn\'t match what the computer expects. The engine may hesitate, stall or idle rough.', 2, ['Dirty MAF sensor', 'Air leak after the sensor', 'Clogged air filter', 'Failing MAF sensor'])
add('P0102', 'Mass or Volume Air Flow Sensor A Circuit Low', 'The air flow sensor signal is too low.', 2, ['Dirty or failed MAF sensor', 'Open or shorted wiring', 'Air leak'])
add('P0103', 'Mass or Volume Air Flow Sensor A Circuit High', 'The air flow sensor signal is too high.', 2, ['Failed MAF sensor', 'Wiring fault'])
add('P0106', 'Manifold Absolute Pressure/Barometric Pressure Sensor Range/Performance', 'The MAP sensor reading doesn\'t fit what the engine is doing.', 2, ['Failing MAP sensor', 'Vacuum leak or cracked hose', 'Wiring fault'])
add('P0107', 'Manifold Absolute Pressure Sensor Circuit Low', 'The MAP sensor signal is too low.', 2, ['Failed MAP sensor', 'Wiring fault'])
add('P0108', 'Manifold Absolute Pressure Sensor Circuit High', 'The MAP sensor signal is too high.', 2, ['Failed MAP sensor', 'Vacuum leak', 'Wiring fault'])
add('P0068', 'MAP/MAF - Throttle Position Correlation', 'The air flow, manifold pressure and throttle readings don\'t agree with each other. The car may go into reduced power.', 2, ['Air leak after the throttle', 'Dirty throttle body', 'Faulty MAF or MAP sensor'])
add('P0113', 'Intake Air Temperature Sensor 1 Circuit High', 'The intake air temperature sensor reads as an open circuit (very cold).', 1, ['Unplugged or failed IAT sensor', 'Open wiring'])
add('P0117', 'Engine Coolant Temperature Sensor 1 Circuit Low', 'The coolant temperature sensor reads too low a voltage (looks extremely hot to the computer).', 2, ['Failed coolant temp sensor', 'Shorted wiring'])
add('P0120', 'Throttle/Pedal Position Sensor A Circuit', 'The throttle position sensor signal has an electrical fault. The car may go into reduced power.', 3, ['Failed throttle position sensor', 'Wiring fault', 'Throttle body fault'])
add('P0121', 'Throttle/Pedal Position Sensor A Range/Performance', 'The throttle position reading doesn\'t make sense for the conditions. Hesitation or reduced power is common.', 3, ['Failing throttle position sensor', 'Dirty throttle body', 'Wiring fault'])
add('P0122', 'Throttle/Pedal Position Sensor A Circuit Low', 'The throttle position signal is too low.', 3, ['Failed sensor', 'Shorted or open wiring'])
add('P0123', 'Throttle/Pedal Position Sensor A Circuit High', 'The throttle position signal is too high.', 3, ['Failed sensor', 'Wiring fault'])
add('P0221', 'Throttle/Pedal Position Sensor B Range/Performance', 'The second throttle position signal doesn\'t make sense, so the car may limit power.', 3, ['Failing throttle body sensor', 'Wiring fault'])
add('P0222', 'Throttle/Pedal Position Sensor B Circuit Low', 'The second throttle position signal is too low.', 3, ['Failed sensor', 'Wiring fault'])
add('P0126', 'Insufficient Coolant Temperature for Stable Operation', 'The engine takes too long to warm up.', 1, ['Thermostat stuck open', 'Faulty coolant temp sensor'])
add('P0128', 'Coolant Thermostat (Coolant Temperature Below Thermostat Regulating Temperature)', 'The engine isn\'t reaching normal temperature fast enough. The heater may blow cool and fuel economy drops.', 1, ['Thermostat stuck open', 'Faulty coolant temp sensor', 'Low coolant'])
add('P0170', 'Fuel Trim (Bank 1)', 'The computer had to adjust fuel on bank 1 beyond its normal range.', 2, ['Vacuum leak', 'Fuel delivery problem', 'Faulty MAF or O2 sensor'])
add('P0171', 'System Too Lean (Bank 1)', 'Bank 1 is getting too much air or too little fuel. The engine may hesitate or idle rough.', 2, ['Vacuum leak (hoses, intake gasket, PCV)', 'Dirty MAF sensor', 'Weak fuel pump or clogged filter', 'Leaking exhaust before the O2 sensor'])
add('P0172', 'System Too Rich (Bank 1)', 'Bank 1 is getting too much fuel. You may smell fuel or see worse mileage.', 2, ['Leaking injector', 'Faulty fuel pressure regulator', 'Dirty MAF sensor', 'Faulty O2 sensor'])
add('P0174', 'System Too Lean (Bank 2)', 'Bank 2 is getting too much air or too little fuel.', 2, ['Vacuum leak', 'Dirty MAF sensor', 'Weak fuel pump or clogged filter'])
add('P0175', 'System Too Rich (Bank 2)', 'Bank 2 is getting too much fuel.', 2, ['Leaking injector', 'Faulty regulator', 'Dirty MAF sensor', 'Faulty O2 sensor'])
add('P0190', 'Fuel Rail Pressure Sensor A Circuit', 'The fuel pressure sensor has an electrical fault.', 2, ['Failed fuel pressure sensor', 'Wiring fault'])
add('P0191', 'Fuel Rail Pressure Sensor A Range/Performance', 'The fuel pressure reading doesn\'t match what the computer expects. Hard starting or stalling can follow.', 3, ['Failing pressure sensor', 'Fuel pump or regulator problem', 'Wiring fault'])
add('P0192', 'Fuel Rail Pressure Sensor A Circuit Low', 'The fuel pressure sensor signal is too low.', 2, ['Failed sensor', 'Wiring fault'])
add('P0193', 'Fuel Rail Pressure Sensor A Circuit High', 'The fuel pressure sensor signal is too high.', 2, ['Failed sensor', 'Wiring fault'])
add('P0196', 'Engine Oil Temperature Sensor Range/Performance', 'The oil temperature reading doesn\'t make sense.', 1, ['Failing oil temp sensor', 'Wiring fault'])
add('P0217', 'Engine Coolant Over Temperature Condition', 'The engine is overheating. Pull over safely and shut it off: driving an overheating engine can warp or crack it.', 3, ['Low coolant or a leak', 'Failed water pump or thermostat', 'Cooling fan not working', 'Blown head gasket'])
add('P0218', 'Transmission Fluid Over Temperature Condition', 'The transmission is running too hot. Ease off and let it cool; heat wears a transmission fast.', 3, ['Low or old transmission fluid', 'Towing or heavy load', 'Blocked transmission cooler'])
add('P0219', 'Engine Overspeed Condition', 'The engine went past its safe RPM.', 2, ['Missed shift or downshift at speed', 'Transmission slipping'])
add('P0234', 'Turbocharger/Supercharger A Overboost Condition', 'The turbo is making more boost than it should, so the computer may cut power.', 2, ['Stuck wastegate', 'Faulty boost control solenoid', 'Faulty boost sensor'])
add('P0236', 'Turbocharger/Supercharger Boost Sensor A Range/Performance', 'The boost pressure reading doesn\'t make sense.', 2, ['Faulty boost sensor', 'Boost leak', 'Wiring fault'])
add('P0299', 'Turbocharger/Supercharger A Underboost Condition', 'The turbo isn\'t making the boost the computer asked for, so the car feels slow and may go into reduced power.', 2, ['Boost leak (cracked hose or intercooler)', 'Sticking wastegate', 'Worn turbocharger', 'Faulty boost control solenoid'])

# --- Emissions: O2 sensors, catalyst, EGR, secondary air, EVAP --------------------------------------------------------
add('P0030', 'HO2S Heater Control Circuit (Bank 1 Sensor 1)', 'The heater in the upstream oxygen sensor has an electrical fault, so the sensor is slow to start working.', 1, ['Failed O2 sensor', 'Blown fuse', 'Wiring fault'])
add('P0031', 'HO2S Heater Control Circuit Low (Bank 1 Sensor 1)', 'The upstream O2 sensor heater circuit reads too low.', 1, ['Failed O2 sensor heater', 'Wiring fault'])
add('P0037', 'HO2S Heater Control Circuit Low (Bank 1 Sensor 2)', 'The downstream O2 sensor heater circuit reads too low.', 1, ['Failed O2 sensor heater', 'Wiring fault'])
add('P0131', 'O2 Sensor Circuit Low Voltage (Bank 1 Sensor 1)', 'The upstream O2 sensor reads too low.', 1, ['Failed O2 sensor', 'Exhaust leak', 'Wiring fault'])
add('P0133', 'O2 Sensor Circuit Slow Response (Bank 1 Sensor 1)', 'The upstream O2 sensor reacts too slowly, which hurts fuel control and mileage.', 1, ['Aged O2 sensor', 'Exhaust leak', 'Contamination (oil or coolant)'])
add('P0135', 'O2 Sensor Heater Circuit (Bank 1 Sensor 1)', 'The upstream O2 sensor\'s heater isn\'t working.', 1, ['Failed O2 sensor', 'Blown fuse', 'Wiring fault'])
add('P0136', 'O2 Sensor Circuit (Bank 1 Sensor 2)', 'The downstream O2 sensor (after the catalytic converter) has a fault.', 1, ['Failed O2 sensor', 'Wiring fault', 'Exhaust leak'])
add('P0137', 'O2 Sensor Circuit Low Voltage (Bank 1 Sensor 2)', 'The downstream O2 sensor reads too low.', 1, ['Failed O2 sensor', 'Exhaust leak', 'Wiring fault'])
add('P0138', 'O2 Sensor Circuit High Voltage (Bank 1 Sensor 2)', 'The downstream O2 sensor reads too high.', 1, ['Failed O2 sensor', 'Wiring fault', 'Engine running rich'])
add('P0140', 'O2 Sensor Circuit No Activity Detected (Bank 1 Sensor 2)', 'The downstream O2 sensor isn\'t sending a usable signal.', 1, ['Failed O2 sensor', 'Open wiring'])
add('P0141', 'O2 Sensor Heater Circuit (Bank 1 Sensor 2)', 'The downstream O2 sensor\'s heater isn\'t working.', 1, ['Failed O2 sensor', 'Blown fuse', 'Wiring fault'])
add('P2A00', 'O2 Sensor Circuit Range/Performance (Bank 1 Sensor 1)', 'The upstream O2 sensor signal is out of its expected range.', 1, ['Aged O2 sensor', 'Exhaust leak', 'Fuel mixture problem'])
add('P2195', 'O2 Sensor Signal Biased/Stuck Lean (Bank 1 Sensor 1)', 'The upstream O2 sensor keeps reading lean.', 2, ['Failing O2 sensor', 'Vacuum or exhaust leak', 'Low fuel pressure'])
add('P2196', 'O2 Sensor Signal Biased/Stuck Rich (Bank 1 Sensor 1)', 'The upstream O2 sensor keeps reading rich.', 2, ['Failing O2 sensor', 'Leaking injector', 'Fuel pressure too high'])
add('P2198', 'O2 Sensor Signal Biased/Stuck Rich (Bank 2 Sensor 1)', 'The bank 2 upstream O2 sensor keeps reading rich.', 2, ['Failing O2 sensor', 'Leaking injector'])
add('P2096', 'Post Catalyst Fuel Trim System Too Lean (Bank 1)', 'After the catalytic converter, the exhaust reads too lean for too long.', 2, ['Exhaust leak', 'Failing O2 sensor', 'Vacuum leak'])
add('P2097', 'Post Catalyst Fuel Trim System Too Rich (Bank 1)', 'After the catalytic converter, the exhaust reads too rich for too long.', 2, ['Failing catalytic converter', 'Failing O2 sensor', 'Engine running rich'])
add('P2099', 'Post Catalyst Fuel Trim System Too Rich (Bank 2)', 'After the bank 2 catalytic converter, the exhaust reads too rich.', 2, ['Failing catalytic converter', 'Failing O2 sensor'])
add('P2191', 'System Too Lean at Higher Load (Bank 1)', 'Bank 1 runs lean when you accelerate or pull hard.', 2, ['Weak fuel pump', 'Clogged fuel filter or injectors', 'Dirty MAF sensor'])
for code, b in [('P219A', 1), ('P219B', 2)]:
    add(code, f'Bank {b} Air-Fuel Ratio Imbalance', f'One or more cylinders on bank {b} are getting a different air-fuel mix than the others. The engine may idle rough or hesitate.', 2,
        ['Clogged or leaking fuel injector', 'Vacuum leak at one cylinder', 'Faulty O2 sensor', 'Carbon on the intake valves'])
for code, n in [('P219C', 1), ('P219D', 2), ('P219E', 3), ('P219F', 4)]:
    add(code, f'Cylinder {n} Air-Fuel Ratio Imbalance', f'Cylinder {n} is getting a different air-fuel mix than the other cylinders.', 2, [f'Injector on cylinder {n}', 'Vacuum leak at that cylinder', 'Carbon buildup'])
add('P0420', 'Catalyst System Efficiency Below Threshold (Bank 1)', 'The catalytic converter on bank 1 isn\'t cleaning the exhaust as well as it should. The car usually drives normally, but it can fail an emissions test.', 1,
    ['Worn-out catalytic converter', 'Faulty downstream O2 sensor', 'Exhaust leak', 'Misfires or oil burning that damaged the converter'])
add('P0421', 'Warm Up Catalyst Efficiency Below Threshold (Bank 1)', 'The small warm-up catalytic converter on bank 1 isn\'t working as well as it should.', 1, ['Worn converter', 'Faulty O2 sensor', 'Exhaust leak'])
add('P0430', 'Catalyst System Efficiency Below Threshold (Bank 2)', 'The catalytic converter on bank 2 isn\'t cleaning the exhaust as well as it should.', 1, ['Worn-out catalytic converter', 'Faulty downstream O2 sensor', 'Exhaust leak', 'Misfires that damaged the converter'])
add('P0401', 'Exhaust Gas Recirculation A Flow Insufficient Detected', 'Not enough exhaust gas is being sent back into the engine. It can cause pinging and higher emissions.', 1, ['Carbon-clogged EGR valve or passages', 'Failed EGR valve', 'Faulty EGR sensor'])
add('P0402', 'Exhaust Gas Recirculation A Flow Excessive Detected', 'Too much exhaust gas is going back into the engine, which can cause a rough idle or stalling.', 2, ['EGR valve stuck open', 'Faulty EGR control'])
add('P0403', 'Exhaust Gas Recirculation A Control Circuit', 'The EGR valve control circuit has an electrical fault.', 1, ['Failed EGR valve', 'Wiring fault'])
add('P0404', 'Exhaust Gas Recirculation A Control Circuit Range/Performance', 'The EGR valve isn\'t moving the way it\'s commanded.', 1, ['Sticking EGR valve', 'Carbon buildup', 'Wiring fault'])
add('P0405', 'Exhaust Gas Recirculation Sensor A Circuit Low', 'The EGR position sensor reads too low.', 1, ['Failed EGR valve/sensor', 'Wiring fault'])
add('P0406', 'Exhaust Gas Recirculation Sensor A Circuit High', 'The EGR position sensor reads too high.', 1, ['Failed EGR valve/sensor', 'Wiring fault'])
add('P0410', 'Secondary Air Injection System', 'The system that pumps air into the exhaust during cold starts has a fault.', 1, ['Failed air pump', 'Stuck check valve', 'Blown fuse or relay'])
add('P0411', 'Secondary Air Injection System Incorrect Flow Detected', 'The secondary air system isn\'t moving the right amount of air.', 1, ['Failed air pump', 'Stuck or leaking valve', 'Cracked hose'])
add('P0418', 'Secondary Air Injection System Control A Circuit', 'The relay or circuit that runs the secondary air pump has a fault.', 1, ['Failed relay', 'Wiring fault'])
add('P0491', 'Secondary Air Injection System Insufficient Flow (Bank 1)', 'The secondary air system isn\'t moving enough air on bank 1.', 1, ['Failed air pump', 'Stuck valve', 'Clogged passage'])
for code, b, st in [('P2440', 1, 'Stuck Open'), ('P2441', 1, 'Stuck Closed'), ('P2442', 2, 'Stuck Open'), ('P2443', 2, 'Stuck Closed')]:
    add(code, f'Secondary Air Injection System Switching Valve {st} (Bank {b})', f'The valve that lets cold-start air into the bank {b} exhaust is {st.lower()}.' + (' Exhaust moisture can then reach and damage the air pump.' if st == 'Stuck Open' else ''), 1,
        ['Failed switching (check) valve', 'Failed air pump', 'Water or carbon in the valve'])
add('P2444', 'Secondary Air Injection System Pump Stuck On (Bank 1)', 'The secondary air pump keeps running when it shouldn\'t.', 1, ['Stuck relay', 'Wiring fault'])
add('P2445', 'Secondary Air Injection System Pump Stuck Off (Bank 1)', 'The secondary air pump isn\'t running when commanded.', 1, ['Failed air pump', 'Failed relay or fuse'])
add('P2431', 'Secondary Air Injection System Air Flow/Pressure Sensor Circuit Range/Performance (Bank 1)', 'The secondary air pressure sensor reading doesn\'t look right.', 1, ['Failed pressure sensor', 'Leaking hose', 'Failed pump'])
add('P2432', 'Secondary Air Injection System Air Flow/Pressure Sensor Circuit Low (Bank 1)', 'The secondary air pressure sensor reads too low.', 1, ['Failed sensor', 'Wiring fault'])
add('P2433', 'Secondary Air Injection System Air Flow/Pressure Sensor Circuit High (Bank 1)', 'The secondary air pressure sensor reads too high.', 1, ['Failed sensor', 'Wiring fault'])
add('P0440', 'Evaporative Emission System', 'The system that traps fuel vapor from the gas tank has a fault. It\'s an emissions problem, not usually a drivability one.', 1, ['Loose or bad gas cap', 'Leaking EVAP hose', 'Faulty purge or vent valve'])
add('P0441', 'Evaporative Emission System Incorrect Purge Flow', 'Fuel vapor isn\'t being drawn into the engine the way it should.', 1, ['Faulty purge valve', 'Cracked or blocked hose', 'Faulty canister'])
add('P0442', 'Evaporative Emission System Leak Detected (Small Leak)', 'There\'s a small leak in the fuel vapor system.', 1, ['Gas cap not sealing', 'Cracked EVAP hose', 'Leaking purge or vent valve'])
add('P0443', 'Evaporative Emission System Purge Control Valve Circuit', 'The purge valve circuit has an electrical fault.', 1, ['Failed purge valve', 'Wiring fault'])
add('P0445', 'Evaporative Emission System Purge Control Valve Circuit Closed', 'The purge valve circuit reads shorted.', 1, ['Failed purge valve', 'Shorted wiring'])
add('P0446', 'Evaporative Emission System Vent Control Circuit', 'The EVAP vent valve isn\'t working right.', 1, ['Failed vent valve', 'Blocked vent filter', 'Wiring fault'])
add('P0448', 'Evaporative Emission System Vent Control Circuit Shorted', 'The EVAP vent valve circuit reads shorted.', 1, ['Failed vent valve', 'Shorted wiring'])
add('P0449', 'Evaporative Emission System Vent Valve/Solenoid Circuit', 'The EVAP vent valve circuit has an electrical fault.', 1, ['Failed vent solenoid', 'Wiring fault'])
add('P0451', 'Evaporative Emission System Pressure Sensor/Switch Range/Performance', 'The fuel tank pressure reading doesn\'t make sense.', 1, ['Failed tank pressure sensor', 'Wiring fault'])
add('P0452', 'Evaporative Emission System Pressure Sensor/Switch Low', 'The fuel tank pressure sensor reads too low.', 1, ['Failed sensor', 'Wiring fault'])
add('P0455', 'Evaporative Emission System Leak Detected (Large Leak)', 'There\'s a large leak in the fuel vapor system. Often it\'s just a gas cap left loose or off.', 1, ['Gas cap loose or missing', 'Disconnected or cracked EVAP hose', 'Purge or vent valve stuck open'])
add('P0456', 'Evaporative Emission System Leak Detected (Very Small Leak)', 'There\'s a very small leak in the fuel vapor system. The car drives normally.', 1, ['Gas cap seal', 'Tiny crack in an EVAP hose', 'Leaking purge or vent valve'])
add('P0457', 'Evaporative Emission System Leak Detected (Fuel Cap Loose/Off)', 'The computer thinks the gas cap is loose or missing.', 1, ['Gas cap loose, missing or worn', 'Filler neck seal'])
add('P0496', 'Evaporative Emission System High Purge Flow', 'Too much fuel vapor is being pulled into the engine, often from a purge valve stuck open. It can cause hard starts after fueling.', 2, ['Purge valve stuck open', 'Wiring fault'])
add('P2401', 'Evaporative Emission System Leak Detection Pump Control Circuit Low', 'The EVAP leak test pump circuit reads too low.', 1, ['Failed leak detection pump', 'Wiring fault'])
add('P2402', 'Evaporative Emission System Leak Detection Pump Control Circuit High', 'The EVAP leak test pump circuit reads too high.', 1, ['Failed leak detection pump', 'Wiring fault'])
add('P2422', 'Evaporative Emission System Vent Valve Stuck Closed', 'The EVAP vent valve is stuck shut, which can make it hard to fill the tank.', 1, ['Failed vent valve', 'Blocked vent filter (dirt, spiders)'])
add('P2450', 'Evaporative Emission System Switching Valve Performance/Stuck Open', 'An EVAP switching valve isn\'t working right.', 1, ['Failed switching valve', 'Wiring fault'])
add('P0460', 'Fuel Level Sensor A Circuit', 'The fuel gauge sender has an electrical fault, so the gauge may be wrong.', 1, ['Failed fuel level sender', 'Wiring fault'])
add('P0461', 'Fuel Level Sensor A Circuit Range/Performance', 'The fuel level reading doesn\'t make sense, so the gauge may jump around.', 1, ['Worn fuel level sender', 'Wiring fault'])
add('P0462', 'Fuel Level Sensor A Circuit Low', 'The fuel level sender reads too low. The gauge may show empty when it isn\'t, or the other way around.', 2, ['Failed fuel level sender', 'Wiring fault'])
add('P0463', 'Fuel Level Sensor A Circuit High', 'The fuel level sender reads too high. The gauge can show fuel that isn\'t there, which risks running out of gas.', 2, ['Failed fuel level sender', 'Open wiring or connector'])
add('P0464', 'Fuel Level Sensor A Circuit Intermittent', 'The fuel level signal drops out now and then.', 1, ['Worn sender', 'Loose connector'])
add('P043E', 'Evaporative Emission System Leak Detection Reference Orifice Low Flow', 'The EVAP leak test\'s reference port reads low flow.', 1, ['Clogged leak detection module', 'Blocked vent filter'])
add('P043F', 'Evaporative Emission System Leak Detection Reference Orifice High Flow', 'The EVAP leak test\'s reference port reads high flow.', 1, ['Failed leak detection module', 'Leak in the module'])
add('P04DB', 'Crankcase Ventilation System Disconnected', 'The PCV hose that vents the engine crankcase looks disconnected.', 2, ['Disconnected or broken PCV hose', 'Cracked fitting'])
add('P052E', 'Positive Crankcase Ventilation Regulator Valve Performance', 'The crankcase ventilation (PCV) system isn\'t controlling pressure the way it should.', 2, ['Failed PCV valve or oil separator', 'Cracked PCV hose', 'Vacuum leak'])
add('P2002', 'Diesel Particulate Filter Efficiency Below Threshold (Bank 1)', 'The diesel particulate filter isn\'t trapping soot as it should.', 2, ['Damaged particulate filter', 'Faulty pressure sensor'])
add('P2459', 'Diesel Particulate Filter Regeneration Frequency', 'The particulate filter is having to clean itself too often.', 2, ['Short trips that interrupt regeneration', 'Faulty sensor', 'Engine running rich or burning oil'])

# --- Idle, speed, power -------------------------------------------------------------------------------------------------------
add('P0500', 'Vehicle Speed Sensor A', 'The computer lost the vehicle speed signal. The speedometer, cruise control and shifting can act up.', 2, ['Failed speed sensor', 'Wiring fault', 'ABS sensor fault on some cars'])
add('P0504', 'Brake Switch A/B Correlation', 'The two brake pedal switch signals disagree. Cruise control may stop working and brake lights may act up.', 2, ['Failed brake light switch', 'Wiring fault'])
add('P0505', 'Idle Air Control System', 'The idle control isn\'t holding the right idle speed.', 2, ['Dirty throttle body or IAC valve', 'Vacuum leak', 'Failed IAC valve'])
add('P0506', 'Idle Air Control System RPM Lower Than Expected', 'The engine idles lower than it should and may stall.', 2, ['Dirty throttle body', 'Vacuum leak', 'Failing IAC'])
add('P0507', 'Idle Air Control System RPM Higher Than Expected', 'The engine idles higher than it should.', 1, ['Vacuum leak', 'Dirty throttle body', 'Failing IAC'])
add('P050A', 'Cold Start Idle Air Control System Performance', 'Right after a cold start, the idle speed isn\'t where the computer wants it.', 1, ['Dirty throttle body', 'Vacuum leak', 'Software (updates exist for some cars)'])
add('P050B', 'Cold Start Ignition Timing Performance', 'Right after a cold start, the spark timing isn\'t where the computer wants it.', 1, ['Dirty throttle body', 'Vacuum leak', 'Software'])
add('P050D', 'Cold Start Rough Idle', 'The engine idles rough right after a cold start.', 1, ['Fuel or ignition issue', 'Carbon on the valves', 'Software'])
add('P0513', 'Incorrect Immobilizer Key', 'The anti-theft system didn\'t recognize the key, so the engine may not start or may stall right away.', 3, ['Key chip not read', 'Failed immobilizer module or antenna'])
add('P0520', 'Engine Oil Pressure Sensor/Switch A Circuit', 'The oil pressure sensor has an electrical fault. Check the real oil level before driving on.', 2, ['Failed oil pressure sensor', 'Wiring fault'])
add('P0521', 'Engine Oil Pressure Sensor/Switch A Range/Performance', 'The oil pressure reading doesn\'t make sense. Check the oil level first.', 3, ['Low oil', 'Failing oil pressure sensor', 'Worn oil pump'])
add('P0523', 'Engine Oil Pressure Sensor/Switch A Circuit High', 'The oil pressure sensor reads too high.', 2, ['Failed sensor', 'Wiring fault'])
add('P0524', 'Engine Oil Pressure Too Low', 'Oil pressure is too low. Stop the engine as soon as it\'s safe: low oil pressure can destroy an engine quickly.', 3, ['Low oil level or a leak', 'Worn oil pump or bearings', 'Clogged oil pickup', 'Faulty sensor (rule it out with a gauge)'])
add('P051B', 'Crankcase Pressure Sensor Circuit Range/Performance', 'The crankcase pressure reading doesn\'t make sense.', 2, ['Failed sensor', 'PCV problem'])
add('P0556', 'Brake Booster Pressure Sensor Circuit Range/Performance', 'The brake booster vacuum reading doesn\'t make sense. Brakes may feel harder to press.', 3, ['Failed booster pressure sensor', 'Vacuum leak', 'Weak vacuum pump'])
add('P0562', 'System Voltage Low', 'The car\'s electrical voltage is too low. Lights and modules may act up, and the car may not start next time.', 2, ['Weak battery', 'Failing alternator', 'Corroded battery cables'])
add('P0571', 'Brake Switch A Circuit', 'The brake pedal switch has a fault. Cruise control and brake lights may not work right.', 2, ['Failed brake light switch', 'Wiring fault'])
add('P0597', 'Thermostat Heater Control Circuit/Open', 'The electrically heated thermostat circuit is open.', 1, ['Failed thermostat heater', 'Wiring fault'])
add('P0598', 'Thermostat Heater Control Circuit Low', 'The electrically heated thermostat circuit reads too low.', 1, ['Failed thermostat heater', 'Wiring fault'])
add('P059F', 'Active Grille Air Shutter A Performance', 'The front grille shutters aren\'t moving as commanded.', 1, ['Stuck or broken shutter', 'Failed shutter motor'])

# --- Computers and wiring -------------------------------------------------------------------------------------------------------
add('P0600', 'Serial Communication Link', 'The engine computer has trouble talking to another module.', 2, ['Wiring fault', 'Failing control module'])
add('P0601', 'Internal Control Module Memory Check Sum Error', 'The engine computer found an error in its own memory.', 2, ['Failing engine computer', 'Needs reprogramming'])
add('P0605', 'Internal Control Module Read Only Memory (ROM) Error', 'The engine computer found an error in its stored programming.', 2, ['Failing engine computer', 'Needs reprogramming'])
add('P0606', 'Control Module Processor', 'The engine computer found a fault in its own processor. Stalling or limp mode can follow.', 3, ['Failing engine computer', 'Poor power or ground to the module', 'Needs reprogramming'])
add('P0607', 'Control Module Performance', 'The engine computer isn\'t performing correctly.', 3, ['Failing engine computer', 'Power or ground fault'])
add('P060A', 'Internal Control Module Monitoring Processor Performance', 'The engine computer\'s backup processor found a problem.', 3, ['Failing engine computer', 'Software'])
add('P061A', 'Internal Control Module Torque Performance', 'The engine computer\'s torque check found a mismatch.', 3, ['Failing engine computer', 'Software'])
add('P061B', 'Internal Control Module Torque Calculation Performance', 'The engine computer\'s two torque calculations don\'t match, so it may cut power for safety.', 3, ['Software', 'Failing engine computer', 'Sensor input fault'])
add('P061C', 'Internal Control Module Engine RPM Performance', 'The engine computer\'s RPM check found a mismatch.', 3, ['Failing engine computer', 'Software'])
add('P0627', 'Fuel Pump A Control Circuit/Open', 'The fuel pump control circuit is open. The engine may not start or may stall.', 3, ['Failed fuel pump relay or module', 'Wiring fault', 'Failed fuel pump'])
add('P0638', 'Throttle Actuator Control Range/Performance (Bank 1)', 'The electronic throttle isn\'t moving the way it\'s commanded. The car may go into reduced power.', 3, ['Dirty or failing throttle body', 'Wiring fault'])
add('P0651', 'Sensor Reference Voltage B Circuit/Open', 'A 5-volt reference feed to several sensors is faulty, which can trigger a group of other codes.', 2, ['Shorted sensor on that circuit', 'Wiring fault'])
add('P0657', 'Actuator Supply Voltage A Circuit/Open', 'Power to some engine actuators is missing.', 2, ['Blown fuse', 'Failed relay', 'Wiring fault'])
add('P0685', 'ECM/PCM Power Relay Control Circuit/Open', 'The relay that powers the engine computer has a circuit fault.', 3, ['Failed main relay', 'Wiring fault'])
add('P068A', 'ECM/PCM Power Relay De-Energized - Too Early', 'The engine computer lost power sooner than expected after shut-off.', 2, ['Failing main relay', 'Weak battery', 'Wiring fault'])
add('P069E', 'Fuel Pump Control Module Requested MIL Illumination', 'The fuel pump control module found its own fault and turned on the check engine light.', 2, ['Failed fuel pump module', 'Failing fuel pump', 'Wiring fault'])
add('P06B8', 'Internal Control Module Non-Volatile Random Access Memory (NVRAM) Error', 'The engine computer found an error in its saved memory.', 2, ['Failing engine computer', 'Needs reprogramming'])
add('P06DA', 'Engine Oil Pressure Control Circuit/Open', 'The circuit that switches the oil pump between pressures is open.', 2, ['Failed oil pressure control solenoid', 'Wiring fault'])
add('P06DD', 'Engine Oil Pressure Control Circuit Stuck Off', 'Oil pressure isn\'t reaching what the computer asked for; the variable oil pump may be stuck in its low-pressure mode. Check the oil level and have the oil pressure tested right away.', 3, ['Failed oil pressure control solenoid', 'Low oil', 'Failing oil pump'])
add('P06DE', 'Engine Oil Pressure Control Circuit Stuck On', 'The variable oil pump is stuck in one pressure mode.', 2, ['Failed oil pressure control solenoid', 'Failing oil pump'])
add('P06E9', 'Engine Starter Performance', 'The starter took longer than expected to crank the engine.', 2, ['Weak battery', 'Failing starter', 'Bad cables'])
add('P2535', 'Ignition Switch Run/Start Position Circuit High', 'The ignition switch run/start circuit reads too high.', 2, ['Failed ignition switch', 'Wiring fault'])
add('P2610', 'ECM/PCM Internal Engine Off Timer Performance', 'The engine computer\'s internal off-timer isn\'t working right.', 1, ['Failing engine computer', 'Needs reprogramming'])
add('P2615', 'Camshaft Position Signal Output Circuit Low', 'The camshaft signal the engine computer sends to other modules reads low.', 2, ['Wiring fault', 'Failing module'])

# --- Throttle and pedal (drive-by-wire) -----------------------------------------------------------------------------------
add('P2101', 'Throttle Actuator A Control Motor Circuit Range/Performance', 'The electronic throttle motor isn\'t responding correctly. The car may drop into reduced power.', 3, ['Dirty or failing throttle body', 'Wiring or connector fault'])
add('P2104', 'Throttle Actuator Control System - Forced Idle', 'The computer found a throttle problem and is holding the engine at idle for safety. The car may barely move.', 3, ['Failing throttle body', 'Pedal sensor fault', 'Wiring fault'])
add('P2106', 'Throttle Actuator Control System - Forced Limited Power', 'The computer found a throttle problem and put the car in limp mode with reduced power.', 3, ['Failing throttle body', 'Pedal or throttle sensor fault', 'Wiring fault'])
add('P2107', 'Throttle Actuator Control Module Processor', 'The throttle control processor found an internal fault.', 3, ['Failing engine computer', 'Throttle body fault'])
add('P2110', 'Throttle Actuator Control System - Forced Limited RPM', 'The computer is limiting engine speed because of a throttle fault.', 3, ['Failing throttle body', 'Sensor fault'])
add('P2111', 'Throttle Actuator Control System - Stuck Open', 'The electronic throttle is stuck more open than commanded. The car can go into limp mode or act unpredictably.', 3, ['Dirty or failing throttle body', 'Throttle motor fault', 'Software'])
add('P2112', 'Throttle Actuator Control System - Stuck Closed', 'The electronic throttle is stuck more closed than commanded, so the engine loses power and may go into limp mode.', 3, ['Dirty or failing throttle body', 'Throttle motor fault', 'Software'])
add('P2118', 'Throttle Actuator Control Motor Current Range/Performance', 'The throttle motor is drawing an unexpected current.', 3, ['Failing throttle body motor', 'Wiring fault'])
add('P2119', 'Throttle Actuator Control Throttle Body Range/Performance', 'The throttle isn\'t reaching the position it\'s commanded to.', 3, ['Dirty or sticking throttle body', 'Failing throttle motor'])
add('P2121', 'Throttle/Pedal Position Sensor/Switch D Circuit Range/Performance', 'One of the gas pedal position signals doesn\'t make sense.', 3, ['Failing accelerator pedal sensor', 'Wiring fault'])
add('P2122', 'Throttle/Pedal Position Sensor/Switch D Circuit Low', 'One of the gas pedal position signals reads too low, so the car may go into reduced power.', 3, ['Failing accelerator pedal sensor', 'Wiring fault'])
add('P2127', 'Throttle/Pedal Position Sensor/Switch E Circuit Low', 'The second gas pedal position signal reads too low.', 3, ['Failing accelerator pedal sensor', 'Wiring fault'])
add('P2128', 'Throttle/Pedal Position Sensor/Switch E Circuit High', 'The second gas pedal position signal reads too high.', 3, ['Failing accelerator pedal sensor', 'Wiring fault'])
add('P2135', 'Throttle/Pedal Position Sensor/Switch A/B Voltage Correlation', 'The two throttle position signals disagree, so the computer cuts power to stay safe.', 3, ['Failing throttle body sensor', 'Wiring or connector fault'])
add('P2138', 'Throttle/Pedal Position Sensor/Switch D/E Voltage Correlation', 'The two gas pedal position signals disagree, so the car may go into reduced power or not respond to the pedal.', 3, ['Failing accelerator pedal sensor', 'Wiring or connector fault', 'Throttle body fault'])
add('P2172', 'Throttle Actuator Control System - High Airflow Detected (Sudden)', 'The computer saw a sudden, unexpected jump in airflow.', 3, ['Throttle body fault', 'Vacuum leak'])
add('P2173', 'Throttle Actuator Control System - High Airflow Detected (Slow)', 'The computer saw airflow creeping higher than expected.', 3, ['Throttle body fault', 'Vacuum leak'])
add('P2176', 'Throttle Actuator Control System - Idle Position Not Learned', 'The computer hasn\'t learned the throttle\'s closed position, often after battery work or cleaning.', 2, ['Needs an idle relearn', 'Dirty throttle body'])

# --- Intake runners, cooling, misc engine -------------------------------------------------------------------------------
for code, b, st in [('P2004', 1, 'Stuck Open'), ('P2005', 2, 'Stuck Open'), ('P2006', 1, 'Stuck Closed'), ('P2007', 2, 'Stuck Closed')]:
    add(code, f'Intake Manifold Runner Control {st} (Bank {b})', f'The flaps inside the bank {b} intake manifold are {st.lower()}. Power and smoothness can suffer.', 1, ['Carbon buildup on the runner flaps', 'Failed runner actuator', 'Vacuum leak to the actuator'])
add('P200A', 'Intake Manifold Runner Control Performance (Bank 1)', 'The intake runner flaps aren\'t moving as commanded.', 1, ['Sticking runner flaps', 'Failed actuator'])
add('P2015', 'Intake Manifold Runner Position Sensor/Switch Circuit Range/Performance (Bank 1)', 'The intake runner position reading doesn\'t make sense.', 1, ['Broken runner linkage', 'Failed position sensor'])
add('P2181', 'Cooling System Performance', 'The engine isn\'t holding its normal temperature.', 2, ['Faulty thermostat', 'Low coolant', 'Faulty coolant temp sensor'])
add('P2263', 'Turbo/Super Charger Boost System Performance', 'The boost system isn\'t performing as expected.', 2, ['Boost leak', 'Wastegate problem', 'Faulty boost sensor'])
add('P228C', 'Fuel Pressure Regulator 1 Exceeded Control Limits - Pressure Too Low', 'The fuel pressure regulator can\'t keep pressure up. Stalling and power loss are common.', 3, ['Failing fuel pump or high-pressure pump', 'Faulty regulator', 'Fuel leak'])
add('P228D', 'Fuel Pressure Regulator 1 Exceeded Control Limits - Pressure Too High', 'The fuel pressure regulator can\'t keep pressure down.', 2, ['Faulty regulator', 'Faulty pressure sensor'])
add('P2293', 'Fuel Pressure Regulator 2 Performance', 'The second fuel pressure regulator isn\'t holding the right pressure.', 2, ['Faulty regulator', 'Fuel pump problem'])
add('P2600', 'Coolant Pump A Control Circuit/Open', 'The electric coolant pump circuit is open, so the engine can overheat.', 3, ['Failed electric coolant pump', 'Wiring fault'])
add('P2601', 'Coolant Pump A Control Circuit Range/Performance', 'The electric coolant pump isn\'t performing as commanded.', 3, ['Failing coolant pump', 'Wiring fault'])
add('P2609', 'Intake Air Heater System Performance', 'The intake air heater (used for cold starts) isn\'t performing as expected.', 1, ['Failed heater or relay'])
add('P2635', 'Fuel Pump A Low Flow/Performance', 'The fuel pump isn\'t delivering enough fuel. Hesitation and stalling can follow.', 3, ['Weak fuel pump', 'Clogged filter or strainer', 'Wiring or voltage problem'])
add('P2637', 'Torque Management Feedback Signal A', 'A torque signal between the engine and transmission computers is faulty.', 2, ['Wiring fault', 'Module fault'])
add('P2646', 'A Rocker Arm Actuator System Performance or Stuck Off (Bank 1)', 'The variable valve lift system on bank 1 isn\'t switching as commanded.', 2, ['Low or dirty oil', 'Failed rocker arm oil control solenoid'])
add('P3400', 'Cylinder Deactivation System (Bank 1)', 'The system that shuts off cylinders to save fuel has a fault on bank 1. The engine can run rough or misfire.', 2, ['Low or dirty oil', 'Failed deactivation solenoid', 'Collapsed lifter'])
add('P3497', 'Cylinder Deactivation System (Bank 2)', 'The system that shuts off cylinders to save fuel has a fault on bank 2.', 2, ['Low or dirty oil', 'Failed deactivation solenoid', 'Collapsed lifter'])

# --- Transmission ------------------------------------------------------------------------------------------------------------
add('P0700', 'Transmission Control System Malfunction', 'The transmission computer found its own problem and asked for the check engine light. Another transmission code with the details is usually stored too.', 2,
    ['A second transmission code that says what failed (the transmission computer has to be read for it)', 'Low or old transmission fluid', 'A shift solenoid or sensor fault'])
add('P0701', 'Transmission Control System Range/Performance', 'The transmission control system isn\'t performing as expected.', 2, ['Transmission computer fault', 'Low fluid'])
add('P0705', 'Transmission Range Sensor A Circuit (PRNDL Input)', 'The computer can\'t tell which gear the shifter is in. The car may not start, or may show the wrong gear.', 3, ['Failed range sensor', 'Misadjusted linkage', 'Wiring fault'])
add('P0706', 'Transmission Range Sensor A Circuit Range/Performance', 'The gear selector position signal doesn\'t make sense. Shifting and starting can act up.', 3, ['Failing range sensor', 'Misadjusted linkage'])
add('P0707', 'Transmission Range Sensor A Circuit Low', 'The gear selector position signal is too low.', 3, ['Failed range sensor', 'Wiring fault'])
add('P0711', 'Transmission Fluid Temperature Sensor A Circuit Range/Performance', 'The transmission fluid temperature reading doesn\'t make sense.', 2, ['Failing temp sensor', 'Low fluid', 'Wiring fault'])
add('P0713', 'Transmission Fluid Temperature Sensor A Circuit High', 'The transmission fluid temperature sensor reads as an open circuit.', 2, ['Failed sensor', 'Open wiring'])
add('P0715', 'Input/Turbine Speed Sensor A Circuit', 'The transmission lost its input speed signal, so shifting can become harsh or stuck in one gear.', 3, ['Failed input speed sensor', 'Wiring fault'])
add('P0716', 'Input/Turbine Speed Sensor A Circuit Range/Performance', 'The transmission\'s input speed signal is erratic.', 3, ['Failing input speed sensor', 'Wiring fault', 'Internal slipping'])
add('P0717', 'Input/Turbine Speed Sensor A Circuit No Signal', 'There\'s no input speed signal from the transmission.', 3, ['Failed input speed sensor', 'Open wiring'])
add('P0720', 'Output Speed Sensor Circuit', 'The transmission lost its output speed signal. The speedometer and shifting can act up.', 3, ['Failed output speed sensor', 'Wiring fault'])
add('P0721', 'Output Speed Sensor Circuit Range/Performance', 'The transmission\'s output speed signal is erratic.', 3, ['Failing output speed sensor', 'Wiring fault'])
add('P0722', 'Output Speed Sensor Circuit No Signal', 'There\'s no output speed signal from the transmission, so shifts and the speedometer can fail.', 3, ['Failed output speed sensor', 'Open wiring'])
add('P0725', 'Engine Speed Input Circuit', 'The transmission computer lost the engine speed signal.', 3, ['Crank sensor fault', 'Wiring fault'])
add('P0729', 'Gear 6 Incorrect Ratio', 'Sixth gear isn\'t matching the expected engine-to-wheel speed, so something is slipping.', 3, ['Low or burnt fluid', 'Worn clutches', 'Solenoid or valve body fault'])
add('P0730', 'Incorrect Gear Ratio', 'The transmission isn\'t matching the expected engine-to-wheel speed in some gear, which usually means slipping.', 3, ['Low or burnt fluid', 'Worn clutches or bands', 'Solenoid or valve body fault'])
for n, g in [(1, 'First'), (2, 'Second'), (3, 'Third'), (4, 'Fourth'), (5, 'Fifth')]:
    add(f'P073{n}', f'Gear {n} Incorrect Ratio', f'{g} gear isn\'t matching the expected engine-to-wheel speed, which usually means slipping in that gear.', 3, ['Low or burnt fluid', 'Worn clutches', 'Solenoid or valve body fault'])
add('P0736', 'Reverse Incorrect Ratio', 'Reverse isn\'t matching the expected speed, which usually means slipping in reverse.', 3, ['Low or burnt fluid', 'Worn reverse clutch', 'Valve body fault'])
add('P0740', 'Torque Converter Clutch Solenoid Circuit/Open', 'The torque converter lockup solenoid has an electrical fault. Fuel economy drops and the car may shudder.', 2, ['Failed TCC solenoid', 'Wiring fault'])
add('P0741', 'Torque Converter Clutch Solenoid Circuit Performance/Stuck Off', 'The torque converter isn\'t locking up as commanded. You may feel shudder or see higher RPM on the highway.', 2, ['Worn torque converter clutch', 'Failing TCC solenoid', 'Low or old fluid', 'Valve body wear'])
add('P0742', 'Torque Converter Clutch Solenoid Circuit Stuck On', 'The torque converter is staying locked when it shouldn\'t, which can stall the engine when you stop.', 3, ['Stuck TCC solenoid', 'Valve body fault'])
add('P0744', 'Torque Converter Clutch Solenoid Circuit Intermittent', 'The torque converter lockup control drops out now and then.', 2, ['Failing TCC solenoid', 'Loose connector'])
add('P0745', 'Pressure Control Solenoid A', 'The main transmission pressure solenoid has a fault. Shifts may be harsh or soft.', 3, ['Failed pressure control solenoid', 'Dirty fluid', 'Wiring fault'])
add('P0746', 'Pressure Control Solenoid A Performance/Stuck Off', 'The main transmission pressure solenoid isn\'t controlling pressure, so shifts can slip or flare.', 3, ['Failing pressure control solenoid', 'Dirty fluid', 'Valve body wear'])
add('P0747', 'Pressure Control Solenoid A Stuck On', 'The main transmission pressure solenoid is stuck on, so shifts can be harsh.', 3, ['Stuck pressure control solenoid', 'Dirty fluid'])
for code, sol, what in [('P0750', 'A', 'Malfunction'), ('P0751', 'A', 'Performance/Stuck Off'), ('P0752', 'A', 'Stuck On'), ('P0753', 'A', 'Electrical'),
                        ('P0755', 'B', 'Malfunction'), ('P0756', 'B', 'Performance/Stuck Off'), ('P0758', 'B', 'Electrical'),
                        ('P0760', 'C', 'Malfunction'), ('P0761', 'C', 'Performance/Stuck Off'), ('P0765', 'D', 'Malfunction'), ('P0766', 'D', 'Performance/Stuck Off'), ('P0770', 'E', 'Malfunction')]:
    add(code, f'Shift Solenoid {sol} {what}', f'Shift solenoid {sol} isn\'t working as commanded, so the transmission may skip gears, shift harshly or stay in one gear.', 3, [f'Failed shift solenoid {sol}', 'Dirty or low fluid', 'Wiring or valve body fault'])
add('P0775', 'Pressure Control Solenoid B', 'Transmission pressure solenoid B has a fault.', 3, ['Failed pressure control solenoid B', 'Dirty fluid', 'Wiring fault'])
add('P0776', 'Pressure Control Solenoid B Performance/Stuck Off', 'Transmission pressure solenoid B isn\'t controlling pressure, so shifts can slip, flare or bang.', 3, ['Failing pressure control solenoid B', 'Dirty or low fluid', 'Valve body wear'])
add('P0777', 'Pressure Control Solenoid B Stuck On', 'Transmission pressure solenoid B is stuck on.', 3, ['Stuck solenoid', 'Dirty fluid'])
add('P0780', 'Shift Error', 'A shift didn\'t happen the way the computer expected.', 3, ['Low or burnt fluid', 'Solenoid fault', 'Internal wear'])
add('P0785', 'Shift/Timing Solenoid', 'The shift timing solenoid has a fault.', 3, ['Failed solenoid', 'Wiring fault'])
add('P0796', 'Pressure Control Solenoid C Performance/Stuck Off', 'Transmission pressure solenoid C isn\'t controlling pressure.', 3, ['Failing solenoid C', 'Dirty fluid'])
add('P0805', 'Clutch Position Sensor Circuit', 'The clutch pedal position sensor has a fault.', 2, ['Failed clutch position sensor', 'Wiring fault'])
add('P0826', 'Up and Down Shift Switch Circuit', 'The manual shift (+/-) switch circuit has a fault.', 1, ['Failed shift switch', 'Wiring fault'])
add('P0840', 'Transmission Fluid Pressure Sensor/Switch A Circuit', 'A transmission fluid pressure switch has an electrical fault.', 3, ['Failed pressure switch', 'Wiring fault'])
add('P0841', 'Transmission Fluid Pressure Sensor/Switch A Circuit Range/Performance', 'A transmission fluid pressure reading doesn\'t match the gear the computer expects.', 3, ['Failing pressure switch', 'Low fluid', 'Valve body fault'])
add('P0843', 'Transmission Fluid Pressure Sensor/Switch A Circuit High', 'A transmission fluid pressure switch reads too high.', 3, ['Failed switch', 'Wiring fault'])
add('P0845', 'Transmission Fluid Pressure Sensor/Switch B Circuit', 'A second transmission fluid pressure switch has a fault.', 3, ['Failed switch', 'Wiring fault'])
add('P0846', 'Transmission Fluid Pressure Sensor/Switch B Circuit Range/Performance', 'A second transmission fluid pressure reading doesn\'t look right.', 3, ['Failing switch', 'Low fluid'])
add('P0850', 'Park/Neutral Switch Input Circuit', 'The park/neutral switch signal has a fault, so starting or idle control may act up.', 2, ['Failed switch', 'Misadjusted range sensor', 'Wiring fault'])
add('P0867', 'Transmission Fluid Pressure', 'Transmission fluid pressure isn\'t what the computer expects.', 3, ['Low fluid', 'Pump or valve body fault', 'Pressure sensor fault'])
add('P0868', 'Transmission Fluid Pressure Low', 'Transmission fluid pressure is too low, which can cause slipping or loss of drive.', 3, ['Low fluid or a leak', 'Weak pump', 'Pressure sensor fault'])
add('P0871', 'Transmission Fluid Pressure Sensor/Switch C Circuit Range/Performance', 'A third transmission fluid pressure reading doesn\'t look right.', 3, ['Failing switch', 'Low fluid'])
add('P0884', 'TCM Power Input Signal Intermittent', 'The transmission computer\'s power supply drops out now and then.', 3, ['Loose power or ground', 'Weak battery', 'Wiring fault'])
add('P0902', 'Clutch Actuator Circuit Low', 'The automated clutch actuator circuit reads too low.', 3, ['Failed clutch actuator', 'Wiring fault'])
add('P0929', 'Gear Shift Lock Solenoid/Actuator Control Circuit Range/Performance', 'The shift lock (the part that keeps the shifter in park until you press the brake) isn\'t working right.', 2, ['Failed shift lock solenoid', 'Brake switch fault'])
add('P0944', 'Hydraulic Pressure Unit Loss of Pressure', 'The transmission\'s hydraulic unit is losing pressure.', 3, ['Leak', 'Failing hydraulic pump'])
add('P0965', 'Pressure Control Solenoid B Control Circuit Range/Performance', 'The circuit for transmission pressure solenoid B isn\'t performing as expected.', 3, ['Failing solenoid B', 'Wiring fault'])
add('P0973', 'Shift Solenoid A Control Circuit Low', 'The circuit for shift solenoid A reads too low.', 3, ['Failed solenoid', 'Shorted wiring'])
add('P0975', 'Shift Solenoid B Control Circuit Open', 'The circuit for shift solenoid B is open.', 3, ['Failed solenoid', 'Open wiring'])
for code, el in [('P2700', 'A'), ('P2701', 'B'), ('P2702', 'C'), ('P2703', 'D'), ('P2704', 'E')]:
    add(code, f'Transmission Friction Element {el} Apply Time Range/Performance', f'Clutch pack {el} inside the transmission takes too long (or too little time) to engage, so shifts can slip or flare.', 3, ['Worn clutch pack', 'Low or old fluid', 'Valve body or solenoid fault', 'May need a transmission relearn'])
add('P2711', 'Unexpected Mechanical Gear Disengagement', 'The transmission dropped out of gear unexpectedly. The car can suddenly lose drive, which is a safety risk.', 3, ['Low fluid', 'Internal transmission failure', 'Solenoid or valve body fault'])
add('P2714', 'Pressure Control Solenoid D Performance/Stuck Off', 'Transmission pressure solenoid D isn\'t controlling pressure, so shifts can slip or bang.', 3, ['Failing solenoid D', 'Dirty fluid', 'Valve body wear'])
add('P2715', 'Pressure Control Solenoid D Stuck On', 'Transmission pressure solenoid D is stuck on.', 3, ['Stuck solenoid', 'Dirty fluid'])
add('P2716', 'Pressure Control Solenoid D Electrical', 'Transmission pressure solenoid D has an electrical fault.', 3, ['Failed solenoid D', 'Wiring fault'])
add('P2723', 'Pressure Control Solenoid E Performance/Stuck Off', 'Transmission pressure solenoid E isn\'t controlling pressure.', 3, ['Failing solenoid E', 'Dirty fluid'])
add('P2757', 'Torque Converter Clutch Pressure Control Solenoid Control Circuit Performance/Stuck Off', 'The torque converter clutch pressure control isn\'t working as commanded. Shudder is common.', 2, ['Failing TCC pressure solenoid', 'Worn converter clutch', 'Old fluid'])
add('P2764', 'Torque Converter Clutch Pressure Control Solenoid Control Circuit Low', 'The torque converter clutch pressure solenoid circuit reads too low.', 2, ['Failed solenoid', 'Wiring fault'])
add('P2797', 'Auxiliary Transmission Fluid Pump Performance', 'The extra transmission pump (used by start-stop systems) isn\'t performing.', 2, ['Failed auxiliary pump', 'Wiring fault'])

# --- Hybrid ---------------------------------------------------------------------------------------------------------------
add('P0A08', 'DC/DC Converter Status Circuit', 'The part that charges the 12-volt battery from the hybrid battery has a fault. The 12-volt battery can run down.', 3, ['Failed DC/DC converter', 'Wiring fault'])
add('P0A0A', 'High Voltage System Interlock Circuit', 'A high-voltage safety interlock is open, so the hybrid system may shut down.', 3, ['Loose high-voltage connector or cover', 'Wiring fault'])
add('P0A7F', 'Hybrid Battery Pack Deterioration', 'The hybrid battery is wearing out and storing less energy.', 2, ['Aged hybrid battery cells', 'Battery cooling fan clogged'])
add('P0A80', 'Replace Hybrid Battery Pack', 'The hybrid battery has weak cells and the computer says it needs replacing. Power and mileage drop.', 2, ['Aged hybrid battery cells', 'Battery cooling problems'])
add('P0A93', 'Inverter Cooling System Performance', 'The hybrid inverter isn\'t being cooled properly. The car can shut down to protect it.', 3, ['Failed inverter coolant pump', 'Low inverter coolant'])
add('P0A94', 'DC/DC Converter Performance', 'The hybrid system\'s voltage converter isn\'t performing as expected.', 3, ['Failing converter', 'Inverter fault'])
add('P0AA6', 'Hybrid Battery Voltage System Isolation Fault', 'High voltage is leaking somewhere it shouldn\'t. This is a safety fault: get it checked by a hybrid-trained shop.', 3, ['Damaged high-voltage cable or part', 'Coolant leak into high-voltage parts', 'Failed AC compressor (on some hybrids)'])

# --- Network (U) codes ----------------------------------------------------------------------------------------------------------
add('U0001', 'High Speed CAN Communication Bus', 'The main high-speed data network that the car\'s computers use to talk has a fault. Many warning lights can come on at once.', 3, ['Wiring or connector fault on the network', 'A failing module dragging the network down', 'Weak battery'])
add('U0002', 'High Speed CAN Communication Bus Performance', 'The main data network isn\'t performing as expected.', 3, ['Wiring fault', 'Failing module', 'Weak battery'])
add('U0073', 'Control Module Communication Bus A Off', 'A data network the car\'s computers share has gone quiet.', 3, ['Wiring fault', 'Failing module', 'Weak battery or poor ground'])
U_LOST = [('U0100', 'ECM/PCM "A"', 'the engine computer', 3), ('U0101', 'TCM', 'the transmission computer', 3), ('U0102', 'Transfer Case Control Module', 'the transfer case module', 2),
          ('U0103', 'Gear Shift Module', 'the gear shift module', 3), ('U0104', 'Cruise Control Module', 'the cruise control module', 2), ('U0109', 'Fuel Pump Control Module', 'the fuel pump control module', 3),
          ('U0111', 'Battery Energy Control Module "A"', 'the battery energy control module', 3), ('U0121', 'Anti-Lock Brake System (ABS) Control Module', 'the anti-lock brake (ABS) module', 3),
          ('U0122', 'Vehicle Dynamics Control Module', 'the stability control module', 3), ('U0126', 'Steering Angle Sensor Module', 'the steering angle sensor module', 3),
          ('U0129', 'Brake System Control Module', 'the brake system control module', 3), ('U0131', 'Power Steering Control Module', 'the power steering control module', 3),
          ('U0140', 'Body Control Module', 'the body control module', 2), ('U0141', 'Body Control Module "A"', 'body control module A', 2), ('U0146', 'Gateway "A"', 'the gateway module', 3),
          ('U0151', 'Restraints Control Module', 'the airbag (restraints) control module', 3), ('U0155', 'Instrument Panel Cluster (IPC) Control Module', 'the instrument cluster', 2),
          ('U0159', 'Parking Assist Control Module', 'the parking assist module', 1), ('U0164', 'HVAC Control Module', 'the climate control module', 1),
          ('U0170', 'Restraint System Sensor "A"', 'an airbag system sensor', 3), ('U0184', 'Radio', 'the radio', 1), ('U0212', 'Steering Column Control Module', 'the steering column module', 2),
          ('U0293', 'Hybrid Powertrain Control Module', 'the hybrid powertrain control module', 3)]
for code, title, mod, sev in U_LOST:
    add(code, f'Lost Communication With {title}', f'The other computers in the car stopped hearing from {mod}. Features that depend on it can stop working, and several warning lights often come on together.', sev,
        ['Wiring or connector fault on the data network', f'Power or ground problem at {mod}', f'Failed {mod.replace("the ", "")}', 'Weak battery'])
U_BAD = [('U0401', 'ECM/PCM "A"', 'the engine computer'), ('U0402', 'TCM', 'the transmission computer'), ('U0403', 'Transfer Case Control Module', 'the transfer case module'),
         ('U0404', 'Gear Shift Control Module "A"', 'the gear shift module'), ('U0415', 'Anti-Lock Brake System (ABS) Control Module', 'the anti-lock brake (ABS) module'),
         ('U0416', 'Vehicle Dynamics Control Module', 'the stability control module'), ('U0418', 'Brake System Control Module', 'the brake system control module'),
         ('U0420', 'Power Steering Control Module', 'the power steering control module'), ('U0422', 'Body Control Module', 'the body control module'),
         ('U0423', 'Instrument Panel Control Module', 'the instrument panel module'), ('U0428', 'Steering Angle Sensor Module', 'the steering angle sensor module'),
         ('U0452', 'Restraints Control Module', 'the airbag (restraints) control module')]
for code, title, mod in U_BAD:
    add(code, f'Invalid Data Received From {title}', f'Another computer in the car received data from {mod} that did not make sense.', 2,
        [f'A fault inside {mod}', 'Network wiring problem', 'Needs a software update', 'Weak battery'])

# --- Manufacturer-specific meanings, verified per make (11-10) -------------------------------------------------------------
MAKE = {
    'P1326': dict(makes=['Hyundai', 'Kia'], t='Knock Sensor Detection System (KSDS)', s=3,
                  m='On Hyundai and Kia engines, the knock sensor detection system picked up vibration that can point to wearing connecting rod bearings. The car may go into limp mode. Owners are usually told to see a dealer, because this system was added during the brands\' engine bearing campaigns.',
                  c=['Early connecting rod bearing wear', 'Faulty knock sensor or wiring', 'Software (KSDS update)']),
    'C1391': dict(makes=['Toyota', 'Lexus'], t='Abnormal Leak in Brake Accumulator', s=3,
                  m='On Toyota and Lexus models with a powered brake booster (mostly hybrids), the brake computer saw the stored brake pressure falling faster than it should, which points to an internal leak. Braking assist can be affected, so get it checked before driving much.',
                  c=['Internal leak in the brake booster/accumulator assembly', 'Leaking seals in the brake actuator']),
    'P1450': dict(makes=['Ford', 'Lincoln', 'Mercury'], t='Unable to Bleed Up Fuel Tank Vacuum', s=1,
                  m='On Fords, the fuel vapor (EVAP) system couldn\'t release vacuum from the gas tank. It\'s an emissions fault; the car usually drives normally.',
                  c=['Blocked EVAP vent valve or filter', 'Kinked EVAP hose', 'Faulty purge valve (some Ford bulletins replace it)']),
    'P1299': dict(makes=['Ford', 'Lincoln', 'Mercury'], t='Cylinder Head Overtemperature Protection Active', s=3,
                  m='On Fords, the engine got hot enough that the computer turned on its overheat protection, which can shut off cylinders and cut power. Pull over and let it cool.',
                  c=['Low coolant or a leak', 'Failed thermostat or water pump', 'Cooling fan problem', 'Faulty cylinder head temperature sensor']),
    'P1285': dict(makes=['Ford', 'Lincoln', 'Mercury'], t='Cylinder Head Overtemperature Sensed', s=3,
                  m='On Fords, the cylinder head temperature sensor saw the engine overheating. Stop and let it cool before driving on.',
                  c=['Low coolant or a leak', 'Failed thermostat or water pump', 'Cooling fan problem', 'Faulty head temperature sensor']),
    'P17F0': dict(makes=['Nissan', 'Infiniti'], t='CVT Judder (Transmission Inspection)', s=2,
                  m='On Nissans with a CVT, the transmission computer detected shudder (judder) while driving. Nissan service bulletins send this code to a transmission inspection, and some cars got a reprogram or a new CVT.',
                  c=['Internal CVT wear', 'CVT fluid condition', 'Software (Nissan bulletins)']),
    'P17F1': dict(makes=['Nissan', 'Infiniti'], t='CVT Judder (Control Valve Inspection)', s=2,
                  m='On Nissans with a CVT, the transmission computer detected judder. Nissan\'s repair steps for this code inspect the control valve (valve body) and the CVT\'s belt or chain.',
                  c=['Control valve (valve body) fault', 'Worn CVT belt or chain', 'Software (Nissan bulletins)']),
    'P1870': dict(makes=['Chevrolet', 'GMC', 'Buick', 'Cadillac', 'Pontiac', 'Oldsmobile', 'Saturn', 'Hummer'], t='Transmission Component Slipping', s=3,
                  m='On GM automatics like the 4L60-E, the computer saw slipping when the torque converter clutch was told to lock up, most often from wear in the torque converter clutch valves.',
                  c=['Worn TCC regulator or isolator valve bore', 'Failing TCC solenoid', 'Worn torque converter clutch', 'Old or burnt fluid']),
}

SEV = {1: ('Drive on, get it checked', 'You can usually keep driving. Have the code read at your next service or within a few weeks.'),
       2: ('Get it fixed soon', 'A few more days of normal driving is usually OK, but waiting can turn a small repair into a bigger one or a breakdown.'),
       3: ('Stop and fix now', 'Don\'t put it off. This can affect safety, stall the car or cause expensive damage.')}

# 11-10 (Elijah approved): "Stop and fix now" only for codes that are dangerous to drive on: overheating, low oil pressure,
# braking/ABS/stability, airbags, steering assist, high-voltage hybrid safety, and throttle stuck open (unintended acceleration).
# Every other former level-3 code becomes "fix soon" with a watch-for-symptoms warning (w=1).
STOP_KEEP = {'P0217', 'P0218', 'P0524', 'P06DD', 'P0556', 'P0A0A', 'P0AA6', 'P0A93', 'P2111', 'P2172', 'P2173',
             'U0121', 'U0122', 'U0129', 'U0131', 'U0151'}
SOFTENED = sorted(k for k, v in D.items() if v['s'] == 3 and k not in STOP_KEEP)
for k in SOFTENED: D[k]['s'] = 2; D[k]['w'] = 1
SEV_W = ('Fix soon', 'Book a shop visit this week. Stop driving if the car slips, shakes, overheats or warns you.')
def sev_text(v): return SEV_W if v.get('w') else SEV[v['s']]
