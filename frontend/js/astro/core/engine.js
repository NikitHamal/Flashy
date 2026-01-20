/**
 * ============================================================================
 * Astronomy Engine Wrapper
 * ============================================================================
 *
 * Provides precise astronomical calculations using the Astronomy Engine library
 * (NASA JPL DE405 ephemeris). This module wraps the library and adds:
 *
 * - Multiple Ayanamsa system support (Lahiri, Raman, KP, etc.)
 * - Proper obliquity calculation
 * - True and Mean node options
 * - Sunrise/Sunset/Moonrise calculations
 * - Planetary hora calculations
 *
 * @module engine
 * @version 2.0.0
 */

/* global Astronomy */

import { AYANAMSA_J2000, PRECESSION_RATE } from './constants.js';

/**
 * Ayanamsa calculation systems
 * Each system has different reference epoch and values
 */
const AYANAMSA_SYSTEMS = {
    /**
     * Lahiri (Chitrapaksha) Ayanamsa - Most widely used in India
     * Reference: Chitra star at 180° in sidereal Libra
     * Official Government of India Ephemeris standard
     */
    Lahiri: {
        j2000Value: 23.853056,
        // Polynomial coefficients for precise calculation
        // A = a0 + a1*T + a2*T² where T = Julian centuries from J2000
        coefficients: [23.853056, 1.396971, 0.000308]
    },

    /**
     * B.V. Raman Ayanamsa
     * Reference: Based on Surya Siddhanta with modern precession
     */
    Raman: {
        j2000Value: 22.460000,
        coefficients: [22.460000, 1.396971, 0.000308]
    },

    /**
     * Krishnamurti (KP) Ayanamsa
     * Used in Krishnamurti Paddhati system
     * Reference: Star Spica at 179° in sidereal Virgo
     */
    Krishnamurti: {
        j2000Value: 23.780000,
        coefficients: [23.780000, 1.396971, 0.000308]
    },

    /**
     * Fagan-Bradley Ayanamsa
     * Popular in Western sidereal astrology
     */
    FaganBradley: {
        j2000Value: 24.044000,
        coefficients: [24.044000, 1.396971, 0.000308]
    },

    /**
     * Yukteshwar Ayanamsa
     * Based on Sri Yukteshwar Giri's calculations
     */
    Yukteshwar: {
        j2000Value: 22.475000,
        coefficients: [22.475000, 1.396971, 0.000308]
    },

    /**
     * True Chitrapaksha (Spica at exactly 180°)
     * Some software like Jagannatha Hora uses this
     */
    TrueChitra: {
        j2000Value: 23.9762,
        coefficients: [23.9762, 1.396971, 0.000308]
    },

    /**
     * Pushya-paksha Ayanamsa
     * Reference: Pushya star at exactly 106°40' (3s 16°40')
     * Gaining popularity for its precision in timing events.
     */
    PushyaPaksha: {
        j2000Value: 24.116667,
        coefficients: [24.116667, 1.396971, 0.000308]
    }
};

class Engine {
    constructor() {
        // Validate Astronomy Engine is loaded
        if (typeof Astronomy === 'undefined') {
            console.error('Astronomy Engine not loaded! Calculations will fail.');
        }

        // Default Ayanamsa system
        this.ayanamsaSystem = 'Lahiri';
        this.nodeType = 'Mean';

        // Cache for expensive calculations
        this._cache = new Map();
        this._cacheMaxSize = 100;
    }

    /**
     * Set the Ayanamsa system to use
     * @param {string} system - One of: 'Lahiri', 'Raman', 'Krishnamurti', 'FaganBradley', 'Yukteshwar', 'TrueChitra'
     */
    setAyanamsaSystem(system) {
        if (AYANAMSA_SYSTEMS[system]) {
            this.ayanamsaSystem = system;
            this._cache.clear(); // Clear cache when system changes
        } else {
            console.warn(`Unknown Ayanamsa system: ${system}. Using Lahiri.`);
            this.ayanamsaSystem = 'Lahiri';
        }
    }

