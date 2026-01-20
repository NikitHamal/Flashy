/**
 * ============================================================================
 * ARISHTA YOGAS - Affliction and Challenge Combinations
 * ============================================================================
 *
 * This module implements Arishta (affliction) yogas from classical texts:
 * - Balarishta (Childhood afflictions)
 * - Rogarishta (Health afflictions)
 * - Daridra (Poverty yogas)
 * - Accident/Mishap indicators
 *
 * References:
 * - Brihat Parashara Hora Shastra (BPHS) Chapter 13, 44
 * - Phaladeepika
 * - Jataka Parijata
 *
 * @module yogas/arishta
 * @version 1.0.0
 */

import I18n from '../../core/i18n.js';
import { YogaModuleBase, createYoga, kendras, trikonas, dusthanas } from './base.js';

/**
 * Arishta Yogas Module
 */
export class ArishtaYogas extends YogaModuleBase {
    constructor(ctx) {
        super(ctx);
    }

    check() {
        this._checkBalarishta();
        this._checkRogaYogas();
        this._checkDaridrYogas();
        this._checkAccidentYogas();
        this._checkMrityuYogas();
        this._checkDurbhagyaYogas();
        this._checkComprehensiveBhanga();
    }

    // ========================================================================
    // BALARISHTA YOGAS (Childhood Afflictions)
    // ========================================================================

    _checkBalarishta() {
        const ctx = this.ctx;

        // Balarishta: Moon afflicted in specific ways
        const moonHouse = ctx.getHouse('Moon');
        const isWaning = !ctx.isWaxingMoon();

        // 1. Moon in 6/8/12 with malefic aspects
        if (dusthanas.includes(moonHouse) && isWaning) {
            const maleficsAspecting = ['Mars', 'Saturn', 'Rahu', 'Ketu'].filter(m => ctx.aspects(m, 'Moon'));
            if (maleficsAspecting.length > 0) {
                // Advanced Bhanga: Check Avasthas
                const moonAvastha = ctx.avasthas?.Moon;
                const isDeepta = moonAvastha?.deeptadi?.state === 'DEEPTA';
                const isBhojana = moonAvastha?.sayanaadi?.state === 'BHOJANA';
                
                // Check for traditional cancellation
                const jupAspects = ctx.aspects('Jupiter', 'Moon');
                const venAspects = ctx.aspects('Venus', 'Moon');

                if (jupAspects || venAspects || isDeepta || isBhojana) {
                    ctx.addYoga(createYoga({
                        name: I18n.t('lists.yoga_list.Balarishta_Bhanga.name'),
                        nameKey: 'Balarishta_Bhanga',
                        category: 'Arishta',
                        description: I18n.t('lists.yoga_list.Balarishta_Bhanga.effects'),
                        descriptionKey: 'Balarishta_Bhanga',
                        planets: ['Moon', ...(jupAspects ? ['Jupiter'] : []), ...(venAspects ? ['Venus'] : [])],
                        nature: 'Neutral',
                        strength: 6 + (isDeepta ? 2 : 0)
                    }));
                } else {
                    ctx.addYoga(createYoga({
                        name: I18n.t('lists.yoga_list.Balarishta.name'),
                        nameKey: 'Balarishta',
                        category: 'Arishta',
                        description: I18n.t('lists.yoga_list.Balarishta.effects', {
                            house: I18n.n(moonHouse),
                            planets: maleficsAspecting.map(p => I18n.t('planets.' + p)).join(', ')
                        }),
                        descriptionKey: 'Balarishta',
                        planets: ['Moon', ...maleficsAspecting],
                        nature: 'Malefic',
                        strength: 3,
                        params: { house: moonHouse, planets: maleficsAspecting.join(', ') }
                    }));
                }
            }
        }

        // 2. Lagna lord in 6/8/12 with malefic
        const lord1 = ctx.getHouseLord(1);
        const lord1House = ctx.getHouse(lord1);
        if (dusthanas.includes(lord1House)) {
            const maleficsConj = ['Mars', 'Saturn', 'Rahu', 'Ketu'].filter(m => ctx.isConjunct(lord1, m));
            if (maleficsConj.length > 0) {
                ctx.addYoga(createYoga({
                    name: I18n.t('lists.yoga_list.Lagna_Arishta.name'),
                    nameKey: 'Lagna_Arishta',
                    category: 'Arishta',
                    description: I18n.t('lists.yoga_list.Lagna_Arishta.effects'),
                    descriptionKey: 'Lagna_Arishta',
                    planets: [lord1, ...maleficsConj],
                    nature: 'Malefic',
                    strength: 4,
                    params: { planet: lord1, house: lord1House }
                }));
            }
        }

        // 3. Moon in Rahu-Ketu axis
        const moonRasi = ctx.moonRasi;
        if (moonRasi === ctx.getRasi('Rahu') || moonRasi === ctx.getRasi('Ketu')) {
            ctx.addYoga(createYoga({
                name: I18n.t('lists.yoga_list.Grahan.name', { planet: I18n.t('planets.Moon') }),
                nameKey: 'Grahan',
                category: 'Arishta',
                description: I18n.t('lists.yoga_list.Grahan.effects', { planet: I18n.t('planets.Moon') }),
                descriptionKey: 'Grahan',
                planets: ['Moon', 'Rahu', 'Ketu'],
                nature: 'Malefic',
                strength: 4,
                params: { planet: 'Moon' }
            }));
        }
    }

