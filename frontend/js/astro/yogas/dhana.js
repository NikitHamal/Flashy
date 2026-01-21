/**
 * Dhana (Wealth) Yogas Module
 * Implements wealth-generating planetary combinations
 */

import I18n from '../../core/i18n.js';
import { YogaModuleBase, createYoga, kendras, trikonas } from './base.js';

export class DhanaYogas extends YogaModuleBase {
    check() {
        this._checkChandraMangalVariations();
        this._checkShankhaYoga();
        this._checkBheriYoga();
        this._checkKoormaYoga();
        this._checkKhagaYoga();
        this._checkShreenathYoga();
        this._checkKahalYoga();
        this._checkRajyaLakshmiYoga();
        this._checkUttamadiYoga();
        this._checkSriKanthaYoga();
        this._checkSunaphaDhana();
        this._checkChatussagaraYoga();
        this._checkShubhaUbhayachari();
        this._checkAkhandDhanYoga();
        this._checkMadhyaYoga();
        this._checkSpecificDhanaYogas();
    }

    /**
     * Chandra-Mangal Yoga variations in specific houses
     */
    _checkChandraMangalVariations() {
        if (!this.isConjunct('Moon', 'Mars')) return;

        const moonHouse = this.getHouse('Moon');
        const wealthHouses = [2, 5, 9, 11];

        if (wealthHouses.includes(moonHouse)) {
            this.addYoga(createYoga({
                name: I18n.t('lists.yoga_list.Chandra_Mangal_Dhana.name'),
                nameKey: 'Chandra_Mangal_Dhana',
                category: 'Dhana',
                description: I18n.t('lists.yoga_list.Chandra_Mangal_Dhana.effects'),
                descriptionKey: 'Chandra_Mangal_Dhana',
                planets: ['Moon', 'Mars'],
                nature: 'Benefic',
                strength: this.getStrength(['Moon', 'Mars']) * 1.1,
                params: { planet: 'Moon', p2: 'Mars' }
            }));
        }
    }

    /**
     * Shankha Yoga (Dhana version)
     * Lords of 5th & 6th in Kendras from each other
     */
    _checkShankhaYoga() {
        const lord5 = this.getHouseLord(5);
        const lord6 = this.getHouseLord(6);

        const lord5Sign = this.getRasi(lord5);
        const lord6House = this.getHouse(lord6, lord5Sign);

        if (kendras.includes(lord6House)) {
            this.addYoga(createYoga({
                name: I18n.t('lists.yoga_list.Shankha_Dhana.name'),
                nameKey: 'Shankha_Dhana',
                category: 'Dhana',
                description: I18n.t('lists.yoga_list.Shankha_Dhana.effects'),
                descriptionKey: 'Shankha_Dhana',
                planets: [lord5, lord6],
                nature: 'Benefic',
                strength: this.getStrength([lord5, lord6])
            }));
        }
    }

    /**
     * Bheri Yoga (Wealth version)
     * 9th lord in Kendra, Jupiter, Venus, Lagna Lord in Kendras
     */
    _checkBheriYoga() {
        const lord9 = this.getHouseLord(9);
        const lord1 = this.getHouseLord(1);

        const lord9InKendra = kendras.includes(this.getHouse(lord9));
        const jupInKendra = kendras.includes(this.getHouse('Jupiter'));
        const venInKendra = kendras.includes(this.getHouse('Venus'));
        const lord1InKendra = kendras.includes(this.getHouse(lord1));

        if (lord9InKendra && jupInKendra && venInKendra && lord1InKendra) {
            this.addYoga(createYoga({
                name: I18n.t('lists.yoga_list.Bheri_Dhana.name'),
                nameKey: 'Bheri_Dhana',
                category: 'Dhana',
                description: I18n.t('lists.yoga_list.Bheri_Dhana.effects'),
                descriptionKey: 'Bheri_Dhana',
                planets: [lord9, 'Jupiter', 'Venus', lord1],
                nature: 'Benefic',
                strength: 8
            }));
        }
    }

    /**
     * Koorma Yoga
     * Benefics in 5th, 6th, 7th
     */
    _checkKoormaYoga() {
        const benefics = this.getNaturalBenefics();
        const inTarget = benefics.filter(p => [5, 6, 7].includes(this.getHouse(p)));

        if (inTarget.length >= 3) {
            this.addYoga(createYoga({
                name: I18n.t('lists.yoga_list.Koorma_Dhana.name'),
                nameKey: 'Koorma_Dhana',
                category: 'Dhana',
                description: I18n.t('lists.yoga_list.Koorma_Dhana.effects'),
                descriptionKey: 'Koorma_Dhana',
                planets: inTarget,
                nature: 'Benefic',
                strength: this.getStrength(inTarget)
            }));
        }
    }