    /**
     * Set the Node type (Mean or True)
     * @param {string} type - 'Mean' or 'True'
     */
    setNodeType(type) {
        this.nodeType = type === 'True' ? 'True' : 'Mean';
    }

    /**
     * Get current Ayanamsa system
     * @returns {string}
     */
    getAyanamsaSystem() {
        return this.ayanamsaSystem;
    }

    /**
     * Get list of available Ayanamsa systems
     * @returns {string[]}
     */
    getAvailableAyanamsaSystems() {
        return Object.keys(AYANAMSA_SYSTEMS);
    }

    /**
     * Calculate planetary positions
     * @param {Date} date - Date/time for calculation
     * @returns {Object} Planetary positions with ecliptic coordinates
     */
    calculatePlanets(date) {
        const bodies = ['Sun', 'Moon', 'Mercury', 'Venus', 'Mars', 'Jupiter', 'Saturn'];
        const results = {};

        const time = Astronomy.MakeTime(date);
        
        // Use centered difference for velocity (1 minute interval)
        // This provides much higher precision for stationary/retrograde detection
        const dt = 1 / (24 * 60); // 1 minute in days
        const timeMinus = Astronomy.MakeTime(new Date(date.getTime() - 60000));
        const timePlus = Astronomy.MakeTime(new Date(date.getTime() + 60000));

        bodies.forEach(body => {
            const vector = Astronomy.GeoVector(body, time, true);
            const state = Astronomy.Ecliptic(vector, time);

            const vectorMinus = Astronomy.GeoVector(body, timeMinus, true);
            const stateMinus = Astronomy.Ecliptic(vectorMinus, timeMinus);
            
            const vectorPlus = Astronomy.GeoVector(body, timePlus, true);
            const statePlus = Astronomy.Ecliptic(vectorPlus, timePlus);

            // Centered difference velocity: (pos(t+dt) - pos(t-dt)) / (2*dt)
            let diff = statePlus.elon - stateMinus.elon;
            if (diff < -180) diff += 360;
            if (diff > 180) diff -= 360;
            
            // Convert to degrees per day (dt is 1/1440 days, so 2*dt is 1/720)
            const speed = diff * 720;

            // Get equatorial position (for declination)
            const observer = new Astronomy.Observer(0, 0, 0);
            const eq = Astronomy.Equator(body, time, observer, true, true);

            results[body] = {
                elon: state.elon,
                elat: state.elat,
                dist: state.dist,
                dec: eq.dec,
                ra: eq.ra,
                speed: speed
            };
        });

        // Calculate lunar nodes (Rahu/Ketu)
        const nodes = this.calculateNodes(date, this.nodeType === 'True');
        results['Rahu'] = nodes.rahu;
        results['Ketu'] = nodes.ketu;

        return results;
    }

    /**
     * Calculate lunar nodes (Rahu/Ketu)
     * @param {Date} date - Date for calculation
     * @param {boolean} useTrueNode - Use true node vs mean node
     * @returns {Object} Rahu and Ketu positions
     */
    calculateNodes(date, useTrueNode = false) {
        const jd = this.dateToJulian(date);
        const T = (jd - 2451545.0) / 36525.0;

        let rahuLon;

        if (useTrueNode && typeof Astronomy.TrueNode === 'function') {
            // Use true node if available in the library
            try {
                rahuLon = Astronomy.TrueNode(date);
            } catch {
                useTrueNode = false;
            }
        }

        if (!useTrueNode) {
            // Mean node calculation per Meeus Astronomical Algorithms
            // More accurate formula with higher order terms
            rahuLon = 125.044522
                - 1934.136261 * T
                + 0.0020708 * T * T
                + T * T * T / 450000.0;

            rahuLon = rahuLon % 360;
            if (rahuLon < 0) rahuLon += 360;
        }

        const ketuLon = (rahuLon + 180) % 360;

        // Mean daily motion of nodes (retrograde)
        const nodeSpeed = -0.05295;

        return {
            rahu: { elon: rahuLon, elat: 0, dist: 0, dec: 0, speed: nodeSpeed },
            ketu: { elon: ketuLon, elat: 0, dist: 0, dec: 0, speed: nodeSpeed }
        };
    }