    _checkRogaYogas() {
        const ctx = this.ctx;
        const lord6 = ctx.getHouseLord(6);
        const lord1 = ctx.getHouseLord(1);

        if (ctx.isConnected(lord6, lord1)) {
            ctx.addYoga(createYoga({
                name: I18n.t('lists.yoga_list.Roga.name'),
                nameKey: 'Roga',
                category: 'Arishta',
                description: I18n.t('lists.yoga_list.Roga.effects'),
                descriptionKey: 'Roga',
                planets: [lord6, lord1],
                nature: 'Malefic',
                strength: 4
            }));
        }

        if (ctx.isConjunct('Sun', 'Saturn')) {
            ctx.addYoga(createYoga({
                name: I18n.t('lists.yoga_list.Pitru_Kashta.name'),
                nameKey: 'Pitru_Kashta',
                category: 'Arishta',
                description: I18n.t('lists.yoga_list.Pitru_Kashta.effects'),
                descriptionKey: 'Pitru_Kashta',
                planets: ['Sun', 'Saturn'],
                nature: 'Malefic',
                strength: 4
            }));
        }

        const marsHouse = ctx.getHouse('Mars');
        if ([6, 8].includes(marsHouse)) {
            if (!['Exalted', 'Own'].includes(ctx.getDignity('Mars'))) {
                ctx.addYoga(createYoga({
                    name: I18n.t('lists.yoga_list.Kshata.name'),
                    nameKey: 'Kshata',
                    category: 'Arishta',
                    description: I18n.t('lists.yoga_list.Kshata.effects'),
                    descriptionKey: 'Kshata',
                    planets: ['Mars'],
                    nature: 'Malefic',
                    strength: 4
                }));
            }
        }

        const lord8 = ctx.getHouseLord(8);
        if (ctx.getHouse(lord8) === 1) {
            ctx.addYoga(createYoga({
                name: I18n.t('lists.yoga_list.Deha_Durbala.name'),
                nameKey: 'Deha_Durbala',
                category: 'Arishta',
                description: I18n.t('lists.yoga_list.Deha_Durbala.effects'),
                descriptionKey: 'Deha_Durbala',
                planets: [lord8],
                nature: 'Malefic',
                strength: 4
            }));
        }

        if (ctx.isConjunct('Moon', 'Saturn')) {
            ctx.addYoga(createYoga({
                name: I18n.t('lists.yoga_list.Vish_Yoga.name'),
                nameKey: 'Vish_Yoga',
                category: 'Arishta',
                description: I18n.t('lists.yoga_list.Vish_Yoga.effects'),
                descriptionKey: 'Vish_Yoga',
                planets: ['Moon', 'Saturn'],
                nature: 'Malefic',
                strength: 4,
                params: { planet: 'Moon', p2: 'Saturn' }
            }));
        }
    }

