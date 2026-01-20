/**
 * Spiritual/Moksha Yogas Module
 * Implements yogas related to spiritual growth and liberation
 */

import { YogaModuleBase, createYoga, kendras, trikonas, dusthanas } from './base.js';

export class SpiritualYogas extends YogaModuleBase {
    check() {
        this._checkMokshaYoga();
        this._checkPravrityaYoga();
        this._checkDhyanaYoga();
        this._checkYogakarakaYoga();
        this._checkAdhyatmikaYoga();
        this._checkSiddhiYoga();
        this._checkGuruBhaktiYoga();
        this._checkJnanaYoga();
    }

    /**
     * Moksha Yoga (Liberation)
     * 12th house/lord combinations with Jupiter/Ketu
     */
    _checkMokshaYoga() {
        const lord12 = this.getHouseLord(12);
        const lord12House = this.getHouse(lord12);
        const planetsIn12 = this.getPlanetsInHouse(12);

        // Ketu in 12th (natural moksha karaka in moksha house)
        if (planetsIn12.includes('Ketu')) {
            this.addYoga(createYoga({
                name: 'Moksha Yoga (Ketu)',
                nameKey: 'Moksha_Ketu',
                category: 'Spiritual',
                description: 'Ketu in 12th house. Strong spiritual liberation potential - detachment, meditation, past-life spiritual progress.',
                descriptionKey: 'Moksha_Ketu',
                planets: ['Ketu'],
                nature: 'Benefic',
                strength: 8
            }));
        }

        // Jupiter in 12th (guru in moksha house)
        if (planetsIn12.includes('Jupiter') && !this.isCombust('Jupiter')) {
            this.addYoga(createYoga({
                name: 'Moksha Yoga (Jupiter)',
                nameKey: 'Moksha_Jupiter',
                category: 'Spiritual',
                description: 'Jupiter in 12th house. Spiritual wisdom, divine grace, meditation, temple visits, moksha through knowledge.',
                descriptionKey: 'Moksha_Jupiter',
                planets: ['Jupiter'],
                nature: 'Benefic',
                strength: 7
            }));
        }

        // 12th lord in 9th (moksha through dharma)
        if (lord12House === 9) {
            this.addYoga(createYoga({
                name: 'Moksha Yoga (Dharma)',
                nameKey: 'Moksha_Dharma',
                category: 'Spiritual',
                description: '12th lord in 9th house. Liberation through righteous living, spiritual teachers, pilgrimage.',
                descriptionKey: 'Moksha_Dharma',
                planets: [lord12],
                nature: 'Benefic',
                strength: 7
            }));
        }

        // Jupiter-Ketu conjunction in 9th or 12th
        if (this.isConjunct('Jupiter', 'Ketu')) {
            const jupHouse = this.getHouse('Jupiter');
            if ([9, 12].includes(jupHouse)) {
                this.addYoga(createYoga({
                    name: 'Moksha Yoga (Guru-Ketu)',
                    nameKey: 'Moksha_Guru_Ketu',
                    category: 'Spiritual',
                    description: 'Jupiter-Ketu conjunction in spiritual house. Highest spiritual yoga - wisdom without attachment, liberation.',
                    descriptionKey: 'Moksha_Guru_Ketu',
                    planets: ['Jupiter', 'Ketu'],
                    nature: 'Benefic',
                    strength: 9
                }));
            }
        }
    }

    /**
     * Pravritya Yoga (Active spirituality)
     * 9th and 10th connection with Jupiter
     */
    _checkPravrityaYoga() {
        const lord9 = this.getHouseLord(9);
        const lord10 = this.getHouseLord(10);

        const connected = this.isConnected(lord9, lord10);
        const jupConnected = this.isConnected('Jupiter', lord9) || this.isConnected('Jupiter', lord10);

        if (connected && jupConnected) {
            this.addYoga(createYoga({
                name: 'Pravritya Yoga',
                nameKey: 'Pravritya',
                category: 'Spiritual',
                description: '9th-10th lords connected with Jupiter. Active spirituality - spreading dharma through work, teaching, public service.',
                descriptionKey: 'Pravritya',
                planets: [lord9, lord10, 'Jupiter'],
                nature: 'Benefic',
                strength: 7
            }));
        }
    }