    /**
     * Calculate Ayanamsa (precession correction)
     * @param {Date} date - Date for calculation
     * @param {string} system - Optional override for Ayanamsa system
     * @returns {number} Ayanamsa value in degrees
     */
    getAyanamsa(date, system = null) {
        const useSystem = system || this.ayanamsaSystem;
        const config = AYANAMSA_SYSTEMS[useSystem] || AYANAMSA_SYSTEMS.Lahiri;

        const jd = this.dateToJulian(date);
        const T = (jd - 2451545.0) / 36525.0; // Julian centuries from J2000

        // Apply polynomial formula
        const [a0, a1, a2] = config.coefficients;
        return a0 + (a1 * T) + (a2 * T * T);
    }

    /**
     * Calculate obliquity of the ecliptic
     * @param {Date} date - Date for calculation
     * @returns {number} Obliquity in degrees
     */
    getObliquity(date) {
        const jd = this.dateToJulian(date);
        const T = (jd - 2451545.0) / 36525.0;

        // IAU 2006 obliquity formula (high precision)
        // Reference: Capitaine et al., 2003
        const eps0 = 84381.406; // arcseconds at J2000

        // Polynomial terms (arcseconds)
        const eps = eps0
            - 46.836769 * T
            - 0.0001831 * T * T
            + 0.00200340 * T * T * T
            - 0.000000576 * T * T * T * T
            - 0.0000000434 * T * T * T * T * T;

        return eps / 3600; // Convert to degrees
    }

    /**
     * Calculate Ascendant (Lagna)
     * @param {Date} date - Date/time for calculation
     * @param {number} lat - Latitude in degrees
     * @param {number} lng - Longitude in degrees
     * @returns {number} Tropical ascendant longitude in degrees
     */
    calculateLagna(date, lat, lng) {
        // 1. Calculate Greenwich Mean Sidereal Time
        const gmst = Astronomy.SiderealTime(date);
        const gmstDeg = gmst * 15; // Convert hours to degrees

        // 2. Adjust for local longitude to get Local Sidereal Time
        let lmst = gmstDeg + lng;
        if (lmst < 0) lmst += 360;
        if (lmst >= 360) lmst -= 360;

        // 3. Get obliquity of ecliptic
        const eps = this.getObliquity(date);
        const epsRad = eps * (Math.PI / 180);

        // 4. Calculate Ascendant using standard formula
        // Standard Ascendant (Asc) formula:
        // tan(Asc) = cos(RAMC) / -(sin(RAMC)*cos(eps) + tan(lat)*sin(eps))
        const ramcRad = lmst * (Math.PI / 180);
        const latRad = lat * (Math.PI / 180);

        const y = Math.cos(ramcRad);
        const x = -(Math.sin(ramcRad) * Math.cos(epsRad) + Math.tan(latRad) * Math.sin(epsRad));

        let asc = Math.atan2(y, x) * (180 / Math.PI);
        if (asc < 0) asc += 360;

        return asc;
    }