    _checkDaridrYogas() {
        const ctx = this.ctx;
        const lord11 = ctx.getHouseLord(11);
        const lord11House = ctx.getHouse(lord11);

        if (dusthanas.includes(lord11House) && !this.isStrong(lord11)) {
            ctx.addYoga(createYoga({
                name: I18n.t('lists.yoga_list.Daridra.name'),
                nameKey: 'Daridra',
                category: 'Arishta',
                description: I18n.t('lists.yoga_list.Daridra.effects', { house: I18n.n(lord11House) }),
                descriptionKey: 'Daridra',
                planets: [lord11],
                nature: 'Malefic',
                strength: 3,
                params: { house: lord11House }
            }));
        }

        const lord2 = ctx.getHouseLord(2);
        if (ctx.getHouse(lord2) === 12) {
            ctx.addYoga(createYoga({
                name: I18n.t('lists.yoga_list.Dhana_Nashak.name'),
                nameKey: 'Dhana_Nashak',
                category: 'Arishta',
                description: I18n.t('lists.yoga_list.Dhana_Nashak.effects'),
                descriptionKey: 'Dhana_Nashak',
                planets: [lord2],
                nature: 'Malefic',
                strength: 4
            }));
        }

        if (ctx.isCombust('Jupiter')) {
            ctx.addYoga(createYoga({
                name: I18n.t('lists.yoga_list.Guru_Asta.name'),
                nameKey: 'Guru_Asta',
                category: 'Arishta',
                description: I18n.t('lists.yoga_list.Guru_Asta.effects'),
                descriptionKey: 'Guru_Asta',
                planets: ['Jupiter', 'Sun'],
                nature: 'Malefic',
                strength: 4
            }));
        }

        const malefics = ['Saturn', 'Mars', 'Rahu', 'Ketu'];
        const maleficsInKendras = malefics.filter(p => kendras.includes(ctx.getHouse(p)));
        if (maleficsInKendras.length >= 3) {
            ctx.addYoga(createYoga({
                name: I18n.t('lists.yoga_list.Maha_Sarpa.name'),
                nameKey: 'Maha_Sarpa',
                category: 'Arishta',
                description: I18n.t('lists.yoga_list.Maha_Sarpa.effects'),
                descriptionKey: 'Maha_Sarpa',
                planets: maleficsInKendras,
                nature: 'Malefic',
                strength: 3
            }));
        }
    }

    _checkAccidentYogas() {
        const ctx = this.ctx;

        if (ctx.isConjunct('Mars', 'Rahu')) {
            ctx.addYoga(createYoga({
                name: I18n.t('lists.yoga_list.Angarak.name'),
                nameKey: 'Angarak',
                category: 'Arishta',
                description: I18n.t('lists.yoga_list.Angarak.effects', { house: I18n.n(ctx.getHouse('Mars')) }),
                descriptionKey: 'Angarak',
                planets: ['Mars', 'Rahu'],
                nature: 'Malefic',
                strength: 3,
                params: { house: ctx.getHouse('Mars') }
            }));
        }

        const lord8 = ctx.getHouseLord(8);
        if (ctx.isConnected(lord8, 'Mars')) {
            ctx.addYoga(createYoga({
                name: I18n.t('lists.yoga_list.Apamrityu.name'),
                nameKey: 'Apamrityu',
                category: 'Arishta',
                description: I18n.t('lists.yoga_list.Apamrityu.effects'),
                descriptionKey: 'Apamrityu',
                planets: [lord8, 'Mars'],
                nature: 'Malefic',
                strength: 4
            }));

            if (ctx.aspects('Jupiter', 'Mars') || ctx.aspects('Jupiter', lord8)) {
                ctx.addYoga(createYoga({
                    name: I18n.t('lists.yoga_list.Apamrityu_Bhanga.name'),
                    nameKey: 'Apamrityu_Bhanga',
                    category: 'Arishta',
                    description: I18n.t('lists.yoga_list.Apamrityu_Bhanga.effects'),
                    descriptionKey: 'Apamrityu_Bhanga',
                    planets: ['Jupiter', lord8, 'Mars'],
                    nature: 'Neutral',
                    strength: 5
                }));
            }
        }

        const planetsIn4 = ctx.getPlanetsInHouse(4);
        const maleficsIn4 = planetsIn4.filter(p => ['Mars', 'Saturn', 'Rahu', 'Ketu'].includes(p));
        if (maleficsIn4.length >= 2) {
            ctx.addYoga(createYoga({
                name: I18n.t('lists.yoga_list.Vahana_Kshaya.name'),
                nameKey: 'Vahana_Kshaya',
                category: 'Arishta',
                description: I18n.t('lists.yoga_list.Vahana_Kshaya.effects'),
                descriptionKey: 'Vahana_Kshaya',
                planets: maleficsIn4,
                nature: 'Malefic',
                strength: 4
            }));
        }
    }

