import { AYANAMSA_SYSTEMS } from "./constants.js";

class AstroEngine {
    constructor() {
        this.ayanamsaSystem = "Lahiri";
        this.nodeType = "Mean";
    }

    setAyanamsaSystem(system) {
        if (AYANAMSA_SYSTEMS[system]) {
            this.ayanamsaSystem = system;
        }
    }

    setNodeType(type) {
        this.nodeType = type === "True" ? "True" : "Mean";
    }

    calculatePlanets(date) {
        const bodies = ["Sun", "Moon", "Mercury", "Venus", "Mars", "Jupiter", "Saturn"];
        const results = {};
        const time = Astronomy.MakeTime(date);
        const dt = 1 / (24 * 60);
        const timeMinus = Astronomy.MakeTime(new Date(date.getTime() - 60000));
        const timePlus = Astronomy.MakeTime(new Date(date.getTime() + 60000));

        bodies.forEach((body) => {
            const vector = Astronomy.GeoVector(body, time, true);
            const state = Astronomy.Ecliptic(vector, time);

            const vectorMinus = Astronomy.GeoVector(body, timeMinus, true);
            const stateMinus = Astronomy.Ecliptic(vectorMinus, timeMinus);
            const vectorPlus = Astronomy.GeoVector(body, timePlus, true);
            const statePlus = Astronomy.Ecliptic(vectorPlus, timePlus);

            let diff = statePlus.elon - stateMinus.elon;
            if (diff < -180) diff += 360;
            if (diff > 180) diff -= 360;
            const speed = diff * 720;

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

        const nodes = this.calculateNodes(date, this.nodeType === "True");
        results["Rahu"] = nodes.rahu;
        results["Ketu"] = nodes.ketu;

        return results;
    }

    calculateNodes(date, useTrueNode = false) {
        const jd = this.dateToJulian(date);
        const T = (jd - 2451545.0) / 36525.0;

        let rahuLon;
        if (useTrueNode && typeof Astronomy.TrueNode === "function") {
            try {
                rahuLon = Astronomy.TrueNode(date);
            } catch {
                useTrueNode = false;
            }
        }

        if (!useTrueNode) {
            rahuLon = 125.044522
                - 1934.136261 * T
                + 0.0020708 * T * T
                + (T * T * T) / 450000.0;
            rahuLon = rahuLon % 360;
            if (rahuLon < 0) rahuLon += 360;
        }

        const ketuLon = (rahuLon + 180) % 360;
        const nodeSpeed = -0.05295;

        return {
            rahu: { elon: rahuLon, elat: 0, dist: 0, dec: 0, speed: nodeSpeed },
            ketu: { elon: ketuLon, elat: 0, dist: 0, dec: 0, speed: nodeSpeed }
        };
    }

    getAyanamsa(date, system = null) {
        const useSystem = system || this.ayanamsaSystem;
        const config = AYANAMSA_SYSTEMS[useSystem] || AYANAMSA_SYSTEMS.Lahiri;
        const jd = this.dateToJulian(date);
        const T = (jd - 2451545.0) / 36525.0;
        const [a0, a1, a2] = config.coefficients;
        return a0 + a1 * T + a2 * T * T;
    }

    getObliquity(date) {
        const jd = this.dateToJulian(date);
        const T = (jd - 2451545.0) / 36525.0;
        const eps0 = 84381.406;
        const eps = eps0
            - 46.836769 * T
            - 0.0001831 * T * T
            + 0.00200340 * T * T * T
            - 0.000000576 * T * T * T * T
            - 0.0000000434 * T * T * T * T * T;
        return eps / 3600;
    }

    calculateLagna(date, lat, lng) {
        const gmst = Astronomy.SiderealTime(date);
        const gmstDeg = gmst * 15;
        let lmst = gmstDeg + lng;
        if (lmst < 0) lmst += 360;
        if (lmst >= 360) lmst -= 360;

        const epsRad = this.getObliquity(date) * (Math.PI / 180);
        const ramcRad = lmst * (Math.PI / 180);
        const latRad = lat * (Math.PI / 180);

        const y = Math.cos(ramcRad);
        const x = -(Math.sin(ramcRad) * Math.cos(epsRad) + Math.tan(latRad) * Math.sin(epsRad));
        let asc = Math.atan2(y, x) * (180 / Math.PI);
        if (asc < 0) asc += 360;
        return asc;
    }

    calculateMC(date, lng) {
        const gmst = Astronomy.SiderealTime(date);
        const gmstDeg = gmst * 15;
        let lmst = gmstDeg + lng;
        if (lmst < 0) lmst += 360;
        if (lmst >= 360) lmst -= 360;

        const epsRad = this.getObliquity(date) * (Math.PI / 180);
        const ramcRad = lmst * (Math.PI / 180);
        const y = Math.sin(ramcRad);
        const x = Math.cos(ramcRad) * Math.cos(epsRad);
        let mc = Math.atan2(y, x) * (180 / Math.PI);
        if (mc < 0) mc += 360;
        return mc;
    }

    dateToJulian(date) {
        return (date.getTime() / 86400000) + 2440587.5;
    }
}

const engine = new AstroEngine();
export default engine;
