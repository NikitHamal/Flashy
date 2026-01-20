/**
 * Raja Yogas - Specific Named Yogas
 * Implements major Raja Yogas beyond the basic Kendra-Trikona combinations
 */

import { YogaModuleBase, createYoga, kendras, trikonas, sevenPlanets } from './base.js';

export class RajaYogas extends YogaModuleBase {
    check() {
        this._checkMahaBhagyaYoga();
        this._checkKahalaYoga();
        this._checkChamaraYoga();
        this._checkSankhaYoga();
        this._checkBheriYoga();
        this._checkMridangaYoga();
        this._checkSreenathYoga();
        this._checkMatsyaYoga();
        this._checkKurmaYoga();
        this._checkKhagaYoga();
        this._checkKhadgaYoga();
        this._checkKusumaYoga();
        this._checkMakutaYoga();
        this._checkSimhasanaYoga();
        this._checkAkhandaSamrajyaYoga();
        this._checkParvataYoga();
        this._checkSaraswatiYoga();
        this._checkIndraYoga();
        this._checkBrahmaYoga();
        this._checkVishnuYoga();
        this._checkShivaYoga();
        this._checkShubhaMalaYoga();
    }

    /**
     * Maha Bhagya Yoga
     * Day birth/male: Sun, Moon, Lagna in odd signs
     * Night birth/female: Sun, Moon, Lagna in even signs
     */
    _checkMahaBhagyaYoga() {
        const sunSign = this.getRasi('Sun');
        const moonSign = this.getRasi('Moon');
        const lagnaSign = this.ctx.lagnaRasi;

        if (sunSign === -1 || moonSign === -1) return;

        // Check odd/even signs (0=Aries is odd, 1=Taurus is even)
        const isOdd = (sign) => sign % 2 === 0; // Aries(0), Gemini(2), etc are odd

        const sunOdd = isOdd(sunSign);
        const moonOdd = isOdd(moonSign);
        const lagnaOdd = isOdd(lagnaSign);

        // Determine day/night birth by Sun's house position
        const sunHouse = this.getHouse('Sun');
        const isDayBirth = sunHouse >= 1 && sunHouse <= 6; // Sun above horizon roughly

        // Male/Female check would need birth data - assume based on day/night for now
        // Traditional: Day birth male with all odd, Night birth female with all even

        if (isDayBirth && sunOdd && moonOdd && lagnaOdd) {
            this.addYoga(createYoga({
                name: 'Maha Bhagya Yoga (Day Birth)',
                nameKey: 'Maha_Bhagya',
                category: 'Raja',
                description: 'Sun, Moon, and Lagna all in odd signs with day birth. Exceptionally fortunate - wealth, fame, long life, royal comforts.',
                descriptionKey: 'Maha_Bhagya',
                planets: ['Sun', 'Moon'],
                nature: 'Benefic',
                strength: 9
            }));
        } else if (!isDayBirth && !sunOdd && !moonOdd && !lagnaOdd) {
            this.addYoga(createYoga({
                name: 'Maha Bhagya Yoga (Night Birth)',
                nameKey: 'Maha_Bhagya',
                category: 'Raja',
                description: 'Sun, Moon, and Lagna all in even signs with night birth. Exceptionally fortunate - wealth, fame, long life, royal comforts.',
                descriptionKey: 'Maha_Bhagya',
                planets: ['Sun', 'Moon'],
                nature: 'Benefic',
                strength: 9
            }));
        }
    }

    /**
     * Kahala Yoga
     * 4th lord and Jupiter in mutual Kendras, strong Lagna lord
     */
    _checkKahalaYoga() {
        const lord4 = this.getHouseLord(4);
        const lord1 = this.getHouseLord(1);

        const lord4House = this.getHouse(lord4);
        const jupiterHouse = this.getHouse('Jupiter');
        const lord1House = this.getHouse(lord1);

        // Check if 4th lord and Jupiter are in mutual Kendras
        const lord4InKendra = kendras.includes(lord4House);
        const jupInKendra = kendras.includes(jupiterHouse);
        const lord1Strong = this.isStrong(lord1) || ['Exalted', 'Own', 'Moolatrikona'].includes(this.getDignity(lord1));

        if (lord4InKendra && jupInKendra && lord1Strong) {
            this.addYoga(createYoga({
                name: 'Kahala Yoga',
                nameKey: 'Kahala',
                category: 'Raja',
                description: '4th lord and Jupiter in Kendras with strong Lagna lord. Brave, leads army, bold in ventures, rules territory.',
                descriptionKey: 'Kahala',
                planets: [lord4, 'Jupiter', lord1],
                nature: 'Benefic',
                strength: 7
            }));
        }
    }