    /**
     * Khaga Yoga
     * Jupiter in 9th, Venus in 4th from Jupiter
     */
    _checkKhagaYoga() {
        const jupHouse = this.getHouse('Jupiter');
        if (jupHouse !== 9) return;

        const venusHouseFromJup = this.getHouse('Venus', this.getRasi('Jupiter'));
        if (venusHouseFromJup === 4) {
            this.addYoga(createYoga({
                name: I18n.t('lists.yoga_list.Khaga_Dhana.name'),
                nameKey: 'Khaga_Dhana',
                category: 'Dhana',
                description: I18n.t('lists.yoga_list.Khaga_Dhana.effects'),
                descriptionKey: 'Khaga_Dhana',
                planets: ['Jupiter', 'Venus'],
                nature: 'Benefic',
                strength: 7
            }));
        }
    }

    /**
     * Shreenath Yoga
     * 7th lord exalted, 10th lord with 9th lord
     */
    _checkShreenathYoga() {
        const lord7 = this.getHouseLord(7);
        const lord9 = this.getHouseLord(9);
        const lord10 = this.getHouseLord(10);

        const lord7Exalted = this.getDignity(lord7) === 'Exalted';
        const lordsConjunct = this.isConjunct(lord9, lord10);

        if (lord7Exalted && lordsConjunct) {
            this.addYoga(createYoga({
                name: I18n.t('lists.yoga_list.Shreenath_Dhana.name'),
                nameKey: 'Shreenath_Dhana',
                category: 'Dhana',
                description: I18n.t('lists.yoga_list.Shreenath_Dhana.effects'),
                descriptionKey: 'Shreenath_Dhana',
                planets: [lord7, lord9, lord10],
                nature: 'Benefic',
                strength: 7
            }));
        }
    }

    /**
     * Kahal Yoga
     * 4th & 9th lords in Kendras from each other
     */
    _checkKahalYoga() {
        const lord4 = this.getHouseLord(4);
        const lord9 = this.getHouseLord(9);

        const lord4Sign = this.getRasi(lord4);
        const lord9House = this.getHouse(lord9, lord4Sign);

        if (kendras.includes(lord9House)) {
            this.addYoga(createYoga({
                name: I18n.t('lists.yoga_list.Kahal_Dhana.name'),
                nameKey: 'Kahal_Dhana',
                category: 'Dhana',
                description: I18n.t('lists.yoga_list.Kahal_Dhana.effects'),
                descriptionKey: 'Kahal_Dhana',
                planets: [lord4, lord9],
                nature: 'Benefic',
                strength: this.getStrength([lord4, lord9])
            }));
        }
    }

    /**
     * Rajya Lakshmi Yoga
     * Moon in Lagna, benefics in 6th, 7th, 8th
     */
    _checkRajyaLakshmiYoga() {
        const moonHouse = this.getHouse('Moon');
        if (moonHouse !== 1) return;

        const benefics = this.getNaturalBenefics();
        const in678 = benefics.filter(p => [6, 7, 8].includes(this.getHouse(p)));

        if (in678.length >= 2) {
            this.addYoga(createYoga({
                name: I18n.t('lists.yoga_list.Rajya_Lakshmi.name'),
                nameKey: 'Rajya_Lakshmi',
                category: 'Dhana',
                description: I18n.t('lists.yoga_list.Rajya_Lakshmi.effects'),
                descriptionKey: 'Rajya_Lakshmi',
                planets: ['Moon', ...in678],
                nature: 'Benefic',
                strength: 8
            }));
        }
    }

    /**
     * Uttamadi Yoga
     * Jupiter-Mercury in Kendras, Venus in own sign
     */
    _checkUttamadiYoga() {
        const jupInKendra = kendras.includes(this.getHouse('Jupiter'));
        const merInKendra = kendras.includes(this.getHouse('Mercury'));
        const venusInOwn = ['Own', 'Moolatrikona'].includes(this.getDignity('Venus'));

        if (jupInKendra && merInKendra && venusInOwn) {
            this.addYoga(createYoga({
                name: I18n.t('lists.yoga_list.Uttamadi.name'),
                nameKey: 'Uttamadi',
                category: 'Dhana',
                description: I18n.t('lists.yoga_list.Uttamadi.effects'),
                descriptionKey: 'Uttamadi',
                planets: ['Jupiter', 'Mercury', 'Venus'],
                nature: 'Benefic',
                strength: 7
            }));
        }
    }