    /**
     * Calculate Midheaven (MC)
     * @param {Date} date - Date/time for calculation
     * @param {number} lng - Longitude in degrees
     * @returns {number} Tropical MC longitude in degrees
     */
    calculateMC(date, lng) {
        const gmst = Astronomy.SiderealTime(date);
        const gmstDeg = gmst * 15;
        let lmst = gmstDeg + lng;
        if (lmst < 0) lmst += 360;
        if (lmst >= 360) lmst -= 360;

        const eps = this.getObliquity(date);
        const epsRad = eps * (Math.PI / 180);
        const ramcRad = lmst * (Math.PI / 180);

        // MC formula: tan(MC) = tan(RAMC) / cos(eps)
        const y = Math.sin(ramcRad);
        const x = Math.cos(ramcRad) * Math.cos(epsRad);

        let mc = Math.atan2(y, x) * (180 / Math.PI);
        if (mc < 0) mc += 360;

        return mc;
    }

    /**
     * Calculate sunrise and sunset times
     * @param {Date} date - Date for calculation
     * @param {number} lat - Latitude in degrees
     * @param {number} lng - Longitude in degrees
     * @returns {Object} Sunrise and sunset Date objects
     */
    getSunriseSunset(date, lat, lng) {
        const observer = new Astronomy.Observer(lat, lng, 0);

        // Search for sunrise (direction = +1) and sunset (direction = -1)
        const sunrise = Astronomy.SearchRiseSet('Sun', observer, 1, date, 1);
        const sunset = Astronomy.SearchRiseSet('Sun', observer, -1, date, 1);

        return {
            sunrise: sunrise ? sunrise.date : null,
            sunset: sunset ? sunset.date : null
        };
    }

    /**
     * Calculate previous sunrise (for Hora calculation)
     * @param {Date} date - Current date/time
     * @param {number} lat - Latitude
     * @param {number} lng - Longitude
     * @returns {Date} Previous sunrise time
     */
    getPreviousSunrise(date, lat, lng) {
        const observer = new Astronomy.Observer(lat, lng, 0);

        // Search backwards from current time
        const searchStart = new Date(date.getTime() - 24 * 60 * 60 * 1000);
        const sunrise = Astronomy.SearchRiseSet('Sun', observer, 1, searchStart, 1);

        if (sunrise && sunrise.date <= date) {
            return sunrise.date;
        }

        // Try further back
        const searchStart2 = new Date(date.getTime() - 48 * 60 * 60 * 1000);
        const sunrise2 = Astronomy.SearchRiseSet('Sun', observer, 1, searchStart2, 1);

        return sunrise2 ? sunrise2.date : null;
    }

    /**
     * Calculate planetary Hora (hour lord)
     * @param {Date} date - Current date/time
     * @param {number} lat - Latitude
     * @param {number} lng - Longitude
     * @returns {Object} Hora information
     */
    calculateHora(date, lat, lng) {
        const { sunrise, sunset } = this.getSunriseSunset(date, lat, lng);

        if (!sunrise || !sunset) {
            return { lord: null, horaNumber: null };
        }

        // Hora sequence starts from day lord, then follows Chaldean order
        const dayLords = ['Sun', 'Moon', 'Mars', 'Mercury', 'Jupiter', 'Venus', 'Saturn'];
        const chaldeanOrder = ['Saturn', 'Jupiter', 'Mars', 'Sun', 'Venus', 'Mercury', 'Moon'];

        const dayOfWeek = date.getDay();
        const dayLord = dayLords[dayOfWeek];

        // Find starting index in Chaldean order for this day's lord
        const startIdx = chaldeanOrder.indexOf(dayLord);

        // Calculate day and night hora durations
        const sunriseMs = sunrise.getTime();
        const sunsetMs = sunset.getTime();
        const currentMs = date.getTime();

        let horaNumber;
        let horaDuration;

        if (currentMs >= sunriseMs && currentMs < sunsetMs) {
            // Daytime
            const dayDuration = sunsetMs - sunriseMs;
            horaDuration = dayDuration / 12;
            horaNumber = Math.floor((currentMs - sunriseMs) / horaDuration);
        } else {
            // Nighttime
            const nextSunrise = new Date(sunriseMs + 24 * 60 * 60 * 1000);
            const nightDuration = nextSunrise.getTime() - sunsetMs;
            horaDuration = nightDuration / 12;

            if (currentMs >= sunsetMs) {
                horaNumber = 12 + Math.floor((currentMs - sunsetMs) / horaDuration);
            } else {
                // Before sunrise
                const prevSunset = new Date(sunsetMs - 24 * 60 * 60 * 1000);
                horaNumber = 12 + Math.floor((currentMs - prevSunset.getTime()) / horaDuration);
            }
        }

        // Calculate hora lord
        const lordIdx = (startIdx + horaNumber) % 7;
        const horaLord = chaldeanOrder[lordIdx];

        return {
            lord: horaLord,
            horaNumber: (horaNumber % 24) + 1,
            isDay: horaNumber < 12,
            sunrise,
            sunset
        };
    }