    /**
     * Chamara Yoga
     * Lagna lord exalted in Kendra, aspected by Jupiter
     */
    _checkChamaraYoga() {
        const lord1 = this.getHouseLord(1);
        const lord1House = this.getHouse(lord1);
        const lord1Dignity = this.getDignity(lord1);

        if (lord1Dignity === 'Exalted' && kendras.includes(lord1House)) {
            if (this.aspects('Jupiter', lord1)) {
                this.addYoga(createYoga({
                    name: 'Chamara Yoga',
                    nameKey: 'Chamara',
                    category: 'Raja',
                    description: 'Lagna lord exalted in Kendra, aspected by Jupiter. Royal insignia - eloquent speaker, long-lived, king or equal.',
                    descriptionKey: 'Chamara',
                    planets: [lord1, 'Jupiter'],
                    nature: 'Benefic',
                    strength: 8
                }));
            }
        }
    }

    /**
     * Sankha Yoga
     * 5th and 6th lords in mutual Kendras
     */
    _checkSankhaYoga() {
        const lord5 = this.getHouseLord(5);
        const lord6 = this.getHouseLord(6);
        const lord5House = this.getHouse(lord5);
        const lord6House = this.getHouse(lord6);

        // Check if both are in Kendras (mutual position)
        if (kendras.includes(lord5House) && kendras.includes(lord6House)) {
            this.addYoga(createYoga({
                name: 'Sankha Yoga',
                nameKey: 'Sankha',
                category: 'Raja',
                description: '5th and 6th lords in mutual Kendras. Conch symbol - good spouse, children, land, righteous, long life.',
                descriptionKey: 'Sankha',
                planets: [lord5, lord6],
                nature: 'Benefic',
                strength: 7
            }));
        }
    }

    /**
     * Bheri Yoga
     * Venus, Jupiter, Lagna lord strong, 9th lord in Kendra
     */
    _checkBheriYoga() {
        const lord1 = this.getHouseLord(1);
        const lord9 = this.getHouseLord(9);
        const lord9House = this.getHouse(lord9);

        const venusStrong = this.isStrong('Venus');
        const jupiterStrong = this.isStrong('Jupiter');
        const lord1Strong = this.isStrong(lord1);
        const lord9InKendra = kendras.includes(lord9House);

        if (venusStrong && jupiterStrong && lord1Strong && lord9InKendra) {
            this.addYoga(createYoga({
                name: 'Bheri Yoga',
                nameKey: 'Bheri',
                category: 'Raja',
                description: 'Venus, Jupiter, Lagna lord strong with 9th lord in Kendra. Drum symbol - wealthy, famous, king-like, long-lived.',
                descriptionKey: 'Bheri',
                planets: ['Venus', 'Jupiter', lord1, lord9],
                nature: 'Benefic',
                strength: 8
            }));
        }
    }

    /**
     * Mridanga Yoga
     * Lagna lord strong, all planets in Kendras/Trikonas
     */
    _checkMridangaYoga() {
        const lord1 = this.getHouseLord(1);
        const lord1Strong = this.isStrong(lord1);

        // Check all planets in Kendras or Trikonas
        const goodHouses = [...kendras, ...trikonas];
        let allInGoodHouses = true;

        for (const p of sevenPlanets) {
            const h = this.getHouse(p);
            if (h === -1 || !goodHouses.includes(h)) {
                allInGoodHouses = false;
                break;
            }
        }

        if (lord1Strong && allInGoodHouses) {
            this.addYoga(createYoga({
                name: 'Mridanga Yoga',
                nameKey: 'Mridanga',
                category: 'Raja',
                description: 'Strong Lagna lord with all planets in Kendras/Trikonas. Musical drum - famous, adorned by king, royal honors.',
                descriptionKey: 'Mridanga',
                planets: sevenPlanets,
                nature: 'Benefic',
                strength: 9
            }));
        }
    }