    _checkMrityuYogas() {
        const ctx = this.ctx;
        const lord1 = ctx.getHouseLord(1);
        const lord8 = ctx.getHouseLord(8);

        let alpayuCount = 0;
        if (dusthanas.includes(ctx.getHouse(lord1)) && !ctx.isStrong(lord1)) alpayuCount++;
        if (ctx.getHouse(lord8) === 1) alpayuCount++;
        if ([6, 8].includes(ctx.getHouse('Moon')) && !ctx.isWaxingMoon()) alpayuCount++;
        if (ctx.aspects('Saturn', lord1) && !ctx.aspects('Jupiter', lord1)) alpayuCount++;

        if (alpayuCount >= 3) {
            if (kendras.includes(ctx.getHouse('Jupiter')) || ctx.isStrong(lord1)) {
                ctx.addYoga(createYoga({
                    name: I18n.t('lists.yoga_list.Madhyayu.name'),
                    nameKey: 'Madhyayu',
                    category: 'Longevity',
                    description: I18n.t('lists.yoga_list.Madhyayu.effects'),
                    descriptionKey: 'Madhyayu',
                    planets: [lord1, 'Jupiter'],
                    nature: 'Neutral',
                    strength: 5
                }));
            } else {
                ctx.addYoga(createYoga({
                    name: I18n.t('lists.yoga_list.Alpayu.name'),
                    nameKey: 'Alpayu',
                    category: 'Longevity',
                    description: I18n.t('lists.yoga_list.Alpayu.effects'),
                    descriptionKey: 'Alpayu',
                    planets: [lord1, lord8],
                    nature: 'Malefic',
                    strength: 3
                }));
            }
        }

        if (kendras.includes(ctx.getHouse(lord1)) && ctx.isStrong(lord1)) {
            if (kendras.includes(ctx.getHouse('Jupiter')) || trikonas.includes(ctx.getHouse('Jupiter'))) {
                ctx.addYoga(createYoga({
                    name: I18n.t('lists.yoga_list.Deerghayu.name'),
                    nameKey: 'Deerghayu',
                    category: 'Longevity',
                    description: I18n.t('lists.yoga_list.Deerghayu.effects'),
                    descriptionKey: 'Deerghayu',
                    planets: [lord1, 'Jupiter'],
                    nature: 'Benefic',
                    strength: 7
                }));
            }
        }
    }

    _checkDurbhagyaYogas() {
        const ctx = this.ctx;
        const lord9 = ctx.getHouseLord(9);
        const lord9House = ctx.getHouse(lord9);

        if (dusthanas.includes(lord9House)) {
            if (!ctx.isConnected('Jupiter', lord9)) {
                ctx.addYoga(createYoga({
                    name: I18n.t('lists.yoga_list.Durbhagya.name'),
                    nameKey: 'Durbhagya',
                    category: 'Arishta',
                    description: I18n.t('lists.yoga_list.Durbhagya.effects'),
                    descriptionKey: 'Durbhagya',
                    planets: [lord9],
                    nature: 'Malefic',
                    strength: 4
                }));
            }
        }

        const planetsIn9 = ctx.getPlanetsInHouse(9);
        const maleficsIn9 = planetsIn9.filter(p => ['Sun', 'Mars', 'Saturn', 'Rahu', 'Ketu'].includes(p));
        if (maleficsIn9.length >= 2) {
            ctx.addYoga(createYoga({
                name: I18n.t('lists.yoga_list.Bhagya_Nashak.name'),
                nameKey: 'Bhagya_Nashak',
                category: 'Arishta',
                description: I18n.t('lists.yoga_list.Bhagya_Nashak.effects'),
                descriptionKey: 'Bhagya_Nashak',
                planets: maleficsIn9,
                nature: 'Malefic',
                strength: 4
            }));
        }

        if (ctx.isConjunct('Saturn', 'Rahu')) {
            ctx.addYoga(createYoga({
                name: I18n.t('lists.yoga_list.Shrapit.name'),
                nameKey: 'Shrapit',
                category: 'Arishta',
                description: I18n.t('lists.yoga_list.Shrapit.effects', { house: I18n.n(ctx.getHouse('Saturn')) }),
                descriptionKey: 'Shrapit',
                planets: ['Saturn', 'Rahu'],
                nature: 'Malefic',
                strength: 3,
                params: { house: ctx.getHouse('Saturn') }
            }));
        }

        const sunHouse = ctx.getHouse('Sun');
        const sunWithNodes = ctx.isConjunct('Sun', 'Rahu') || ctx.isConjunct('Sun', 'Ketu');
        const sunWithSaturn = ctx.isConjunct('Sun', 'Saturn');

        if (sunWithNodes || (sunWithSaturn && dusthanas.includes(sunHouse))) {
            ctx.addYoga(createYoga({
                name: I18n.t('lists.yoga_list.Pitra_Dosha.name'),
                nameKey: 'Pitra_Dosha',
                category: 'Arishta',
                description: I18n.t('lists.yoga_list.Pitra_Dosha.effects', { house: I18n.n(sunHouse) }),
                descriptionKey: 'Pitra_Dosha',
                planets: ['Sun', sunWithNodes ? (ctx.isConjunct('Sun', 'Rahu') ? 'Rahu' : 'Ketu') : 'Saturn'],
                nature: 'Malefic',
                strength: 4,
                params: { house: sunHouse }
            }));
        }
    }