    /**
     * Calculate day/night duration ratios
     * @param {Date} date - Date for calculation
     * @param {number} lat - Latitude
     * @param {number} lng - Longitude
     * @returns {Object} Day/night duration info
     */
    getDayNightDuration(date, lat, lng) {
        const { sunrise, sunset } = this.getSunriseSunset(date, lat, lng);

        if (!sunrise || !sunset) {
            return { dayDuration: 12 * 60, nightDuration: 12 * 60, isDaytime: true };
        }

        const sunriseMs = sunrise.getTime();
        const sunsetMs = sunset.getTime();
        const currentMs = date.getTime();

        // Get next sunrise for night duration
        const nextSunrise = this.getPreviousSunrise(
            new Date(sunsetMs + 24 * 60 * 60 * 1000), lat, lng
        );
        const nextSunriseMs = nextSunrise ?
            nextSunrise.getTime() + 24 * 60 * 60 * 1000 :
            sunriseMs + 24 * 60 * 60 * 1000;

        const dayDuration = (sunsetMs - sunriseMs) / 60000; // minutes
        const nightDuration = (nextSunriseMs - sunsetMs) / 60000; // minutes
        const isDaytime = currentMs >= sunriseMs && currentMs < sunsetMs;

        return {
            dayDuration: Math.round(dayDuration),
            nightDuration: Math.round(nightDuration),
            isDaytime,
            sunrise,
            sunset,
            dayHoraDuration: dayDuration / 12,    // Duration of one day hora in minutes
            nightHoraDuration: nightDuration / 12  // Duration of one night hora in minutes
        };
    }

    /**
     * Convert JavaScript Date to Julian Day Number
     * @param {Date} date - Date object
     * @returns {number} Julian Day Number
     */
    dateToJulian(date) {
        return (date.getTime() / 86400000) + 2440587.5;
    }

    /**
     * Calculate Ahargana (Days elapsed since Kali Yuga Epoch)
     * Epoch: Feb 18, 3102 BCE (Julian) = Julian Day 588465.5
     * @param {Date} date - Date for calculation
     * @returns {number} Days elapsed
     */
    getAhargana(date) {
        const jd = this.dateToJulian(date);
        const KALI_YUGA_EPOCH_JD = 588465.5;
        return jd - KALI_YUGA_EPOCH_JD;
    }

    /**
     * Convert Julian Day Number to JavaScript Date
     * @param {number} jd - Julian Day Number
     * @returns {Date} Date object
     */
    julianToDate(jd) {
        return new Date((jd - 2440587.5) * 86400000);
    }

    /**
     * Calculate angular separation between two longitudes
     * @param {number} lon1 - First longitude (degrees)
     * @param {number} lon2 - Second longitude (degrees)
     * @returns {number} Angular separation (0-180 degrees)
     */
    getAngularSeparation(lon1, lon2) {
        let diff = Math.abs(lon1 - lon2);
        if (diff > 180) diff = 360 - diff;
        return diff;
    }