    /**
     * Sreenatha Yoga
     * 7th lord exalted, 10th lord with 9th lord
     */
    _checkSreenathYoga() {
        const lord7 = this.getHouseLord(7);
        const lord9 = this.getHouseLord(9);
        const lord10 = this.getHouseLord(10);

        const lord7Exalted = this.getDignity(lord7) === 'Exalted';
        const lordsConjunct = this.isConjunct(lord9, lord10);

        if (lord7Exalted && lordsConjunct) {
            this.addYoga(createYoga({
                name: 'Sreenatha Yoga',
                nameKey: 'Sreenatha',
                category: 'Raja',
                description: '7th lord exalted, 10th lord with 9th lord. Lord of prosperity - wealthy in later life, high position.',
                descriptionKey: 'Sreenatha',
                planets: [lord7, lord9, lord10],
                nature: 'Benefic',
                strength: 7
            }));
        }
    }

    /**
     * Matsya Yoga
     * Lagna & 9th occupied, benefics in 5th, malefics in 4th & 8th
     */
    _checkMatsyaYoga() {
        const planetsIn1 = this.getPlanetsInHouse(1);
        const planetsIn9 = this.getPlanetsInHouse(9);
        const planetsIn5 = this.getPlanetsInHouse(5);
        const planetsIn4 = this.getPlanetsInHouse(4);
        const planetsIn8 = this.getPlanetsInHouse(8);

        const benefics = this.getNaturalBenefics();
        const malefics = this.getNaturalMalefics();

        const lagnaOccupied = planetsIn1.length > 0;
        const ninthOccupied = planetsIn9.length > 0;
        const beneficsIn5 = planetsIn5.some(p => benefics.includes(p));
        const maleficsIn4 = planetsIn4.some(p => malefics.includes(p));
        const maleficsIn8 = planetsIn8.some(p => malefics.includes(p));

        if (lagnaOccupied && ninthOccupied && beneficsIn5 && maleficsIn4 && maleficsIn8) {
            this.addYoga(createYoga({
                name: 'Matsya Yoga',
                nameKey: 'Matsya',
                category: 'Raja',
                description: 'Lagna & 9th occupied, benefics in 5th, malefics in 4th & 8th. Fish symbol - compassionate, religious, powerful.',
                descriptionKey: 'Matsya',
                planets: [...planetsIn1, ...planetsIn9, ...planetsIn5.filter(p => benefics.includes(p))],
                nature: 'Benefic',
                strength: 7
            }));
        }
    }

    /**
     * Kurma Yoga
     * Benefics in 5th, 6th, 7th in own/exaltation, malefics in 3rd, Lagna
     */
    _checkKurmaYoga() {
        const benefics = this.getNaturalBenefics();
        const malefics = this.getNaturalMalefics();

        const beneficsIn567 = benefics.filter(p => {
            const h = this.getHouse(p);
            const dig = this.getDignity(p);
            return [5, 6, 7].includes(h) && ['Exalted', 'Own', 'Moolatrikona'].includes(dig);
        });

        const maleficsIn3_1 = malefics.filter(p => {
            const h = this.getHouse(p);
            return [1, 3].includes(h);
        });

        if (beneficsIn567.length >= 2 && maleficsIn3_1.length >= 1) {
            this.addYoga(createYoga({
                name: 'Kurma Yoga',
                nameKey: 'Kurma',
                category: 'Raja',
                description: 'Benefics in 5th/6th/7th in dignity, malefics in Lagna/3rd. Tortoise symbol - righteous, famous, leader, happy.',
                descriptionKey: 'Kurma',
                planets: [...beneficsIn567, ...maleficsIn3_1],
                nature: 'Benefic',
                strength: 7
            }));
        }
    }

    /**
     * Khaga Yoga
     * Jupiter in 9th, Venus in 4th from Jupiter (12th from chart)
     */
    _checkKhagaYoga() {
        const jupiterHouse = this.getHouse('Jupiter');
        const venusHouseFromJup = this.getHouse('Venus', this.getRasi('Jupiter'));

        if (jupiterHouse === 9 && venusHouseFromJup === 4) {
            this.addYoga(createYoga({
                name: 'Khaga Yoga',
                nameKey: 'Khaga',
                category: 'Raja',
                description: 'Jupiter in 9th, Venus 4th from Jupiter. Bird symbol - comfortable, vehicles, servants, happy.',
                descriptionKey: 'Khaga',
                planets: ['Jupiter', 'Venus'],
                nature: 'Benefic',
                strength: 6
            }));
        }
    }