    _checkComprehensiveBhanga() {
        this._checkVishYogaBhanga();
        this._checkGrahanBhanga();
        this._checkAngarakBhanga();
        this._checkShrapitBhanga();
        this._checkPitraDoshaBhanga();
        this._checkGeneralArishtaBhanga();
        this._checkKemadrumaEnhancedBhanga();
    }

    _checkVishYogaBhanga() {
        const ctx = this.ctx;
        if (!ctx.isConjunct('Moon', 'Saturn')) return;

        const bhangaConditions = [];
        if (ctx.aspects('Jupiter', 'Moon') || ctx.aspects('Jupiter', 'Saturn')) bhangaConditions.push('Jupiter blessing');
        const moonDig = ctx.getDignity('Moon');
        if (['Exalted', 'Own'].includes(moonDig)) bhangaConditions.push('Moon dignity');
        if (ctx.isWaxingMoon()) bhangaConditions.push('Waxing Moon');

        if (bhangaConditions.length >= 2) {
            ctx.addYoga(createYoga({
                name: I18n.t('lists.yoga_list.Vish_Yoga_Bhanga.name'),
                nameKey: 'Vish_Yoga_Bhanga',
                category: 'Arishta_Bhanga',
                description: I18n.t('lists.yoga_list.Vish_Yoga_Bhanga.effects'),
                descriptionKey: 'Vish_Yoga_Bhanga',
                planets: ['Moon', 'Saturn', 'Jupiter'],
                nature: 'Benefic',
                strength: 6
            }));
        }
    }

    _checkGrahanBhanga() {
        const ctx = this.ctx;
        const moonWithRahu = ctx.getRasi('Moon') === ctx.getRasi('Rahu');
        const sunWithRahu = ctx.getRasi('Sun') === ctx.getRasi('Rahu');
        if (!moonWithRahu && !sunWithRahu) return;

        const afflicted = moonWithRahu ? 'Moon' : 'Sun';
        if (ctx.aspects('Jupiter', afflicted) || ['Exalted', 'Own'].includes(ctx.getDignity(afflicted))) {
            ctx.addYoga(createYoga({
                name: I18n.t('lists.yoga_list.Grahan_Bhanga.name'),
                nameKey: 'Grahan_Bhanga',
                category: 'Arishta_Bhanga',
                description: I18n.t('lists.yoga_list.Grahan_Bhanga.effects'),
                descriptionKey: 'Grahan_Bhanga',
                planets: [afflicted, 'Jupiter'],
                nature: 'Neutral',
                strength: 5
            }));
        }
    }

    _checkAngarakBhanga() {
        const ctx = this.ctx;
        if (!ctx.isConjunct('Mars', 'Rahu')) return;

        if (ctx.aspects('Jupiter', 'Mars') || ['Exalted', 'Own'].includes(ctx.getDignity('Mars'))) {
            ctx.addYoga(createYoga({
                name: I18n.t('lists.yoga_list.Angarak_Bhanga.name'),
                nameKey: 'Angarak_Bhanga',
                category: 'Arishta_Bhanga',
                description: I18n.t('lists.yoga_list.Angarak_Bhanga.effects'),
                descriptionKey: 'Angarak_Bhanga',
                planets: ['Mars', 'Rahu', 'Jupiter'],
                nature: 'Neutral',
                strength: 5
            }));
        }
    }

