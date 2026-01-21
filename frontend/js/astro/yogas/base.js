/**
 * Base utilities and constants for all Yoga modules.
 * Re-exports centralized constants and provides helper methods.
 */

// Re-export everything from centralized constants module
import {
    SIGN_LORDS,
    EXALTATION,
    DEBILITATION,
    OWN_SIGNS,
    MOOLATRIKONA,
    COMBUSTION_ORBS,
    PLANETARY_ASPECTS,
    SAPTA_GRAHA,
    PANCHA_GRAHA,
    NAVAGRAHA,
    KENDRAS,
    TRIKONAS,
    DUSTHANAS,
    UPACHAYAS,
    PANAPARAS,
    APOKLIMAS,
    SIGN_ELEMENTS,
    SIGN_MODALITY,
    NATURAL_FRIENDS,
    NATURAL_ENEMIES,
    getDignity,
    getSignLord,
    isKendra,
    isTrikona,
    isDusthana,
    isNaturalBenefic,
    isNaturalMalefic
} from '../constants.js';

// Re-export with original names for backward compatibility
export const signLords = SIGN_LORDS;
export const exaltation = EXALTATION;
export const debilitation = DEBILITATION;
export const ownSigns = OWN_SIGNS;
export const moolatrikona = MOOLATRIKONA;
export const combustionOrbs = COMBUSTION_ORBS;
export const planetaryAspects = PLANETARY_ASPECTS;
export const sevenPlanets = SAPTA_GRAHA;
export const fiveNonLuminaries = PANCHA_GRAHA;
export const allPlanets = NAVAGRAHA;
export const kendras = KENDRAS;
export const trikonas = TRIKONAS;
export const dusthanas = DUSTHANAS;
export const upachayas = UPACHAYAS;
export const panaparas = PANAPARAS;
export const apoklimas = APOKLIMAS;
export const signElements = SIGN_ELEMENTS;
export const signModality = SIGN_MODALITY;
export const naturalFriends = NATURAL_FRIENDS;
export const naturalEnemies = NATURAL_ENEMIES;

/**
 * Base class for yoga modules providing common utility methods
 */
export class YogaModuleBase {
    constructor(ctx) {
        this.ctx = ctx;
    }

    // Get sign index for a planet
    getRasi(planet) {
        return this.ctx.getRasi(planet);
    }

    // Get house number from Lagna (or custom reference)
    getHouse(planet, ref = this.ctx.lagnaRasi) {
        return this.ctx.getHouse(planet, ref);
    }

    // Get degree within sign
    getDegree(planet) {
        return this.ctx.getDegree(planet);
    }

    // Get absolute longitude
    getLongitude(planet) {
        return this.ctx.getLongitude(planet);
    }

    // Check if planet is in specific houses
    inHouse(planet, houses, ref = this.ctx.lagnaRasi) {
        return this.ctx.inHouse(planet, houses, ref);
    }

    // Check conjunction
    isConjunct(p1, p2) {
        return this.ctx.isConjunct(p1, p2);
    }

    // Check aspect
    aspects(fromPlanet, toPlanet) {
        return this.ctx.aspects(fromPlanet, toPlanet);
    }

    // Check mutual aspect
    mutualAspect(p1, p2) {
        return this.ctx.mutualAspect(p1, p2);
    }

    // Check connection (conjunction or aspect)
    isConnected(p1, p2) {
        return this.ctx.isConnected(p1, p2);
    }

    // Get house lord
    getHouseLord(house, ref = this.ctx.lagnaRasi) {
        return this.ctx.getHouseLord(house, ref);
    }

    // Get sign lord
    getSignLord(sign) {
        return this.ctx.getSignLord(sign);
    }

    // Check if planet is retrograde
    isRetrograde(planet) {
        return this.ctx.isRetrograde(planet);
    }

    // Get dignity status
    getDignity(planet) {
        return this.ctx.getDignity(planet);
    }

    // Check combustion
    isCombust(planet) {
        return this.ctx.isCombust(planet);
    }

    // Get planets in a house
    getPlanetsInHouse(house, ref = this.ctx.lagnaRasi) {
        return this.ctx.getPlanetsInHouse(house, ref);
    }

    // Is Moon waxing (Shukla Paksha)
    isWaxingMoon() {
        return this.ctx.isWaxingMoon();
    }

    // Get natural benefics
    getNaturalBenefics() {
        return this.ctx.getNaturalBenefics();
    }

    // Get natural malefics
    getNaturalMalefics() {
        return this.ctx.getNaturalMalefics();
    }

    // Get shadbala strength
    getStrength(planets) {
        return this.ctx.getStrength(planets);
    }

    // Check if planet is strong via shadbala
    isStrong(planet) {
        return this.ctx.isStrong(planet);
    }

    // Add yoga to results
    addYoga(yoga) {
        this.ctx.addYoga(yoga);
    }

    // Abstract method - subclasses must override
    check() {
        throw new Error('check() method must be implemented by subclass');
    }
}

/**
 * Create a standard yoga object with all required fields
 * @param {Object} params - Yoga parameters
 * @returns {Object} Yoga object
 */
export function createYoga({
    name,
    nameKey,
    category,
    description,
    descriptionKey,
    planets = [],
    nature = 'Benefic',
    strength = 5,
    params = {}
}) {
    return {
        name,
        nameKey,
        category,
        description,
        descriptionKey,
        planets,
        nature,
        strength: parseFloat(strength.toFixed(2)),
        params
    };
}