    /**
     * Khadga Yoga (Sword)
     * 9th lord in 2nd, 2nd lord in 9th, Lagna lord in Kendra/Trikona
     */
    _checkKhadgaYoga() {
        const lord2 = this.getHouseLord(2);
        const lord9 = this.getHouseLord(9);
        const lord1 = this.getHouseLord(1);

        const lord9House = this.getHouse(lord9);
        const lord2House = this.getHouse(lord2);
        const lord1House = this.getHouse(lord1);

        const goodHouses = [...kendras, ...trikonas];

        if (lord9House === 2 && lord2House === 9 && goodHouses.includes(lord1House)) {
            this.addYoga(createYoga({
                name: 'Khadga Yoga',
                nameKey: 'Khadga',
                category: 'Raja',
                description: '9th lord in 2nd, 2nd lord in 9th, Lagna lord in Kendra/Trikona. Sword symbol - wealthy, famous, fortunate.',
                descriptionKey: 'Khadga',
                planets: [lord2, lord9, lord1],
                nature: 'Benefic',
                strength: 7
            }));
        }
    }

    /**
     * Kusuma Yoga
     * Venus in fixed Lagna, Moon in 7th, Saturn in 10th
     */
    _checkKusumaYoga() {
        const fixedSigns = [1, 4, 7, 10]; // Taurus, Leo, Scorpio, Aquarius
        const lagnaSign = this.ctx.lagnaRasi;

        const moonHouse = this.getHouse('Moon');
        const saturnHouse = this.getHouse('Saturn');

        if (fixedSigns.includes(lagnaSign) && moonHouse === 7 && saturnHouse === 10) {
            this.addYoga(createYoga({
                name: 'Kusuma Yoga',
                nameKey: 'Kusuma',
                category: 'Raja',
                description: 'Fixed sign Lagna, Moon in 7th, Saturn in 10th. Flower symbol - king, wealthy, happy, long-lived.',
                descriptionKey: 'Kusuma',
                planets: ['Moon', 'Saturn'],
                nature: 'Benefic',
                strength: 7
            }));
        }
    }

    /**
     * Makuta Yoga (Crown)
     * Jupiter 9th from Karakamsa, benefics in Kendras
     */
    _checkMakutaYoga() {
        // Simplified - Jupiter in 9th, benefics in Kendras from Lagna
        const jupiterHouse = this.getHouse('Jupiter');
        const benefics = this.getNaturalBenefics();

        const beneficsInKendras = benefics.filter(p => kendras.includes(this.getHouse(p)));

        if (jupiterHouse === 9 && beneficsInKendras.length >= 2) {
            this.addYoga(createYoga({
                name: 'Makuta Yoga',
                nameKey: 'Makuta',
                category: 'Raja',
                description: 'Jupiter in 9th with benefics in Kendras. Crown symbol - respected leader, good family, prosperous.',
                descriptionKey: 'Makuta',
                planets: ['Jupiter', ...beneficsInKendras],
                nature: 'Benefic',
                strength: 7
            }));
        }
    }

    /**
     * Simhasana Yoga (Lion Throne)
     * 2nd, 4th, 5th, 9th, 10th lords all in Kendras
     */
    _checkSimhasanaYoga() {
        const lords = [
            this.getHouseLord(2),
            this.getHouseLord(4),
            this.getHouseLord(5),
            this.getHouseLord(9),
            this.getHouseLord(10)
        ];

        const uniqueLords = [...new Set(lords)];
        const allInKendras = uniqueLords.every(lord => kendras.includes(this.getHouse(lord)));

        if (allInKendras) {
            this.addYoga(createYoga({
                name: 'Simhasana Yoga',
                nameKey: 'Simhasana',
                category: 'Raja',
                description: 'Lords of 2nd, 4th, 5th, 9th, 10th all in Kendras. Lion throne - king or equal, mighty, famous.',
                descriptionKey: 'Simhasana',
                planets: uniqueLords,
                nature: 'Benefic',
                strength: 9
            }));
        }
    }