    /**
     * Dhyana Yoga (Meditation)
     * Moon-Ketu or Saturn-Ketu connections with 8th/12th
     */
    _checkDhyanaYoga() {
        const moonKetuConj = this.isConjunct('Moon', 'Ketu');
        const ketuHouse = this.getHouse('Ketu');
        const moonHouse = this.getHouse('Moon');

        // Moon-Ketu in meditation houses
        if (moonKetuConj && [4, 8, 12].includes(moonHouse)) {
            this.addYoga(createYoga({
                name: 'Dhyana Yoga (Moon-Ketu)',
                nameKey: 'Dhyana_Moon_Ketu',
                category: 'Spiritual',
                description: 'Moon-Ketu conjunction in meditation house. Deep meditation ability, intuitive insights, past-life spiritual experiences.',
                descriptionKey: 'Dhyana_Moon_Ketu',
                planets: ['Moon', 'Ketu'],
                nature: 'Benefic',
                strength: 7
            }));
        }

        // Saturn in 12th aspecting Moon
        const saturnIn12 = this.getHouse('Saturn') === 12;
        const saturnAspectsMoon = this.aspects('Saturn', 'Moon');
        if (saturnIn12 && saturnAspectsMoon) {
            this.addYoga(createYoga({
                name: 'Dhyana Yoga (Saturn)',
                nameKey: 'Dhyana_Saturn',
                category: 'Spiritual',
                description: 'Saturn in 12th aspecting Moon. Disciplined meditation, solitude, deep contemplation, renunciation tendency.',
                descriptionKey: 'Dhyana_Saturn',
                planets: ['Saturn', 'Moon'],
                nature: 'Neutral',
                strength: 6
            }));
        }

        // Ketu in 4th (inner peace)
        if (ketuHouse === 4) {
            const beneficAspects = this.getNaturalBenefics().some(b =>
                this._aspectsHouse(b, this.getHouse(b), 4)
            );
            if (beneficAspects) {
                this.addYoga(createYoga({
                    name: 'Dhyana Yoga (Heart)',
                    nameKey: 'Dhyana_Heart',
                    category: 'Spiritual',
                    description: 'Ketu in 4th with benefic aspect. Heart-centered meditation, inner peace, contentment.',
                    descriptionKey: 'Dhyana_Heart',
                    planets: ['Ketu'],
                    nature: 'Benefic',
                    strength: 6
                }));
            }
        }
    }

    /**
     * Helper to check house aspect
     */
    _aspectsHouse(planet, planetHouse, targetHouse) {
        const aspects = {
            'Sun': [7], 'Moon': [7], 'Mercury': [7], 'Venus': [7],
            'Mars': [4, 7, 8], 'Jupiter': [5, 7, 9], 'Saturn': [3, 7, 10],
            'Rahu': [5, 7, 9], 'Ketu': [5, 7, 9]
        };

        const planetAspects = aspects[planet] || [7];
        for (const asp of planetAspects) {
            if (((planetHouse - 1 + asp) % 12) + 1 === targetHouse) return true;
        }
        return false;
    }

    /**
     * Yogakaraka Yoga (Spiritual catalyst)
     * Saturn or Mars in 4th/5th/9th/10th for specific Lagnas
     */
    _checkYogakarakaYoga() {
        const lagnaSign = this.ctx.lagnaRasi;

        // Saturn is Yogakaraka for Taurus and Libra Lagna
        if ([1, 6].includes(lagnaSign)) { // Taurus(1) and Libra(6)
            const satHouse = this.getHouse('Saturn');
            if ([4, 5, 9, 10].includes(satHouse)) {
                this.addYoga(createYoga({
                    name: 'Yogakaraka Saturn',
                    nameKey: 'Yogakaraka_Saturn',
                    category: 'Spiritual',
                    description: `Saturn as Yogakaraka in ${satHouse}th for ${lagnaSign === 1 ? 'Taurus' : 'Libra'} Lagna. Exceptional spiritual and material progress through discipline.`,
                    descriptionKey: 'Yogakaraka_Saturn',
                    planets: ['Saturn'],
                    nature: 'Benefic',
                    strength: 8
                }));
            }
        }

        // Mars is Yogakaraka for Cancer and Leo Lagna
        if ([3, 4].includes(lagnaSign)) { // Cancer(3) and Leo(4)
            const marsHouse = this.getHouse('Mars');
            if ([4, 5, 9, 10].includes(marsHouse)) {
                this.addYoga(createYoga({
                    name: 'Yogakaraka Mars',
                    nameKey: 'Yogakaraka_Mars',
                    category: 'Spiritual',
                    description: `Mars as Yogakaraka in ${marsHouse}th for ${lagnaSign === 3 ? 'Cancer' : 'Leo'} Lagna. Success through courage, property, and action.`,
                    descriptionKey: 'Yogakaraka_Mars',
                    planets: ['Mars'],
                    nature: 'Benefic',
                    strength: 8
                }));
            }
        }
    }