    /**
     * Sri Kantha Yoga
     * 5th lord in 1st, 3rd lord in 11th
     */
    _checkSriKanthaYoga() {
        const lord5 = this.getHouseLord(5);
        const lord3 = this.getHouseLord(3);

        if (this.getHouse(lord5) === 1 && this.getHouse(lord3) === 11) {
            this.addYoga(createYoga({
                name: I18n.t('lists.yoga_list.Sri_Kantha.name'),
                nameKey: 'Sri_Kantha',
                category: 'Dhana',
                description: I18n.t('lists.yoga_list.Sri_Kantha.effects'),
                descriptionKey: 'Sri_Kantha',
                planets: [lord5, lord3],
                nature: 'Benefic',
                strength: 6
            }));
        }
    }

    /**
     * Sunapha Dhana variations
     * Specific planets in 2nd from Moon for wealth
     */
    _checkSunaphaDhana() {
        const moonSign = this.ctx.moonRasi;
        const planetsIn2nd = this.getPlanetsInHouse(2, moonSign);

        if (planetsIn2nd.length === 0) return;

        // Check for specific wealth-giving combinations
        if (planetsIn2nd.includes('Jupiter')) {
            this.addYoga(createYoga({
                name: I18n.t('lists.yoga_list.Sunapha_Dhana.name', { planet: I18n.t('planets.Jupiter') }),
                nameKey: 'Sunapha_Dhana',
                category: 'Dhana',
                description: I18n.t('lists.yoga_list.Sunapha_Dhana.effects', { planet: I18n.t('planets.Jupiter') }),
                descriptionKey: 'Sunapha_Dhana',
                planets: ['Moon', 'Jupiter'],
                nature: 'Benefic',
                strength: 7,
                params: { planet: 'Jupiter' }
            }));
        }

        if (planetsIn2nd.includes('Venus')) {
            this.addYoga(createYoga({
                name: I18n.t('lists.yoga_list.Sunapha_Dhana.name', { planet: I18n.t('planets.Venus') }),
                nameKey: 'Sunapha_Dhana',
                category: 'Dhana',
                description: I18n.t('lists.yoga_list.Sunapha_Dhana.effects', { planet: I18n.t('planets.Venus') }),
                descriptionKey: 'Sunapha_Dhana',
                planets: ['Moon', 'Venus'],
                nature: 'Benefic',
                strength: 6,
                params: { planet: 'Venus' }
            }));
        }

        if (planetsIn2nd.includes('Mercury')) {
            this.addYoga(createYoga({
                name: I18n.t('lists.yoga_list.Sunapha_Dhana.name', { planet: I18n.t('planets.Mercury') }),
                nameKey: 'Sunapha_Dhana',
                category: 'Dhana',
                description: I18n.t('lists.yoga_list.Sunapha_Dhana.effects', { planet: I18n.t('planets.Mercury') }),
                descriptionKey: 'Sunapha_Dhana',
                planets: ['Moon', 'Mercury'],
                nature: 'Benefic',
                strength: 6,
                params: { planet: 'Mercury' }
            }));
        }
    }

    /**
     * Chatussagara Yoga
     * All Kendras occupied by planets
     */
    _checkChatussagaraYoga() {
        const occupied = kendras.filter(h => this.getPlanetsInHouse(h).length > 0);

        if (occupied.length === 4) {
            this.addYoga(createYoga({
                name: I18n.t('lists.yoga_list.Chatussagara.name'),
                nameKey: 'Chatussagara',
                category: 'Dhana',
                description: I18n.t('lists.yoga_list.Chatussagara.effects'),
                descriptionKey: 'Chatussagara',
                planets: kendras.flatMap(h => this.getPlanetsInHouse(h)),
                nature: 'Benefic',
                strength: 8
            }));
        }
    }

    /**
     * Shubha Ubhayachari Yoga
     * Only benefics on both sides of Sun
     */
    _checkShubhaUbhayachari() {
        const sunSign = this.ctx.sunRasi;
        const benefics = this.getNaturalBenefics();

        const in2nd = this.getPlanetsInHouse(2, sunSign).filter(p => p !== 'Sun');
        const in12th = this.getPlanetsInHouse(12, sunSign).filter(p => p !== 'Sun');

        const beneficsIn2nd = in2nd.filter(p => benefics.includes(p));
        const beneficsIn12th = in12th.filter(p => benefics.includes(p));
        const hasMalefics = [...in2nd, ...in12th].some(p => !benefics.includes(p));

        if (beneficsIn2nd.length > 0 && beneficsIn12th.length > 0 && !hasMalefics) {
            this.addYoga(createYoga({
                name: I18n.t('lists.yoga_list.Shubha_Ubhayachari.name'),
                nameKey: 'Shubha_Ubhayachari',
                category: 'Dhana',
                description: I18n.t('lists.yoga_list.Shubha_Ubhayachari.effects'),
                descriptionKey: 'Shubha_Ubhayachari',
                planets: ['Sun', ...beneficsIn2nd, ...beneficsIn12th],
                nature: 'Benefic',
                strength: 7
            }));
        }
    }