    /**
     * Akhanda Samrajya Yoga (Unbroken Empire)
     * Jupiter lord of 2nd/5th/11th, in Kendra, 11th lord strong
     */
    _checkAkhandaSamrajyaYoga() {
        const lord2 = this.getHouseLord(2);
        const lord5 = this.getHouseLord(5);
        const lord11 = this.getHouseLord(11);

        const jupiterIsLord = ['Jupiter'].some(p => p === lord2 || p === lord5 || p === lord11);
        const jupiterInKendra = kendras.includes(this.getHouse('Jupiter'));
        const lord11Strong = this.isStrong(lord11);

        if (jupiterIsLord && jupiterInKendra && lord11Strong) {
            this.addYoga(createYoga({
                name: 'Akhanda Samrajya Yoga',
                nameKey: 'Akhanda_Samrajya',
                category: 'Raja',
                description: 'Jupiter rules 2nd/5th/11th, in Kendra, with strong 11th lord. Unbroken empire - continuous authority, lasting legacy.',
                descriptionKey: 'Akhanda_Samrajya',
                planets: ['Jupiter', lord11],
                nature: 'Benefic',
                strength: 9
            }));
        }
    }

    /**
     * Parvata Yoga (Mountain)
     * Lagna & 12th lords in mutual Kendras, benefics in Kendras
     */
    _checkParvataYoga() {
        const lord1 = this.getHouseLord(1);
        const lord12 = this.getHouseLord(12);

        const lord1InKendra = kendras.includes(this.getHouse(lord1));
        const lord12InKendra = kendras.includes(this.getHouse(lord12));

        const benefics = this.getNaturalBenefics();
        const beneficsInKendras = benefics.filter(p => kendras.includes(this.getHouse(p)));

        if (lord1InKendra && lord12InKendra && beneficsInKendras.length >= 2) {
            this.addYoga(createYoga({
                name: 'Parvata Yoga',
                nameKey: 'Parvata',
                category: 'Raja',
                description: 'Lagna & 12th lords in Kendras with benefics in Kendras. Mountain - wealthy, famous, generous, ruler.',
                descriptionKey: 'Parvata',
                planets: [lord1, lord12, ...beneficsInKendras],
                nature: 'Benefic',
                strength: 8
            }));
        }
    }

    /**
     * Saraswati Yoga
     * Jupiter, Venus, Mercury in Kendras/Trikonas/2nd, Jupiter in own/exalt
     */
    _checkSaraswatiYoga() {
        const goodHouses = [...kendras, ...trikonas, 2];

        const jupHouse = this.getHouse('Jupiter');
        const venHouse = this.getHouse('Venus');
        const merHouse = this.getHouse('Mercury');

        const jupDignity = this.getDignity('Jupiter');
        const jupInDignity = ['Exalted', 'Own', 'Moolatrikona'].includes(jupDignity);

        const allInGoodHouses = goodHouses.includes(jupHouse) &&
            goodHouses.includes(venHouse) &&
            goodHouses.includes(merHouse);

        if (allInGoodHouses && jupInDignity) {
            this.addYoga(createYoga({
                name: 'Saraswati Yoga',
                nameKey: 'Saraswati',
                category: 'Raja',
                description: 'Jupiter, Venus, Mercury in Kendras/Trikonas/2nd with Jupiter in dignity. Goddess of learning - highly educated, skilled in arts, famous scholar.',
                descriptionKey: 'Saraswati',
                planets: ['Jupiter', 'Venus', 'Mercury'],
                nature: 'Benefic',
                strength: 8
            }));
        }
    }

    /**
     * Indra Yoga
     * 5th & 11th lords exchange, Moon conjunct Jupiter
     */
    _checkIndraYoga() {
        const lord5 = this.getHouseLord(5);
        const lord11 = this.getHouseLord(11);

        const lord5House = this.getHouse(lord5);
        const lord11House = this.getHouse(lord11);

        const exchange = lord5House === 11 && lord11House === 5;
        const moonJupConjunct = this.isConjunct('Moon', 'Jupiter');

        if (exchange && moonJupConjunct) {
            this.addYoga(createYoga({
                name: 'Indra Yoga',
                nameKey: 'Indra',
                category: 'Raja',
                description: '5th & 11th lords exchange, Moon conjunct Jupiter. King of gods - fame, authority, many servants, royal pleasures.',
                descriptionKey: 'Indra',
                planets: [lord5, lord11, 'Moon', 'Jupiter'],
                nature: 'Benefic',
                strength: 8
            }));
        }
    }