    /**
     * Adhyatmika Yoga (Inner spirituality)
     * 5th house/lord strong with Jupiter/Ketu influence
     */
    _checkAdhyatmikaYoga() {
        const lord5 = this.getHouseLord(5);
        const lord5Strong = this.isStrong(lord5) ||
            ['Exalted', 'Own'].includes(this.getDignity(lord5));

        const jupAspects5 = this._aspectsHouse('Jupiter', this.getHouse('Jupiter'), 5);
        const ketuIn5 = this.getHouse('Ketu') === 5;

        if (lord5Strong && (jupAspects5 || ketuIn5)) {
            this.addYoga(createYoga({
                name: 'Adhyatmika Yoga',
                nameKey: 'Adhyatmika',
                category: 'Spiritual',
                description: 'Strong 5th lord with Jupiter/Ketu influence. Inner spirituality - mantra siddhi, intuition, past-life knowledge.',
                descriptionKey: 'Adhyatmika',
                planets: [lord5, ketuIn5 ? 'Ketu' : 'Jupiter'],
                nature: 'Benefic',
                strength: 7
            }));
        }
    }

    /**
     * Siddhi Yoga (Perfection/Powers)
     * Ketu strong in 5th/9th with benefic aspect
     */
    _checkSiddhiYoga() {
        const ketuHouse = this.getHouse('Ketu');
        const ketuInSpiritual = [5, 9].includes(ketuHouse);

        if (!ketuInSpiritual) return;

        const jupAspectsKetu = this.aspects('Jupiter', 'Ketu');
        const venAspectsKetu = this.aspects('Venus', 'Ketu');

        if (jupAspectsKetu || venAspectsKetu) {
            this.addYoga(createYoga({
                name: 'Siddhi Yoga',
                nameKey: 'Siddhi',
                category: 'Spiritual',
                description: `Ketu in ${ketuHouse}th with benefic aspect. Spiritual powers, psychic abilities, healing capacity, mantra siddhi.`,
                descriptionKey: 'Siddhi',
                planets: ['Ketu', jupAspectsKetu ? 'Jupiter' : 'Venus'],
                nature: 'Benefic',
                strength: 7
            }));
        }
    }

    /**
     * Guru Bhakti Yoga (Devotion to teacher)
     * Jupiter in 9th or 5th strong
     */
    _checkGuruBhaktiYoga() {
        const jupHouse = this.getHouse('Jupiter');
        const jupStrong = this.isStrong('Jupiter') ||
            ['Exalted', 'Own', 'Moolatrikona'].includes(this.getDignity('Jupiter'));

        if ([5, 9].includes(jupHouse) && jupStrong && !this.isCombust('Jupiter')) {
            this.addYoga(createYoga({
                name: 'Guru Bhakti Yoga',
                nameKey: 'Guru_Bhakti',
                category: 'Spiritual',
                description: 'Strong Jupiter in 5th or 9th. Devoted to spiritual teacher, learns from guru, carries on lineage teachings.',
                descriptionKey: 'Guru_Bhakti',
                planets: ['Jupiter'],
                nature: 'Benefic',
                strength: this.getStrength(['Jupiter']) + 1
            }));
        }
    }

    /**
     * Jnana Yoga (Path of knowledge)
     * Jupiter-Mercury connection with 5th/9th
     */
    _checkJnanaYoga() {
        const jupMercConj = this.isConjunct('Jupiter', 'Mercury');
        const jupMercAspect = this.aspects('Jupiter', 'Mercury') || this.aspects('Mercury', 'Jupiter');

        if (!jupMercConj && !jupMercAspect) return;

        const jupHouse = this.getHouse('Jupiter');
        const mercHouse = this.getHouse('Mercury');
        const knowledgeHouses = [1, 5, 9];

        if (knowledgeHouses.includes(jupHouse) || knowledgeHouses.includes(mercHouse)) {
            this.addYoga(createYoga({
                name: 'Jnana Yoga',
                nameKey: 'Jnana',
                category: 'Spiritual',
                description: 'Jupiter-Mercury connection in knowledge houses. Path of wisdom - liberation through understanding, philosophical mind.',
                descriptionKey: 'Jnana',
                planets: ['Jupiter', 'Mercury'],
                nature: 'Benefic',
                strength: this.getStrength(['Jupiter', 'Mercury'])
            }));
        }
    }
}

export default SpiritualYogas;