    /**
     * Calculate next/previous Retrogression/Stationary events
     * @param {string} body - Planet name
     * @param {Date} date - Reference date
     * @returns {Object} Event details
     */
    getRetrogressionEvent(body, date) {
        if (['Sun', 'Moon'].includes(body)) return null;

        const time = Astronomy.MakeTime(date);
        
        // Search for the moment when velocity becomes zero
        // We use a simple iterative approach to find the root of speed(t) = 0
        const findZeroSpeed = (startJd, direction = 1) => {
            let jd = startJd;
            let step = 1.0 * direction; // 1 day steps initially
            let prevSpeed = this._getSpeedAtJd(body, jd);
            
            // 1. Find an interval where speed changes sign
            for (let i = 0; i < 500; i++) { // Max ~1.5 years search
                jd += step;
                let speed = this._getSpeedAtJd(body, jd);
                if (speed * prevSpeed < 0) {
                    // Sign change! Zero is between jd-step and jd
                    return this._refineZeroSpeed(body, jd - step, jd);
                }
                prevSpeed = speed;
            }
            return null;
        };

        const nextJd = findZeroSpeed(time.jd, 1);
        const prevJd = findZeroSpeed(time.jd, -1);

        return {
            next: nextJd ? { date: this.julianToDate(nextJd), speed: this._getSpeedAtJd(body, nextJd + 0.01) > 0 ? 'Direct' : 'Retrograde' } : null,
            prev: prevJd ? { date: this.julianToDate(prevJd), speed: this._getSpeedAtJd(body, prevJd + 0.01) > 0 ? 'Direct' : 'Retrograde' } : null
        };
    }

    _getSpeedAtJd(body, jd) {
        const t = Astronomy.MakeTime(jd);
        const dt = 1 / 1440; // 1 minute
        const t1 = Astronomy.MakeTime(jd - dt);
        const t2 = Astronomy.MakeTime(jd + dt);
        
        const pos1 = Astronomy.Ecliptic(Astronomy.GeoVector(body, t1, true), t1).elon;
        const pos2 = Astronomy.Ecliptic(Astronomy.GeoVector(body, t2, true), t2).elon;
        
        let diff = pos2 - pos1;
        if (diff < -180) diff += 360;
        if (diff > 180) diff -= 360;
        
        return diff * 720;
    }

    _refineZeroSpeed(body, jd1, jd2) {
        // Binary search to refine the zero crossing
        let low = jd1;
        let high = jd2;
        for (let i = 0; i < 20; i++) { // ~0.1 second precision
            let mid = (low + high) / 2;
            let speed = this._getSpeedAtJd(body, mid);
            let speedLow = this._getSpeedAtJd(body, low);
            
            if (speed * speedLow < 0) high = mid;
            else low = mid;
        }
        return (low + high) / 2;
    }

    /**
     * Calculate Heliacal Rising/Setting (Udaya/Asta)
     * Per Surya Siddhanta Kalanshas
     */
    getHeliacalStatus(body, date, sunLon) {
        if (body === 'Sun') return { isVisible: true };
        
        const Kalanshas = {
            Moon: 12,
            Mars: 17,
            Mercury: 14,
            MercuryRetro: 12,
            Jupiter: 11,
            Venus: 10,
            VenusRetro: 8,
            Saturn: 15
        };

        const t = Astronomy.MakeTime(date);
        const pLon = Astronomy.Ecliptic(Astronomy.GeoVector(body, t, true), t).elon;
        const speed = this._getSpeedAtJd(body, t.jd);
        
        let diff = Math.abs(pLon - sunLon);
        if (diff > 180) diff = 360 - diff;

        const isRetro = speed < 0;
        let limit = Kalanshas[body] || 15;
        if (isRetro && Kalanshas[body + 'Retro']) limit = Kalanshas[body + 'Retro'];

        return {
            isVisible: diff > limit,
            distanceFromSun: diff,
            limit: limit
        };
    }

    /**
     * Clear calculation cache
     */
    clearCache() {
        this._cache.clear();
    }
}

export default new Engine();