    /**
     * Brahma Yoga
     * Jupiter in Kendra, Venus in 9th, Mercury in 7th/11th from Venus
     */
    _checkBrahmaYoga() {
        const jupInKendra = kendras.includes(this.getHouse('Jupiter'));
        const venusHouse = this.getHouse('Venus');
        const mercuryHouseFromVenus = this.getHouse('Mercury', this.getRasi('Venus'));

        if (jupInKendra && venusHouse === 9 && [7, 11].includes(mercuryHouseFromVenus)) {
            this.addYoga(createYoga({
                name: 'Brahma Yoga',
                nameKey: 'Brahma',
                category: 'Raja',
                description: 'Jupiter in Kendra, Venus in 9th, Mercury in 7th/11th from Venus. Creator god - supreme knowledge, respected, wealthy.',
                descriptionKey: 'Brahma',
                planets: ['Jupiter', 'Venus', 'Mercury'],
                nature: 'Benefic',
                strength: 8
            }));
        }
    }

    /**
     * Vishnu Yoga
     * 9th lord in 10th, 10th lord in 9th (both exalted is best)
     */
    _checkVishnuYoga() {
        const lord9 = this.getHouseLord(9);
        const lord10 = this.getHouseLord(10);

        const lord9House = this.getHouse(lord9);
        const lord10House = this.getHouse(lord10);

        if (lord9House === 10 && lord10House === 9) {
            const bothExalted = this.getDignity(lord9) === 'Exalted' && this.getDignity(lord10) === 'Exalted';
            const strength = bothExalted ? 10 : 8;

            this.addYoga(createYoga({
                name: 'Vishnu Yoga',
                nameKey: 'Vishnu',
                category: 'Raja',
                description: '9th lord in 10th, 10th lord in 9th. Preserver god - protector, wealthy, long-lived, famous.' +
                    (bothExalted ? ' Both lords exalted - exceptional results.' : ''),
                descriptionKey: 'Vishnu',
                planets: [lord9, lord10],
                nature: 'Benefic',
                strength
            }));
        }
    }

    /**
     * Shiva Yoga
     * 5th lord in 9th, 9th lord in 10th, 10th lord in 5th
     */
    _checkShivaYoga() {
        const lord5 = this.getHouseLord(5);
        const lord9 = this.getHouseLord(9);
        const lord10 = this.getHouseLord(10);

        const lord5House = this.getHouse(lord5);
        const lord9House = this.getHouse(lord9);
        const lord10House = this.getHouse(lord10);

        if (lord5House === 9 && lord9House === 10 && lord10House === 5) {
            this.addYoga(createYoga({
                name: 'Shiva Yoga',
                nameKey: 'Shiva',
                category: 'Raja',
                description: '5th lord in 9th, 9th lord in 10th, 10th lord in 5th. Destroyer/Transformer - spiritual, merchant, authority.',
                descriptionKey: 'Shiva',
                planets: [lord5, lord9, lord10],
                nature: 'Benefic',
                strength: 8
            }));
        }
    }

    /**
     * Shubha Mala Yoga
     * Benefics in 3 consecutive houses
     */
    _checkShubhaMalaYoga() {
        const benefics = this.getNaturalBenefics();
        const beneficHouses = benefics.map(p => this.getHouse(p)).filter(h => h !== -1);

        // Check for any 3 consecutive houses containing benefics
        for (let start = 1; start <= 12; start++) {
            const consecutive = [
                start,
                (start % 12) + 1,
                ((start + 1) % 12) + 1
            ];

            const hasAll = consecutive.every(h => beneficHouses.includes(h));
            if (hasAll) {
                this.addYoga(createYoga({
                    name: 'Shubha Mala Yoga',
                    nameKey: 'Shubha_Mala',
                    category: 'Raja',
                    description: `Benefics in 3 consecutive houses (${consecutive.join(', ')}). Auspicious garland - wealthy, learned, respected.`,
                    descriptionKey: 'Shubha_Mala',
                    planets: benefics.filter(p => consecutive.includes(this.getHouse(p))),
                    nature: 'Benefic',
                    strength: 7
                }));
                break;
            }
        }
    }
}

export default RajaYogas;