    _checkShrapitBhanga() {
        const ctx = this.ctx;
        if (!ctx.isConjunct('Saturn', 'Rahu')) return;

        if (ctx.aspects('Jupiter', 'Saturn') || ['Exalted', 'Own'].includes(ctx.getDignity('Saturn'))) {
            ctx.addYoga(createYoga({
                name: I18n.t('lists.yoga_list.Shrapit_Bhanga.name'),
                nameKey: 'Shrapit_Bhanga',
                category: 'Arishta_Bhanga',
                description: I18n.t('lists.yoga_list.Shrapit_Bhanga.effects'),
                descriptionKey: 'Shrapit_Bhanga',
                planets: ['Saturn', 'Rahu', 'Jupiter'],
                nature: 'Benefic',
                strength: 6
            }));
        }
    }

    _checkPitraDoshaBhanga() {
        const ctx = this.ctx;
        if (!ctx.isConjunct('Sun', 'Rahu') && !ctx.isConjunct('Sun', 'Saturn')) return;

        if (ctx.aspects('Jupiter', 'Sun') || ['Exalted', 'Own'].includes(ctx.getDignity('Sun'))) {
            ctx.addYoga(createYoga({
                name: I18n.t('lists.yoga_list.Pitra_Dosha_Bhanga.name'),
                nameKey: 'Pitra_Dosha_Bhanga',
                category: 'Arishta_Bhanga',
                description: I18n.t('lists.yoga_list.Pitra_Dosha_Bhanga.effects'),
                descriptionKey: 'Pitra_Dosha_Bhanga',
                planets: ['Sun', 'Jupiter'],
                nature: 'Benefic',
                strength: 6
            }));
        }
    }

    _checkGeneralArishtaBhanga() {
        const ctx = this.ctx;
        const lord1 = ctx.getHouseLord(1);
        let protectionCount = 0;

        if ([...kendras, ...trikonas].includes(ctx.getHouse('Jupiter')) && !ctx.isCombust('Jupiter')) protectionCount++;
        if (ctx.isStrong(lord1) && kendras.includes(ctx.getHouse(lord1))) protectionCount++;
        if (ctx.isWaxingMoon() && ['Exalted', 'Own'].includes(ctx.getDignity('Moon'))) protectionCount++;

        if (protectionCount >= 2) {
            ctx.addYoga(createYoga({
                name: I18n.t('lists.yoga_list.Sarva_Arishta_Bhanga.name'),
                nameKey: 'Sarva_Arishta_Bhanga',
                category: 'Arishta_Bhanga',
                description: I18n.t('lists.yoga_list.Sarva_Arishta_Bhanga.effects'),
                descriptionKey: 'Sarva_Arishta_Bhanga',
                planets: ['Jupiter', lord1],
                nature: 'Benefic',
                strength: 7
            }));
        }
    }

    _checkKemadrumaEnhancedBhanga() {
        const ctx = this.ctx;
        const moonRasi = ctx.moonRasi;
        const sevenPlanetsList = ['Sun', 'Mars', 'Mercury', 'Jupiter', 'Venus', 'Saturn'];

        const hasPlanetIn2or12 = sevenPlanetsList.some(p => {
            const pRasi = ctx.getRasi(p);
            if (pRasi === -1) return false;
            const dist = (pRasi - moonRasi + 12) % 12;
            return dist === 1 || dist === 11;
        });

        if (!hasPlanetIn2or12) {
            if (kendras.includes(ctx.getHouse('Moon')) || kendras.includes(ctx.getHouse('Jupiter'))) {
                ctx.addYoga(createYoga({
                    name: I18n.t('lists.yoga_list.Kemadruma_Bhanga_Enhanced.name'),
                    nameKey: 'Kemadruma_Bhanga_Enhanced',
                    category: 'Arishta_Bhanga',
                    description: I18n.t('lists.yoga_list.Kemadruma_Bhanga_Enhanced.effects'),
                    descriptionKey: 'Kemadruma_Bhanga_Enhanced',
                    planets: ['Moon', 'Jupiter'],
                    nature: 'Benefic',
                    strength: 6
                }));
            }
        }
    }
}

export default ArishtaYogas;