    /**
     * Akhand Dhan Yoga
     * Jupiter in 5th/11th aspecting 2nd lord
     */
    _checkAkhandDhanYoga() {
        const jupHouse = this.getHouse('Jupiter');
        const lord2 = this.getHouseLord(2);

        if ([5, 11].includes(jupHouse) && this.aspects('Jupiter', lord2)) {
            this.addYoga(createYoga({
                name: I18n.t('lists.yoga_list.Akhand_Dhan.name'),
                nameKey: 'Akhand_Dhan',
                category: 'Dhana',
                description: I18n.t('lists.yoga_list.Akhand_Dhan.effects'),
                descriptionKey: 'Akhand_Dhan',
                planets: ['Jupiter', lord2],
                nature: 'Benefic',
                strength: 7
            }));
        }
    }

    /**
     * Madhya Yoga
     * 7th lord in 10th, 10th lord in exaltation
     */
    _checkMadhyaYoga() {
        const lord7 = this.getHouseLord(7);
        const lord10 = this.getHouseLord(10);

        const lord7House = this.getHouse(lord7);
        const lord10Dignity = this.getDignity(lord10);

        if (lord7House === 10 && lord10Dignity === 'Exalted') {
            this.addYoga(createYoga({
                name: I18n.t('lists.yoga_list.Madhya.name'),
                nameKey: 'Madhya',
                category: 'Dhana',
                description: I18n.t('lists.yoga_list.Madhya.effects'),
                descriptionKey: 'Madhya',
                planets: [lord7, lord10],
                nature: 'Benefic',
                strength: 7
            }));
        }
    }

    /**
     * Additional specific Dhana Yogas
     */
    _checkSpecificDhanaYogas() {
        const lord2 = this.getHouseLord(2);
        const lord5 = this.getHouseLord(5);
        const lord9 = this.getHouseLord(9);
        const lord11 = this.getHouseLord(11);

        // 2nd and 9th lords connection - inherited wealth
        if (this.isConnected(lord2, lord9)) {
            this.addYoga(createYoga({
                name: I18n.t('lists.yoga_list.Pitri_Dhana.name'),
                nameKey: 'Pitri_Dhana',
                category: 'Dhana',
                description: I18n.t('lists.yoga_list.Pitri_Dhana.effects'),
                descriptionKey: 'Pitri_Dhana',
                planets: [lord2, lord9],
                nature: 'Benefic',
                strength: this.getStrength([lord2, lord9])
            }));
        }

        // 5th and 11th lords connection - speculative gains
        if (this.isConnected(lord5, lord11)) {
            this.addYoga(createYoga({
                name: I18n.t('lists.yoga_list.Labha.name'),
                nameKey: 'Labha',
                category: 'Dhana',
                description: I18n.t('lists.yoga_list.Labha.effects'),
                descriptionKey: 'Labha',
                planets: [lord5, lord11],
                nature: 'Benefic',
                strength: this.getStrength([lord5, lord11])
            }));
        }

        // Jupiter in 2nd or 11th - natural wealth indicator
        const jupHouse = this.getHouse('Jupiter');
        if (jupHouse === 2 && !this.isCombust('Jupiter')) {
            this.addYoga(createYoga({
                name: I18n.t('lists.yoga_list.Dhana_Guru.name'),
                nameKey: 'Dhana_Guru',
                category: 'Dhana',
                description: I18n.t('lists.yoga_list.Dhana_Guru.effects'),
                descriptionKey: 'Dhana_Guru',
                planets: ['Jupiter'],
                nature: 'Benefic',
                strength: this.getStrength(['Jupiter'])
            }));
        }

        if (jupHouse === 11 && !this.isCombust('Jupiter')) {
            this.addYoga(createYoga({
                name: I18n.t('lists.yoga_list.Labha_Guru.name'),
                nameKey: 'Labha_Guru',
                category: 'Dhana',
                description: I18n.t('lists.yoga_list.Labha_Guru.effects'),
                descriptionKey: 'Labha_Guru',
                planets: ['Jupiter'],
                nature: 'Benefic',
                strength: this.getStrength(['Jupiter'])
            }));
        }
    }
}

export default DhanaYogas;
