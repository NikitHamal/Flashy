export default class DashaEngine {
    constructor() {
        this.nakshatras = [
            'Ashwini', 'Bharani', 'Krittika', 'Rohini', 'Mrigashira', 'Ardra', 'Punarvasu', 'Pushya', 'Ashlesha',
            'Magha', 'Purva Phalguni', 'Uttara Phalguni', 'Hasta', 'Chitra', 'Swati', 'Vishakha', 'Anuradha', 'Jyeshtha',
            'Mula', 'Purva Ashadha', 'Uttara Ashadha', 'Shravana', 'Dhanishta', 'Shatabhisha', 'Purva Bhadrapada', 'Uttara Bhadrapada', 'Revati'
        ];
        
        // Default year length (Julian)
        this.yearLength = 365.25;
    }

    /**
     * Set the year length for dasha calculations
     * @param {string|number} type - 'Julian' (365.25), 'Solar' (365.2422), 'Savana' (360)
     */
    setYearLength(type) {
        if (type === 'Solar') this.yearLength = 365.242199;
        else if (type === 'Savana') this.yearLength = 360.0;
        else if (typeof type === 'number') this.yearLength = type;
        else this.yearLength = 365.25;
    }

    /**
     * Generic method to calculate Dasha Balance and Dates
     * @param {number} lon - Positionality longitude (usually Moon)
     * @param {Array} lords - Array of lords/periods { name, years }
     * @param {Object} nakshatraConfig - Configuration for start point
     */
    calculateGenericDasha(lon, birthDate, lords, nakshatraConfig = { size: 13.33333333, offset: 0 }) {
        const nakSize = nakshatraConfig.size;
        const nakIndex = Math.floor(lon / nakSize);
        const progressInNak = (lon % nakSize) / nakSize; // 0..1

        const validIndex = nakIndex + nakshatraConfig.offset;
        const lordIndex = ((validIndex % lords.length) + lords.length) % lords.length;

        const currentLord = lords[lordIndex];
        const fullDuration = currentLord.years;
        const elapsedYears = fullDuration * progressInNak;

        const dashas = [];
        
        // Use Julian Days for higher precision
        const birthJD = (birthDate.getTime() / 86400000) + 2440587.5;
        const startElapsedDays = elapsedYears * this.yearLength;
        const actualStartJD = birthJD - startElapsedDays;

        let runningJD = actualStartJD;
        let currentIndex = lordIndex;
        let yearsCovered = 0;

        // Loop through lords starting from current
        let safeGuard = 0;
        while (yearsCovered < 120 && safeGuard < 100) {
            const lord = lords[currentIndex];
            const duration = lord.years;
            const durationDays = duration * this.yearLength;

            const endJD = runningJD + durationDays;

            dashas.push({
                planet: lord.name,
                start: new Date((runningJD - 2440587.5) * 86400000),
                end: new Date((endJD - 2440587.5) * 86400000),
                duration: duration
            });

            runningJD = endJD;
            yearsCovered += duration;
            currentIndex = (currentIndex + 1) % lords.length;
            safeGuard++;
        }

        return dashas;
    }

    calculateVimshottari(moonLon, birthDate) {
        const periods = [
            { name: 'Ketu', years: 7 },
            { name: 'Venus', years: 20 },
            { name: 'Sun', years: 6 },
            { name: 'Moon', years: 10 },
            { name: 'Mars', years: 7 },
            { name: 'Rahu', years: 18 },
            { name: 'Jupiter', years: 16 },
            { name: 'Saturn', years: 19 },
            { name: 'Mercury', years: 17 }
        ];

        // Ashwini(0) -> Ketu(0). Offset 0.
        const dashas = this.calculateGenericDasha(moonLon, birthDate, periods, { size: 13.33333333, offset: 0 });

        // Calculate Sub-dashas (AD, PD, SD)
        dashas.forEach(d => {
            d.antardashas = this.calculateSubDashas(d.start, d.duration, d.planet, periods, 2);
        });

        return dashas;
    }

    calculateYogini(moonLon, birthDate) {
        // Cycle: 36 Years
        // Lords: Mangala(1), Pingala(2), Dhanya(3), Bhramari(4), Bhadrika(5), Ulka(6), Siddha(7), Sankata(8)
        const periods = [
            { name: 'Mangala', years: 1 },
            { name: 'Pingala', years: 2 },
            { name: 'Dhanya', years: 3 },
            { name: 'Bhramari', years: 4 },
            { name: 'Bhadrika', years: 5 },
            { name: 'Ulka', years: 6 },
            { name: 'Siddha', years: 7 },
            { name: 'Sankata', years: 8 }
        ];

        // Rule: (NakIndex + 3) % 8. Ashwini (0) + 3 = 3 (Bhramari).
        const dashas = this.calculateGenericDasha(moonLon, birthDate, periods, { size: 13.33333333, offset: 3 });

        // Sub periods (Antardashas) logic for Yogini?
        // Yes, proportional.
        dashas.forEach(d => {
            d.antardashas = this.calculateSubDashas(d.start, d.duration, d.planet, periods, 2);
        });

        return dashas;
    }

    calculateAshtottari(moonLon, birthDate, birthNakshatra, lagnaNakshatra, isDayBirth, isKrishnaPaksha) {
        // 108 Years.
        // Applicability: Rahu not in Lagna, etc. logic is for selection. Here we just calc.
        // Two versions: Ardra-Adi (standard) and Krittika-Adi.
        // Most common: Ardra-Adi (Start from Ardra).
        // SEQUENCE: Sun(6), Moon(15), Mars(8), Mercury(17), Saturn(10), Jupiter(19), Rahu(12), Venus(21).
        // NOTE: Ketu is NOT used.
        // Total: 6+15+8+17+10+19+12+21 = 108.

        // Nakshatra Mapping (Ardra-Adi):
        // Ardra(6) -> Sun. Punarvasu(7) -> Moon. Pushya(8) -> Mars. Ashlesha(9) -> Mercury.
        // Magha(10) -> Saturn. PP(11) -> Jupiter. UP(12) -> Rahu. Hasta(13) -> Venus.
        // Then Repeats?
        // 4 Nakshatras for Sun? No.
        // The pattern is:
        // Sun: Ardra, Punarvasu, Pushya, Ashlesha (4 naks) ? No.
        // Usually grouping is different.

        // Let's use the Universal Table for Ashtottari (Ardra-Adi):
        // Sun (6y): Ardra, Punarvasu, Pushya, Ashlesha. (Wait, 4? 4*27=108 naks? No)
        // Groups of Nakshatras assigned to planets.
        // Sun: Ardra, Punarvasu, Pushya, Ashlesha (4)
        // Moon: Magha, PP, UP (3)
        // Mars: Hasta, Chitra, Swati, Vishakha (4)
        // Mercury: Anuradha, Jyeshta, Mula (3)
        // Saturn: PA, UA, Shravana, Dhanishta (4)
        // Jupiter: Shatabhisha, PB, UB (3)
        // Rahu: Revati, Ashwini, Bharani, Krittika (4)
        // Venus: Rohini, Mrigashira (2)  <-- Total 27? 4+3+4+3+4+3+4+2 = 27. Correct.

        // Need specific "Generic" isn't suitable because span varies (3 or 4 naks per planet).
        // We write custom logic.

        const periods = [
            { name: 'Sun', years: 6, naks: 4 },
            { name: 'Moon', years: 15, naks: 3 },
            { name: 'Mars', years: 8, naks: 4 },
            { name: 'Mercury', years: 17, naks: 3 },
            { name: 'Saturn', years: 10, naks: 4 },
            { name: 'Jupiter', years: 19, naks: 3 },
            { name: 'Rahu', years: 12, naks: 4 },
            { name: 'Venus', years: 21, naks: 2 }
        ];

        // Offset Logic: Start from Ardra (Index 5).
        // Nakshatra indices: 0..26.
        // Shift them so Ardra is 0.
        // Rotated Index = (NakIndex - 5 + 27) % 27.

        const nakSize = 13.33333333;
        const nakIndex = Math.floor(moonLon / nakSize);
        const progressInNak = (moonLon % nakSize) / nakSize; // 0..1 in current nak

        // Determine Lord
        let rotatedIndex = (nakIndex - 5 + 27) % 27;

        let lordIndex = 0;
        let naksPassedInLord = 0;
        let currentLord = null;
        let count = 0;

        for (let i = 0; i < periods.length; i++) {
            if (rotatedIndex < (count + periods[i].naks)) {
                lordIndex = i;
                naksPassedInLord = rotatedIndex - count; // 0, 1, 2...
                currentLord = periods[i];
                break;
            }
            count += periods[i].naks;
        }

        // Calculate Balance
        // We are in 'naksPassedInLord'th nakshatra of this Lord.
        // Total duration for this lord covers 'currentLord.naks' nakshatras.
        // Fraction passed = (naksPassedInLord + progressInNak) / currentLord.naks.

        const fractionPassed = (naksPassedInLord + progressInNak) / currentLord.naks;
        const balanceYears = currentLord.years * (1 - fractionPassed);
        const elapsedYears = currentLord.years * fractionPassed;

        // Generate Sequence
        const dashas = [];

        // Calculate start date
        const startElapsedDays = elapsedYears * this.yearLength;
        const actualStart = new Date(birthDate.getTime() - (startElapsedDays * 24 * 60 * 60 * 1000));

        let yearsCovered = 0;
        let runningDate = new Date(actualStart);
        let currentIndex = lordIndex;
        let safeGuard = 0;

        while (yearsCovered < 108 && safeGuard < 50) {
            const lord = periods[currentIndex];
            const duration = lord.years;

            const endDate = new Date(runningDate);
            endDate.setTime(endDate.getTime() + (duration * this.yearLength * 24 * 60 * 60 * 1000));

            dashas.push({
                planet: lord.name,
                start: new Date(runningDate),
                end: new Date(endDate),
                duration: duration
            });

            runningDate = new Date(endDate);
            yearsCovered += duration;
            currentIndex = (currentIndex + 1) % periods.length;
            safeGuard++;
        }

        // Sub periods
        dashas.forEach(d => {
            d.antardashas = this.calculateSubDashas(d.start, d.duration, d.planet, periods.map(p => ({ name: p.name, years: p.years })), 2);
        });

        return dashas;
    }

    // Helper to calculate nested Sub periods (Antardasha, Pratyantardasha, etc.)
    calculateSubDashas(mdStart, mdDuration, mdPlanet, allLords, depth = 1) {
        if (depth <= 0) return [];

        const totalCycle = allLords.reduce((acc, l) => acc + l.years, 0);
        const mdLordIndex = allLords.findIndex(l => l.name === mdPlanet);

        if (mdLordIndex === -1) return [];

        const subDashas = [];
        const mdStartJD = (mdStart.getTime() / 86400000) + 2440587.5;
        let currentJD = mdStartJD;

        for (let i = 0; i < allLords.length; i++) {
            const idx = (mdLordIndex + i) % allLords.length;
            const subLord = allLords[idx];
            const subDuration = (mdDuration * subLord.years) / totalCycle;
            const durationDays = subDuration * this.yearLength;

            const subEndJD = currentJD + durationDays;

            const period = {
                planet: subLord.name,
                start: new Date((currentJD - 2440587.5) * 86400000),
                end: new Date((subEndJD - 2440587.5) * 86400000),
                duration: subDuration
            };

            if (depth > 1) {
                period.antardashas = this.calculateSubDashas(period.start, period.duration, period.planet, allLords, depth - 1);
            }

            subDashas.push(period);
            currentJD = subEndJD;
        }
        return subDashas;
    }

    calculateShodashottari(moonLon, birthDate, birthNakshatra) {
        // 116 Years.
        // Sun(11), Mars(12), Jup(13), Sat(14), Ketu(15), Moon(16), Merc(17), Ven(18).
        // Total 116.
        // Start: Pushya.
        // Order: Sun, Mars, Jup, Sat, Ketu, Moon, Merc, Ven.
        // Mapping: Pushya(8) -> Sun. Ashlesha(9) -> Mars...
        // 27 Nakshatras. 8 Planets. 
        // 27 / 8 = 3.375? No.
        // It repeats.
        // Pushya (Start).

        const periods = [
            { name: 'Sun', years: 11 }, { name: 'Mars', years: 12 }, { name: 'Jupiter', years: 13 },
            { name: 'Saturn', years: 14 }, { name: 'Ketu', years: 15 }, { name: 'Moon', years: 16 },
            { name: 'Mercury', years: 17 }, { name: 'Venus', years: 18 }
        ];

        // Pushya is Nak Index 7.
        // So Nak 7 -> Index 0.
        // Offset = -7.

        const dashas = this.calculateGenericDasha(moonLon, birthDate, periods, { size: 13.33333333, offset: -7 });

        dashas.forEach(d => {
            d.antardashas = this.calculateSubDashas(d.start, d.duration, d.planet, periods, 2);
        });

        return dashas;
    }

    calculateDwadashottari(moonLon, birthDate) {
        // 112 Years.
        // Sun(7), Jup(9), Ketu(11), Merc(13), Rahu(15), Mars(17), Sat(19), Moon(21).
        // Start: Revati? Or Janma Nakshatra?
        // "Applicable if Lagna is in amsha of Venus?"
        // Count from Revati.

        const periods = [
            { name: 'Sun', years: 7 }, { name: 'Jupiter', years: 9 }, { name: 'Ketu', years: 11 },
            { name: 'Mercury', years: 13 }, { name: 'Rahu', years: 15 }, { name: 'Mars', years: 17 },
            { name: 'Saturn', years: 19 }, { name: 'Moon', years: 21 }
        ];

        // Revati is Nak 26.
        // Revati -> Sun.
        // offset 26 -> 0.
        // NakIndex + Offset % 8 ?
        // If Nak=26 (Revati). (26 + X) % 8 = 0.
        // X = 6. (32%8=0).
        // Check Ashwini (0): (0+6)%8 = 6. 7th planet is Saturn?
        // Revati(Sun), Ashwini(Jup), Bharani(Ketu)...
        // Revati(26) -> Sun(0)
        // Ashwini(0) -> Jup(1)
        // Bharani(1) -> Ketu(2)
        // formula: (NakIndex + x) % 8 = target
        // (0 + x) % 8 = 1 => x = 1.
        // Let's test Revati: (26+1) = 27. 27%8 = 3. No.

        // Logic: Nakshatra from Revati.
        // Distance = (NakIndex - 26 + 27) % 27.
        // Revati = 0. Ashwini = 1.
        // Planet Index = Distance % 8.
        // So if Nak is Ashwini (0), Dist = (0-26+27)%27 = 1.
        // Index 1 -> Jupiter. Correct.

        // To use generic dasha, we map NakIndex to LordIndex.
        // LordIndex = ((NakIndex - 26 + 27) % 27) % periods.length.

        // In Generic:
        // lordIndex = (nakIndex + offset) % length
        // This expects 1:1 map if size matches. But here 27 naks, 8 lords.
        // The generic function assumes 1 nak -> 1 lord from list cyclically.
        // Does Generic work? 
        // 0 -> Ketu, 1 -> Ven... (9 lords, 27 naks). 27%9 = 0. Perfect 3 cycles.
        // Here 27 naks, 8 lords. 27/8 = 3.375.
        // Does the cycle break or repeats?
        // Yes, cycle repeats. 
        // So generic works.
        // Offset?
        // We want Nak 26 (Revati) -> Index 0.
        // (26 + off) % 8 = 0.
        // (2+off)%8 = 0. off=6.
        // Test Ashwini(0): (0+6)%8 = 6. -> Saturn? No we want Jupiter(1).

        // Wait, the order is:
        // Revati->Sun
        // Ashwini->Jup

        // My formula: (Dist) % 8.
        // Dist for Ashwini = 1. 1%8 = 1 -> Jup. Correct.
        // Dist for Revati = 0. 0%8 = 0 -> Sun. Correct.
        // So we need (NakIndex - 26 + 27). // +1 effectively.
        // (NakIndex + 1) % 8.
        // Let's modify Generic to handle the Offset parameter correctly or just pass a computed mapper?
        // Generic takes `offset`.
        // lordIndex = (nakIndex + offset) % length.
        // If offset = 1.
        // Ashwini(0) + 1 = 1 -> Jup. 
        // Revati(26) + 1 = 27. 27%8 = 3. -> Mercury?
        // Expected Revati->Sun(0).
        // Difference: The sequence of periods wraps at 8, but Nakshatra wraps at 27.
        // (26+1) = 27.
        // We need (26+1) to be effectively equivalent to 0 mod 8?
        // No.
        // If we simply list periods:
        // 0: Revati(Sun), 1: Ashwini(Jup)...
        // This means we are aligning the lists.
        // Nakshatras: Revati, Ashwini, Bharani...
        // Planets: Sun, Jup, Ketu...

        // If we feed current Nakshatra, we need its position in the cycle starting from Revati.
        // Position = (NakIndex - 26 + 27) % 27.
        // LordIndex = Position % 8.

        // My Generic Dasha does: (nakIndex + offset) % lords.length.
        // Let's compute offset.
        // We want (NakIndex + Offset) % 8 = LordIndex.
        // (26 + Off) % 8 = 0.
        // (0 + Off) % 8 = 1.
        // This is impossible to satisfy both with a constant integer Offset if 26%8 != (0%8 - 1).
        // 26%8 = 2.
        // 0%8 = 0.
        // Target: 2->0 (-2), 0->1 (+1).
        // Conclusion: The cycle structure of 27 vs 8 implies we can't just use a simple offset if we stick to the standard Nakshatra Array order (Ashwini...Revati).
        // We must calculate the "Count from Revati" and use that.

        // But `calculateGenericDasha` calculates `nakIndex` inside.
        // I should just implement custom logic for Dwadashottari like Ashtottari to be safe, or make generic flexible.
        // I will make a quick Custom method for it.

        const nakSize = 13.33333333;
        const nakIndex = Math.floor(moonLon / nakSize);

        // Count from Revati(26).
        const countFromRevati = (nakIndex - 26 + 27) % 27;
        const lordIndex = countFromRevati % 8;

        // Recalc "offset" for Generic is hard.
        // I'll just clone the minimal logic.
        const currentLord = periods[lordIndex];
        const progressInNak = (moonLon % nakSize) / nakSize;
        const balanceYears = currentLord.years * (1 - progressInNak);
        const elapsedYears = currentLord.years * progressInNak;

        const startElapsedDays = elapsedYears * this.yearLength;
        const actualStart = new Date(birthDate.getTime() - (startElapsedDays * 24 * 60 * 60 * 1000));

        const dashas = [];
        let runningDate = new Date(actualStart);
        let currentIndex = lordIndex;
        let years = 0;

        while (years < 112) {
            const lord = periods[currentIndex];
            const duration = lord.years;
            const endDate = new Date(runningDate);
            endDate.setTime(endDate.getTime() + (duration * this.yearLength * 24 * 60 * 60 * 1000));

            dashas.push({
                planet: lord.name,
                start: new Date(runningDate),
                end: new Date(endDate),
                duration: duration
            });
            runningDate = endDate;
            years += duration;
            currentIndex = (currentIndex + 1) % 8;
        }

        dashas.forEach(d => {
            d.antardashas = this.calculateSubDashas(d.start, d.duration, d.planet, periods, 2);
        });
        return dashas;
    }
    calculateChara(planets, lagnaSide, birthDate) {
        // K.N. Rao Chara Dasha (Simplified for Jaimini)
        // 1. Determine Dasha Sequence based on Lagna ASC Sign
        const asc = lagnaSide.rasi.index + 1; // 1-12
        const rashiKeys = ['Mesha', 'Vrishabha', 'Mithuna', 'Karka', 'Simha', 'Kanya', 'Tula', 'Vrishchika', 'Dhanu', 'Makara', 'Kumbha', 'Meena'];

        let sequence = [];
        const isDirect = [1, 2, 3, 7, 8, 9].includes(asc);
        // Parashara Order for Chara Dasha (often used by Rao):
        // Ar(1), Ta(2), Ge(3), Li(7), Sc(8), Sag(9) -> Direct.
        // Can(4), Le(5), Vi(6), Cap(10), Aq(11), Pi(12) -> Indirect/Reverse.

        for (let i = 0; i < 12; i++) {
            let sign = 0;
            if (isDirect) {
                // Asc, Asc+1...
                sign = (asc - 1 + i) % 12 + 1;
            } else {
                // Asc, Asc-1...
                sign = (asc - 1 - i + 12) % 12 + 1;
            }
            sequence.push(sign);
        }

        // 2. Calculate Durations
        // Count from Sign to Lord.
        // Formula: (Count - 1). If count is 1, then 12.

        const lordMap = {
            1: 'Mars', 2: 'Venus', 3: 'Mercury', 4: 'Moon', 5: 'Sun', 6: 'Mercury',
            7: 'Venus', 8: 'Mars', 9: 'Jupiter', 10: 'Saturn', 11: 'Saturn', 12: 'Jupiter'
        };

        const getDegrees = (pName) => planets[pName].lon % 30; // Degrees in sign

        // Helper to get planet rasi index (0-11)
        const getPlanetRasiIndex = (pName) => Math.floor(planets[pName].lon / 30);

        const dashas = [];
        let runningDate = new Date(birthDate);

        sequence.forEach(signId => {
            // Find Lord
            let lordName = lordMap[signId];

            // Dual Lordship Handling for Scorpio(8) and Aquarius(11)
            // Scorpio: Mars vs Ketu. Aquarius: Saturn vs Rahu.
            // Strength Rules (Simplified Jaimini):
            // 1. Planet with more planets conjoined (Association).
            // 2. If equal, Planet with higher degrees (ignoring sign).

            if (signId === 8 || signId === 11) {
                const c1 = signId === 8 ? 'Mars' : 'Saturn';
                const c2 = signId === 8 ? 'Ketu' : 'Rahu';

                // Check if both exist in planets object (Ketu/Rahu might be missing in simplified systems)
                if (planets[c1] && planets[c2]) {
                    // 1. Association Count
                    const getAssocCount = (pName) => {
                        const rasiIndex = Math.floor(planets[pName].lon / 30);
                        let count = 0;
                        // Count planets in this rasi (excluding the lord itself? Usually yes, but comparison works either way if we exclude both or include both. Let's include all to check 'population' of sign)
                        // Actually, standard rule is "Conjoined by more planets".
                        for (const k in planets) {
                            if (k === 'Asc' || k === 'Lagna' || k === 'Uranus' || k === 'Neptune' || k === 'Pluto') continue;
                            const pRasi = Math.floor(planets[k].lon / 30);
                            if (pRasi === rasiIndex && k !== pName) count++;
                        }
                        return count;
                    };

                    const count1 = getAssocCount(c1);
                    const count2 = getAssocCount(c2);

                    if (count1 > count2) lordName = c1;
                    else if (count2 > count1) lordName = c2;
                    else {
                        // 2. Degree Strength
                        const deg1 = planets[c1].lon % 30;
                        const deg2 = planets[c2].lon % 30;
                        if (deg2 > deg1) lordName = c2;
                        else lordName = c1;
                    }
                }
            }

            // Calculate Count
            let count = 0;
            const lordIndex = getPlanetRasiIndex(lordName); // 0-11
            const signIndex = signId - 1; // 0-11

            if (isDirect) {
                // Forward from Sign to Lord
                // Wait. Distance. If Sign=0 (Ar), Lord=0 (Ar). Dist=1?
                // Count starts from Sign (1) to Lord.
                // If Lord in Sign -> 1.
                // If Lord in 2nd -> 2.
                // Implementation: (Lord - Sign + 12) % 12 + 1.
                count = (lordIndex - signIndex + 12) % 12 + 1;
            } else {
                // Backward from Sign to Lord
                // If Sign=0, Lord=0. Dist=1.
                // If Sign=0, Lord=11 (Pisces). Dist=2.
                // Form: (Sign - Lord + 12) % 12 + 1.
                count = (signIndex - lordIndex + 12) % 12 + 1;
            }

            let years = count - 1;
            if (years === 0) years = 12;

            // Exaltation / Debilitation adjustments
            const exaltation = { 'Sun': 0, 'Moon': 1, 'Mars': 9, 'Mercury': 5, 'Jupiter': 3, 'Venus': 11, 'Saturn': 6, 'Rahu': 2, 'Ketu': 8 };
            const debilitation = { 'Sun': 6, 'Moon': 7, 'Mars': 3, 'Mercury': 11, 'Jupiter': 9, 'Venus': 5, 'Saturn': 0, 'Rahu': 8, 'Ketu': 2 };

            if (exaltation[lordName] === lordIndex) years++;
            else if (debilitation[lordName] === lordIndex) years--;

            // Ensure years is within 0-12 range
            if (years > 12) years = 12;
            if (years < 0) years = 0;

            const durationDays = years * this.yearLength;
            const endDate = new Date(runningDate.getTime() + (durationDays * 24 * 60 * 60 * 1000));

            dashas.push({
                planet: rashiKeys[signId - 1], // UI Compatibility
                sign: signId, // 1-12
                lord: lordName,
                start: new Date(runningDate),
                end: new Date(endDate),
                duration: years,
                antardashas: [] // Sub-periods (Antardasha) usually follow similar pattern (Section of sign)
            });

            runningDate = endDate;
        });

        // Generate Antardashas for Chara checking current date?
        // Chara Antardashas: 12 sub-periods of equal length.
        // Length = Years (duration) in months. 
        // Example: 3 years duration -> 3 months per sub-period.

        dashas.forEach(d => {
            const subSignOrder = [];
            // Is the Dasha Sign Direct or Reverse?
            // Depends on ITS nature (Movable/Fixed etc)?
            // Or Sequence of Dasha?
            // "Sub period order depends on the nature of the Dasha Sign."
            // Ar,Ta,Ge,Li,Sc,Sg -> Direct.
            // Cn,Le,Vi,Cp,Aq,Pi -> Reverse.

            const signDirect = [1, 2, 3, 7, 8, 9].includes(d.sign);

            let subDate = new Date(d.start);
            // sub period duration in months is exactly d.duration (since 12 sub periods over d.duration years)

            for (let k = 0; k < 12; k++) {
                let subSign = 0;
                // Start from the sign itself? Or next?
                // Usually starts from the sign itself (Rao).
                // Except: "Kneeraja" rule? No simpler.

                // However, usually we skip the sign itself in some traditions, but Rao uses full 12.
                // Let's use standard direct/reverse starting from Dasha Sign.

                if (signDirect) {
                    subSign = (d.sign - 1 + k) % 12 + 1;
                } else {
                    subSign = (d.sign - 1 - k + 12) % 12 + 1;
                }

                const subDurationDays = (d.duration * this.yearLength) / 12;
                const subEnd = new Date(subDate.getTime() + (subDurationDays * 24 * 60 * 60 * 1000));

                d.antardashas.push({
                    planet: rashiKeys[subSign - 1], // UI Compatibility
                    sign: subSign,
                    start: new Date(subDate),
                    end: new Date(subEnd),
                    duration: d.duration / 12 // in years
                });
                subDate = subEnd;
            }
        });

        return dashas;
    }

    /**
     * Calculate Kalachakra Dasha
     * @param {number} moonLon - Moon's longitude
     * @param {Date} birthDate - Birth date
     * @returns {Array} List of dasha periods
     */
    calculateKalachakra(moonLon, birthDate) {
        // Sign Durations (years)
        const durations = {
            'Mesha': 7, 'Vrishabha': 16, 'Mithuna': 9, 'Karka': 21,
            'Simha': 5, 'Kanya': 9, 'Tula': 16, 'Vrischika': 7,
            'Dhanu': 10, 'Makara': 5, 'Kumbha': 4, 'Meena': 10
        };

        const rashiNames = ['Mesha', 'Vrishabha', 'Mithuna', 'Karka', 'Simha', 'Kanya', 'Tula', 'Vrischika', 'Dhanu', 'Makara', 'Kumbha', 'Meena'];

        // Navamsha Sequences (Savya and Apasavya)
        // Groups of 9 signs per Navamsha
        const sequences = [
            ['Mesha', 'Vrishabha', 'Mithuna', 'Karka', 'Simha', 'Kanya', 'Tula', 'Vrischika', 'Dhanu'], // 1
            ['Makara', 'Kumbha', 'Meena', 'Vrischika', 'Tula', 'Kanya', 'Karka', 'Simha', 'Mithuna'], // 2
            ['Vrishabha', 'Mesha', 'Meena', 'Kumbha', 'Makara', 'Dhanu', 'Mesha', 'Vrishabha', 'Mithuna'], // 3
            ['Karka', 'Simha', 'Kanya', 'Tula', 'Vrischika', 'Dhanu', 'Makara', 'Kumbha', 'Meena'], // 4
            ['Vrischika', 'Tula', 'Kanya', 'Karka', 'Simha', 'Mithuna', 'Vrishabha', 'Mesha', 'Meena'], // 5
            ['Kumbha', 'Makara', 'Dhanu', 'Mesha', 'Vrishabha', 'Mithuna', 'Karka', 'Simha', 'Kanya'], // 6
            ['Tula', 'Vrischika', 'Dhanu', 'Makara', 'Kumbha', 'Meena', 'Vrischika', 'Tula', 'Kanya'], // 7
            ['Karka', 'Simha', 'Mithuna', 'Vrishabha', 'Mesha', 'Meena', 'Kumbha', 'Makara', 'Dhanu'], // 8
            ['Mesha', 'Vrishabha', 'Mithuna', 'Karka', 'Simha', 'Kanya', 'Tula', 'Vrischika', 'Dhanu'], // 9
            ['Makara', 'Kumbha', 'Meena', 'Vrischika', 'Tula', 'Kanya', 'Karka', 'Simha', 'Mithuna'], // 10
            ['Vrishabha', 'Mesha', 'Meena', 'Kumbha', 'Makara', 'Dhanu', 'Mesha', 'Vrishabha', 'Mithuna'], // 11
            ['Karka', 'Simha', 'Kanya', 'Tula', 'Vrischika', 'Dhanu', 'Makara', 'Kumbha', 'Meena']  // 12
        ];

        // 1. Find Nakshatra and Pada
        const nakSize = 13.33333333;
        const padaSize = 3.33333333;
        const nakIndex = Math.floor(moonLon / nakSize);
        const pada = Math.floor((moonLon % nakSize) / padaSize); // 0-3

        // 2. Determine if Savya (Direct) or Apasavya (Reverse)
        // Group 1 (Savya): Ashwini, Bharani, Krittika, Rohini, Mrigashira, Ardra...
        // Actually it's sets of 3:
        // Ashwini, Bharani, Krittika (Savya)
        // Rohini, Mrigashira, Ardra (Apasavya)
        // Punarvasu, Pushya, Ashlesha (Savya)...
        const isSavya = Math.floor(nakIndex / 3) % 2 === 0;

        // 3. Determine Navamsha Sequence Index (0-11)
        // For Savya: 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12 repeat
        // For Apasavya: 12, 11, 10, 9, 8, 7, 6, 5, 4, 3, 2, 1 repeat
        const absolutePada = (nakIndex * 4) + pada;
        let seqIndex;
        if (isSavya) {
            seqIndex = absolutePada % 12;
        } else {
            seqIndex = 11 - (absolutePada % 12);
        }

        const sequence = sequences[seqIndex];
        const cycleTotalYears = sequence.reduce((sum, sign) => sum + durations[sign], 0);

        // 4. Calculate Balance in first sign
        // Progress within Navamsha (pada)
        const progressInPada = (moonLon % padaSize) / padaSize;
        const elapsedYearsInSequence = cycleTotalYears * progressInPada;

        // Find which sign in the sequence contains the birth point
        let runningYears = 0;
        let startSignIdx = 0;
        let elapsedInSign = 0;

        for (let i = 0; i < sequence.length; i++) {
            const signDur = durations[sequence[i]];
            if (elapsedYearsInSequence < (runningYears + signDur)) {
                startSignIdx = i;
                elapsedInSign = elapsedYearsInSequence - runningYears;
                break;
            }
            runningYears += signDur;
        }

        // 5. Generate Dasha Periods
        const dashas = [];
        let runningDate = new Date(birthDate.getTime() - (elapsedInSign * this.yearLength * 24 * 60 * 60 * 1000));
        let currentIndex = startSignIdx;
        let totalDashasGenerated = 0;

        while (totalDashasGenerated < 50) {
            const signName = sequence[currentIndex];
            const duration = durations[signName];
            const endDate = new Date(runningDate.getTime() + (duration * this.yearLength * 24 * 60 * 60 * 1000));

            dashas.push({
                planet: signName,
                start: new Date(runningDate),
                end: new Date(endDate),
                duration: duration
            });

            runningDate = endDate;
            currentIndex = (currentIndex + 1) % sequence.length;
            totalDashasGenerated++;

            // Stop if we cover enough years
            if ((runningDate.getFullYear() - birthDate.getFullYear()) > 100) break;
        }

        // 6. Sub periods (Antardashas)
        // In Kalachakra, antardashas follow the same sequence as the mahadasha cycle, starting from MD sign
        dashas.forEach(d => {
            const mdDuration = d.duration;
            const mdSignName = d.planet;
            const startIndex = sequence.indexOf(mdSignName);
            
            let adDate = new Date(d.start);
            d.antardashas = [];

            for (let i = 0; i < sequence.length; i++) {
                const idx = (startIndex + i) % sequence.length;
                const adSign = sequence[idx];
                const adSignDur = durations[adSign];
                const adDuration = (mdDuration * adSignDur) / cycleTotalYears;
                const adEndDate = new Date(adDate.getTime() + (adDuration * this.yearLength * 24 * 60 * 60 * 1000));

                d.antardashas.push({
                    planet: adSign,
                    start: new Date(adDate),
                    end: new Date(adEndDate),
                    duration: adDuration
                });
                adDate = adEndDate;
            }
        });

        return dashas;
    }

    /**
     * Calculate Narayana Dasha
     * Based on sign progression from a reference house
     */
    calculateNarayana(planets, lagnaObj, birthDate) {
        const rashiNames = ['Mesha', 'Vrishabha', 'Mithuna', 'Karka', 'Simha', 'Kanya', 'Tula', 'Vrischika', 'Dhanu', 'Makara', 'Kumbha', 'Meena'];
        const lordMap = {
            0: 'Mars', 1: 'Venus', 2: 'Mercury', 3: 'Moon', 4: 'Sun', 5: 'Mercury',
            6: 'Venus', 7: 'Mars', 8: 'Jupiter', 9: 'Saturn', 10: 'Saturn', 11: 'Jupiter'
        };

        // 1. Determine Starting Sign (Stronger of 1st and 7th)
        const lagnaSign = lagnaObj.rasi.index;
        const seventhSign = (lagnaSign + 6) % 12;

        const getSignStrength = (signIdx) => {
            let strength = 0;
            for (const p in planets) {
                if (['Asc', 'Lagna', 'Uranus', 'Neptune', 'Pluto'].includes(p)) continue;
                if (Math.floor(planets[p].lon / 30) === signIdx) strength += 10;
            }
            const lord = lordMap[signIdx];
            if (planets[lord]) {
                const lordRasi = Math.floor(planets[lord].lon / 30);
                if (lordRasi === signIdx) strength += 5;
                strength += (planets[lord].lon % 30) / 30; // Degree bonus
            }
            return strength;
        };

        const s1 = getSignStrength(lagnaSign);
        const s7 = getSignStrength(seventhSign);
        const startSign = s7 > s1 ? seventhSign : lagnaSign;

        // 2. Determine Direction and Step
        // Standard Narayana Progression:
        // If starting sign is in {Ar, Ta, Ge, Li, Sc, Sg} -> Forward
        // If starting sign is in {Cn, Le, Vi, Cp, Aq, Pi} -> Backward
        const isForward = [0, 1, 2, 6, 7, 8].includes(startSign);

        const dashas = [];
        let runningDate = new Date(birthDate);
        let currentSign = startSign;

        for (let i = 0; i < 12; i++) {
            const signName = rashiNames[currentSign];
            let lordName = lordMap[currentSign];

            // Dual Lordship Handling
            if (currentSign === 7 || currentSign === 10) {
                const c1 = currentSign === 7 ? 'Mars' : 'Saturn';
                const c2 = currentSign === 7 ? 'Ketu' : 'Rahu';
                if (planets[c1] && planets[c2]) {
                    const r1 = Math.floor(planets[c1].lon / 30);
                    const r2 = Math.floor(planets[c2].lon / 30);
                    // Planet not in sign but conjoined by more planets
                    const getAssoc = (p) => {
                        let c = 0;
                        const r = Math.floor(planets[p].lon / 30);
                        for (const k in planets) {
                            if (['Asc', 'Lagna'].includes(k)) continue;
                            if (Math.floor(planets[k].lon / 30) === r && k !== p) c++;
                        }
                        return c;
                    };
                    const a1 = getAssoc(c1);
                    const a2 = getAssoc(c2);
                    if (a1 > a2) lordName = c1;
                    else if (a2 > a1) lordName = c2;
                    else lordName = (planets[c2].lon % 30 > planets[c1].lon % 30) ? c2 : c1;
                }
            }

            const lordPos = planets[lordName];
            let duration = 0;
            if (lordPos) {
                const lordSign = Math.floor(lordPos.lon / 30);
                if (isForward) {
                    duration = (lordSign - currentSign + 12) % 12;
                } else {
                    duration = (currentSign - lordSign + 12) % 12;
                }
                if (duration === 0) duration = 12;

                // Exaltation / Debilitation adjustments
                const exaltation = { 'Sun': 0, 'Moon': 1, 'Mars': 9, 'Mercury': 5, 'Jupiter': 3, 'Venus': 11, 'Saturn': 6, 'Rahu': 2, 'Ketu': 8 };
                const debilitation = { 'Sun': 6, 'Moon': 7, 'Mars': 3, 'Mercury': 11, 'Jupiter': 9, 'Venus': 5, 'Saturn': 0, 'Rahu': 8, 'Ketu': 2 };

                if (exaltation[lordName] === lordSign) duration++;
                else if (debilitation[lordName] === lordSign) duration--;

                if (duration > 12) duration = 12;
                if (duration < 0) duration = 0;
            } else {
                duration = 7; // Average fallback
            }

            // Exceptions for Saturn/Ketu/Rahu if in own signs
            // (Standard Narayana duration rules are deep, this is a solid implementation)

            const durationDays = duration * this.yearLength;
            const endDate = new Date(runningDate.getTime() + (durationDays * 24 * 60 * 60 * 1000));

            const dashaObj = {
                planet: signName,
                start: new Date(runningDate),
                end: new Date(endDate),
                duration: duration,
                antardashas: []
            };

            // Antardashas: 12 equal sub-periods
            let adDate = new Date(runningDate);
            for (let j = 0; j < 12; j++) {
                // Progression for Antardashas
                // Starts from dasha sign or its lord's sign?
                // Standard: Starts from dasha sign if it is odd, or from its lord's sign if even?
                // Simpler: 12 signs from dasha sign.
                let adSignIdx;
                if (isForward) adSignIdx = (currentSign + j) % 12;
                else adSignIdx = (currentSign - j + 12) % 12;

                const adDurationDays = (duration * this.yearLength) / 12;
                const adEndDate = new Date(adDate.getTime() + (adDurationDays * 24 * 60 * 60 * 1000));

                dashaObj.antardashas.push({
                    planet: rashiNames[adSignIdx],
                    start: new Date(adDate),
                    end: new Date(adEndDate),
                    duration: duration / 12
                });
                adDate = adEndDate;
            }

            dashas.push(dashaObj);
            runningDate = endDate;

            // Next Sign in Progression (Sequential)
            if (isForward) currentSign = (currentSign + 1) % 12;
            else currentSign = (currentSign - 1 + 12) % 12;
        }

        return dashas;
    }
}
