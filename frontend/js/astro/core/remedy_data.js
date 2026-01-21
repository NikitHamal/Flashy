/**
 * ============================================================================
 * VEDIC REMEDY DATA - Comprehensive Knowledge Base
 * ============================================================================
 * 
 * Centralized repository for all Vedic Astrological remedies categorized by:
 * - Gemstones (Ratna) with alternatives
 * - Mantras (Beej, Gayatri & Stotra)
 * - Charity (Daana)
 * - Fasting (Vrata)
 * - Rituals (Puja/Shanti)
 * - Yantras
 * - Rudraksha
 * - Lifestyle (Yama/Niyama)
 * - Dosha-specific remedies
 */

export const REMEDY_DATA = {
    planets: {
        Sun: {
            gemstone: {
                primary: "Ruby (Manik)",
                nameKey: "Ruby",
                alternates: ["RedGarnet", "RedSpinel", "Sunstone"],
                weight: "3-6",
                metal: "Gold or Copper",
                metalKey: "GoldCopper",
                finger: "Ring finger (Right hand)",
                fingerKey: "Ring_Right",
                day: "Sunday",
                dayKey: "Sunday",
                nakshatra: "Pushya, Uttara Phalguni, Uttara Ashadha",
                timing: "Within 1 hour of sunrise"
            },
            mantra: {
                beej: "Om Hraam Hreem Hroum Sah Suryaya Namah",
                beej_np: "ॐ ह्रां ह्रीं ह्रौं सः सूर्याय नमः",
                gayatri: "Om Adityaya Vidmahe Martandaya Dheemahi Tanno Surya Prachodayat",
                gayatri_np: "ॐ आदित्याय विद्महे मार्तण्डाय धीमहि तन्नो सूर्यः प्रचोदयात्",
                stotra: "Aditya Hridayam Stotram",
                tantric: "Om Hram Hrim Hraum Sah Suryaya Namah",
                count: 7000,
                dailyMin: 108,
                japaDay: "Sunday"
            },
            yantra: {
                name: "Surya Yantra",
                metal: "Copper or Gold",
                placement: "East wall facing West"
            },
            rudraksha: {
                mukhi: 12,
                alternate: 1,
                ruling: "Surya (Sun)"
            },
            charity: {
                items: ["Wheat", "Copper vessel", "Ruby", "Red flowers", "Jaggery", "Gold", "Saffron"],
                itemKeys: ["Wheat", "CopperVessel", "Ruby", "RedFlowers", "Jaggery", "Gold", "Saffron"],
                recipient: "Father figures, Government servants, Priests",
                recipientKey: "FatherGovtPriests",
                day: "Sunday before noon",
                dayKey: "Sunday",
                direction: "East"
            },
            fasting: {
                day: "Sundays",
                food: "Single meal without salt after sunset",
                duration: "Minimum 11 Sundays"
            },
            puja: ["Surya Namaskar (12 rounds)", "Aditya Hridayam Path", "Surya Shanti Puja"],
            temple: "Sun temples - Konark, Modhera, Suryanaar Kovil",
            deity: "Lord Shiva, Surya Narayana, Lord Rama",
            color: "Red, Orange, Copper, Saffron",
            direction: "East",
            bodyPart: "Heart, Eyes, Bones, Right eye",
            metal: "Gold, Copper"
        },
        Moon: {
            gemstone: {
                primary: "Pearl (Moti)",
                nameKey: "Pearl",
                alternates: ["Moonstone", "WhiteCoral", "WhiteSapphire"],
                weight: "4-6",
                metal: "Silver",
                metalKey: "Silver",
                finger: "Little finger or Ring finger (Right hand)",
                fingerKey: "Little_Ring_Right",
                day: "Monday",
                dayKey: "Monday",
                nakshatra: "Rohini, Hasta, Shravana",
                timing: "During Shukla Paksha, evening time"
            },
            mantra: {
                beej: "Om Shram Shreem Shroum Sah Chandraya Namah",
                beej_np: "ॐ श्रां श्रीं श्रौं सः चन्द्राय नमः",
                gayatri: "Om Nisakaraya Vidmahe Kalannathaya Dheemahi Tanno Chandra Prachodayat",
                gayatri_np: "ॐ निसाकराय विद्महे कलन्नाथाय धीमहि तन्नो चन्द्रः प्रचोदयात्",
                stotra: "Chandra Kavacham",
                tantric: "Om Som Somaya Namah",
                count: 11000,
                dailyMin: 108,
                japaDay: "Monday"
            },
            yantra: {
                name: "Chandra Yantra",
                metal: "Silver",
                placement: "Northwest corner"
            },
            rudraksha: {
                mukhi: 2,
                alternate: 9,
                ruling: "Chandra (Moon)"
            },
            charity: {
                items: ["Rice", "Milk", "Silver", "Pearl", "White cloth", "Sugar", "Water", "Curd", "Camphor"],
                itemKeys: ["Rice", "Milk", "Silver", "Pearl", "WhiteCloth", "Sugar", "Water", "Curd", "Camphor"],
                recipient: "Mother figures, Women, the Needy",
                recipientKey: "MotherWomenNeedy",
                day: "Monday evening",
                dayKey: "Monday",
                direction: "Northwest"
            },
            fasting: {
                day: "Mondays",
                food: "White foods only - milk, rice, curd",
                duration: "Minimum 11 Mondays or during Shravan month"
            },
            puja: ["Chandra Shanti Puja", "Durga Puja", "Somvar Vrat Katha"],
            temple: "Somnath Temple, Chandreshwar Temple",
            deity: "Goddess Parvati, Goddess Gauri, Lord Shiva",
            color: "White, Silver, Light Blue, Cream",
            direction: "Northwest",
            bodyPart: "Mind, Blood, Left eye, Breasts, Stomach",
            metal: "Silver"
        },
        Mars: {
            gemstone: {
                primary: "Red Coral (Moonga)",
                nameKey: "Coral",
                alternates: ["Carnelian", "RedJasper", "Bloodstone"],
                weight: "5-9",
                metal: "Gold or Copper",
                metalKey: "GoldCopper",
                finger: "Ring finger (Right hand)",
                fingerKey: "Ring_Right",
                day: "Tuesday",
                dayKey: "Tuesday",
                nakshatra: "Mrigashira, Chitra, Dhanishta",
                timing: "Within 1 hour of sunrise"
            },
            mantra: {
                beej: "Om Kraam Kreem Kroum Sah Bhaumaya Namah",
                beej_np: "ॐ क्रां क्रीं क्रौं सः भौमाय नमः",
                gayatri: "Om Angarkaya Vidmahe Sakti Hastaya Dheemahi Tanno Bhouma Prachodayat",
                gayatri_np: "ॐ अङ्गारकाय विद्महे शक्तिहस्ताय धीमहि तन्नो भौमः प्रचोदयात्",
                stotra: "Mangala Chandika Stotra",
                tantric: "Om Kum Kujaya Namah",
                count: 10000,
                dailyMin: 108,
                japaDay: "Tuesday"
            },
            yantra: {
                name: "Mangal Yantra",
                metal: "Copper",
                placement: "South wall"
            },
            rudraksha: {
                mukhi: 3,
                alternate: 11,
                ruling: "Mangal (Mars)"
            },
            charity: {
                items: ["Red lentils (Masoor Dal)", "Copper", "Red cloth", "Jaggery", "Sandalwood", "Red flowers", "Wheat bread"],
                itemKeys: ["RedLentils", "Copper", "RedCloth", "Jaggery", "Sandalwood", "RedFlowers", "WheatBread"],
                recipient: "Brothers, Soldiers, Athletes",
                recipientKey: "BrothersSoldiersAthletes",
                day: "Tuesday before noon",
                dayKey: "Tuesday",
                direction: "South"
            },
            fasting: {
                day: "Tuesdays",
                food: "Single meal, avoid salt and grains",
                duration: "Minimum 21 Tuesdays"
            },
            puja: ["Mangal Shanti Puja", "Hanuman Chalisa (7 times)", "Rudrabhishek"],
            temple: "Mangalnath Temple Ujjain, Hanuman Temples",
            deity: "Lord Hanuman, Lord Kartikeya, Goddess Durga",
            color: "Bright Red, Coral, Scarlet",
            direction: "South",
            bodyPart: "Blood, Muscles, Bone marrow, Head",
            metal: "Copper, Brass"
        },
        Mercury: {
            gemstone: {
                primary: "Emerald (Panna)",
                nameKey: "Emerald",
                alternates: ["GreenTourmaline", "Peridot", "GreenJade", "Tsavorite"],
                weight: "3-6",
                metal: "Gold",
                metalKey: "Gold",
                finger: "Little finger (Right hand)",
                fingerKey: "Little_Right",
                day: "Wednesday",
                dayKey: "Wednesday",
                nakshatra: "Ashlesha, Jyeshtha, Revati",
                timing: "Within 2 hours of sunrise"
            },
            mantra: {
                beej: "Om Braam Breem Broum Sah Budhaya Namah",
                beej_np: "ॐ ब्रां ब्रीं ब्रौं सः बुधाय नमः",
                gayatri: "Om Budhaya Vidmahe Chandraputraya Dheemahi Tanno Budha Prachodayat",
                gayatri_np: "ॐ बुधाय विद्महे चन्द्रपुत्राय धीमहि तन्नो बुधः प्रचोदयात्",
                stotra: "Budha Kavacham",
                tantric: "Om Bum Budhaya Namah",
                count: 9000,
                dailyMin: 108,
                japaDay: "Wednesday"
            },
            yantra: {
                name: "Budh Yantra",
                metal: "Bronze or Gold",
                placement: "North wall"
            },
            rudraksha: {
                mukhi: 4,
                alternate: 10,
                ruling: "Budh (Mercury)"
            },
            charity: {
                items: ["Green moong dal", "Green cloth", "Emerald", "Vegetables", "Ivory", "Flowers", "Bronze utensils"],
                itemKeys: ["GreenMoong", "GreenCloth", "Emerald", "Vegetables", "Ivory", "Flowers", "BronzeUtensils"],
                recipient: "Students, Scholars, Orphans",
                recipientKey: "StudentsScholarsOrphans",
                day: "Wednesday morning",
                dayKey: "Wednesday",
                direction: "North"
            },
            fasting: {
                day: "Wednesdays",
                food: "Green vegetables, single meal",
                duration: "Minimum 21 Wednesdays"
            },
            puja: ["Budh Shanti Puja", "Vishnu Sahasranama", "Ganesha Puja"],
            temple: "Budh temples, Ganesha temples",
            deity: "Lord Ganesha, Lord Vishnu, Lord Krishna",
            color: "Green, Light Green, Parrot Green",
            direction: "North",
            bodyPart: "Nervous system, Skin, Speech, Lungs",
            metal: "Bronze, Brass"
        },
        Jupiter: {
            gemstone: {
                primary: "Yellow Sapphire (Pukhraj)",
                nameKey: "SapphireY",
                alternates: ["YellowTopaz", "Citrine", "YellowBeryl", "Heliodor"],
                weight: "3-7",
                metal: "Gold",
                metalKey: "Gold",
                finger: "Index finger (Right hand)",
                fingerKey: "Index_Right",
                day: "Thursday",
                dayKey: "Thursday",
                nakshatra: "Punarvasu, Vishakha, Purva Bhadrapada",
                timing: "Within 1 hour of sunrise"
            },
            mantra: {
                beej: "Om Graam Greem Groum Sah Gurave Namah",
                beej_np: "ॐ ग्रां ग्रीं ग्रौं सः गुरवे नमः",
                gayatri: "Om Guru Devaya Vidmahe Parabrahmane Dheemahi Tanno Guruh Prachodayat",
                gayatri_np: "ॐ गुरुदेवाय विद्महे परब्रह्मणे धीमहि तन्नो गुरुः प्रचोदयात्",
                stotra: "Guru Kavacham, Brihaspati Stotra",
                tantric: "Om Brim Brihaspataye Namah",
                count: 19000,
                dailyMin: 108,
                japaDay: "Thursday"
            },
            yantra: {
                name: "Guru Yantra / Brihaspati Yantra",
                metal: "Gold or Brass",
                placement: "Northeast (Ishaan) corner"
            },
            rudraksha: {
                mukhi: 5,
                alternate: 11,
                ruling: "Brihaspati (Jupiter)"
            },
            charity: {
                items: ["Chana Dal", "Turmeric", "Gold", "Yellow cloth", "Honey", "Books", "Bananas", "Ghee"],
                itemKeys: ["ChanaDal", "Turmeric", "Gold", "YellowCloth", "Honey", "Books", "Bananas", "Ghee"],
                recipient: "Brahmins, Teachers, Gurus, Priests",
                recipientKey: "BrahminsTeachersGurus",
                day: "Thursday morning",
                dayKey: "Thursday",
                direction: "Northeast"
            },
            fasting: {
                day: "Thursdays",
                food: "Single meal, yellow foods only",
                duration: "Minimum 16 Thursdays"
            },
            puja: ["Brihaspati Shanti Puja", "Satyanarayan Katha", "Vishnu Puja"],
            temple: "Brihaspati temples, Vishnu temples, Tirupati",
            deity: "Lord Vishnu, Lord Brahma, Dakshinamurthy",
            color: "Yellow, Golden, Saffron, Mustard",
            direction: "Northeast",
            bodyPart: "Liver, Fat, Thighs, Arterial system",
            metal: "Gold"
        },
        Venus: {
            gemstone: {
                primary: "Diamond (Heera)",
                nameKey: "Diamond",
                alternates: ["WhiteSapphire", "Zircon", "WhiteTopaz", "CrystalQuartz"],
                weight: "1-1.5",
                metal: "Platinum, White Gold, or Silver",
                metalKey: "PlatinumWhiteGoldSilver",
                finger: "Middle or Little finger (Right hand)",
                fingerKey: "Middle_Little_Right",
                day: "Friday",
                dayKey: "Friday",
                nakshatra: "Bharani, Purva Phalguni, Purva Ashadha",
                timing: "Morning, within 2 hours of sunrise"
            },
            mantra: {
                beej: "Om Draam Dreem Droum Sah Shukraya Namah",
                beej_np: "ॐ द्रां द्रीं द्रौं सः शुक्राय नमः",
                gayatri: "Om Shukraya Vidmahe Bhargavaya Dheemahi Tanno Shukra Prachodayat",
                gayatri_np: "ॐ शुक्राय विद्महे भार्गवाय धीमहि तन्नो शुक्रः प्रचोदयात्",
                stotra: "Shukra Kavacham",
                tantric: "Om Shum Shukraya Namah",
                count: 16000,
                dailyMin: 108,
                japaDay: "Friday"
            },
            yantra: {
                name: "Shukra Yantra",
                metal: "Silver or Platinum",
                placement: "Southeast corner"
            },
            rudraksha: {
                mukhi: 6,
                alternate: 13,
                ruling: "Shukra (Venus)"
            },
            charity: {
                items: ["Rice", "Curd", "Silver", "White cloth", "Perfumes", "Ghee", "Camphor", "White sweets", "Silk"],
                itemKeys: ["Rice", "Curd", "Silver", "WhiteCloth", "Perfumes", "Ghee", "Camphor", "WhiteSweets", "Silk"],
                recipient: "Young women, Artists, Musicians",
                recipientKey: "YoungWomenArtists",
                day: "Friday evening",
                dayKey: "Friday",
                direction: "Southeast"
            },
            fasting: {
                day: "Fridays",
                food: "White foods - milk, rice, kheer",
                duration: "Minimum 21 Fridays"
            },
            puja: ["Shukra Shanti Puja", "Lakshmi Puja", "Santoshi Mata Vrat"],
            temple: "Lakshmi temples, Mahalakshmi Temple Kolhapur",
            deity: "Goddess Lakshmi, Goddess Annapurna",
            color: "White, Cream, Light Pink, Variegated",
            direction: "Southeast",
            bodyPart: "Reproductive organs, Face, Skin, Eyes",
            metal: "Silver, Platinum"
        },
        Saturn: {
            gemstone: {
                primary: "Blue Sapphire (Neelam)",
                nameKey: "SapphireB",
                alternates: ["Amethyst", "LapisLazuli", "BlueSpinel", "Iolite"],
                weight: "4-7",
                metal: "Iron (Panch-dhatu), Silver",
                metalKey: "IronSilver",
                finger: "Middle finger (Right hand)",
                fingerKey: "Middle_Right",
                day: "Saturday",
                dayKey: "Saturday",
                nakshatra: "Pushya, Anuradha, Uttara Bhadrapada",
                timing: "Evening, 2 hours before sunset",
                caution: "Must trial for 7 days before permanent wear"
            },
            mantra: {
                beej: "Om Praam Preem Proum Sah Shanaye Namah",
                beej_np: "ॐ प्रां प्रीं प्रौं सः शनये नमः",
                gayatri: "Om Sanaischaraya Vidmahe Sooryaputraya Dheemahi Tanno Manda Prachodayat",
                gayatri_np: "ॐ शनैश्चराय विद्महे सूर्यपुत्राय धीमहि तन्नो मन्दः प्रचोदयात्",
                stotra: "Shani Chalisa, Dasharatha Shani Stotra",
                tantric: "Om Sham Shanaishcharaya Namah",
                count: 23000,
                dailyMin: 108,
                japaDay: "Saturday"
            },
            yantra: {
                name: "Shani Yantra",
                metal: "Iron or Lead",
                placement: "West wall"
            },
            rudraksha: {
                mukhi: 7,
                alternate: 14,
                ruling: "Shani (Saturn)"
            },
            charity: {
                items: ["Black sesame (Til)", "Mustard oil", "Iron", "Black cloth", "Leather shoes", "Blankets", "Black gram"],
                itemKeys: ["BlackSesame", "MustardOil", "Iron", "BlackCloth", "LeatherShoes", "Blankets", "BlackGram"],
                recipient: "Servants, Laborers, Disabled, Elderly",
                recipientKey: "ServantsLaborersDisabled",
                day: "Saturday evening",
                dayKey: "Saturday",
                direction: "West"
            },
            fasting: {
                day: "Saturdays",
                food: "Black sesame, single meal after sunset",
                duration: "Minimum 51 Saturdays"
            },
            puja: ["Shani Shanti Puja", "Shani Tailabhishek", "Hanuman Puja"],
            temple: "Shani Shingnapur, Thirunallar",
            deity: "Lord Shani, Lord Hanuman, Lord Bhairava",
            color: "Blue, Black, Dark Blue, Indigo",
            direction: "West",
            bodyPart: "Legs, Teeth, Bones, Knees, Nervous system",
            metal: "Iron, Lead"
        },
        Rahu: {
            gemstone: {
                primary: "Hessonite (Gomed)",
                nameKey: "Hessonite",
                alternates: ["OrangeZircon", "SpessartiteGarnet"],
                weight: "6-8",
                metal: "Ashtadhatu (8 metals) or Silver",
                metalKey: "AshtadhatuSilver",
                finger: "Middle finger (Right hand)",
                fingerKey: "Middle_Right",
                day: "Saturday",
                dayKey: "Saturday",
                nakshatra: "Ardra, Swati, Shatabhisha",
                timing: "Evening or Night time during Rahu Kaal"
            },
            mantra: {
                beej: "Om Bhraam Bhreem Bhroum Sah Rahave Namah",
                beej_np: "ॐ भ्रां भ्रीं भ्रौं सः राहवे नमः",
                gayatri: "Om Sookdantaya Vidmahe Ugraroopaya Dheemahi Tanno Rahu Prachodayat",
                gayatri_np: "ॐ सुकदन्ताय विद्महे उग्ररूपाय धीमहि तन्नो राहुः प्रचोदयात्",
                stotra: "Rahu Kavacham",
                tantric: "Om Ram Rahave Namah",
                count: 18000,
                dailyMin: 108,
                japaDay: "Saturday or Wednesday"
            },
            yantra: {
                name: "Rahu Yantra",
                metal: "Ashtadhatu or Lead",
                placement: "Southwest corner"
            },
            rudraksha: {
                mukhi: 8,
                alternate: 18,
                ruling: "Rahu"
            },
            charity: {
                items: ["Black gram (Urad)", "Lead", "Mustard oil", "Blue cloth", "Blankets", "Coconut", "Radish"],
                itemKeys: ["BlackGram", "Lead", "MustardOil", "BlueCloth", "Blankets", "Coconut", "Radish"],
                recipient: "Outcasts, Sweepers, Leprosy patients",
                recipientKey: "OutcastsSweepersLeprosy",
                day: "Saturday evening or Wednesday",
                dayKey: "Saturday_Wednesday",
                direction: "Southwest"
            },
            fasting: {
                day: "Saturdays",
                food: "Black sesame, avoid non-veg",
                duration: "Minimum 18 Saturdays"
            },
            puja: ["Rahu Shanti Puja", "Kaal Sarp Dosh Nivaran", "Durga Saptashati Path"],
            temple: "Rahu Ketu temples - Kalahasti, Thirunageswaram",
            deity: "Goddess Durga, Saraswati, Lord Bhairava",
            color: "Smoke Grey, Ultraviolet, Dark Blue",
            direction: "Southwest",
            bodyPart: "Head (upper), Breathing, Skin diseases",
            metal: "Lead, Ashtadhatu"
        },
        Ketu: {
            gemstone: {
                primary: "Cat's Eye (Lehsuniya/Vaidurya)",
                nameKey: "CatsEye",
                alternates: ["TigersEye", "Apatite", "Chrysoberyl"],
                weight: "5-7",
                metal: "Silver or Panch-dhatu",
                metalKey: "SilverPanchdhatu",
                finger: "Little or Middle finger (Right hand)",
                fingerKey: "Little_Middle_Right",
                day: "Tuesday or Saturday",
                dayKey: "Tuesday_Saturday",
                nakshatra: "Ashwini, Magha, Moola",
                timing: "2 hours after sunrise"
            },
            mantra: {
                beej: "Om Straam Streem Stroum Sah Ketave Namah",
                beej_np: "ॐ स्त्रां स्त्रीं स्त्रौं सः केतवे नमः",
                gayatri: "Om Chitravarnaya Vidmahe Sarparoopaya Dheemahi Tanno Ketu Prachodayat",
                gayatri_np: "ॐ चित्रवर्णाय विद्महे सर्परूपाय धीमहि तन्नो केतुः प्रचोदयात्",
                stotra: "Ketu Kavacham",
                tantric: "Om Kem Ketave Namah",
                count: 17000,
                dailyMin: 108,
                japaDay: "Tuesday"
            },
            yantra: {
                name: "Ketu Yantra",
                metal: "Silver or Ashtadhatu",
                placement: "Flag post (Dhwaja)"
            },
            rudraksha: {
                mukhi: 9,
                alternate: 18,
                ruling: "Ketu"
            },
            charity: {
                items: ["Horse gram (Kulthi)", "Seven grains", "Multi-colored cloth", "Blanket", "Dog food", "Sesame"],
                itemKeys: ["HorseGram", "SevenGrains", "MultiCloth", "Blanket", "DogFood", "Sesame"],
                recipient: "Dogs, Brahmins, Ascetics",
                recipientKey: "DogsBrahminsAscetics",
                day: "Tuesday or Sunday",
                dayKey: "Tuesday_Sunday",
                direction: "Southwest"
            },
            fasting: {
                day: "Tuesdays or Saturdays",
                food: "Single meal, avoid non-veg",
                duration: "Minimum 21 days"
            },
            puja: ["Ketu Shanti Puja", "Ganesha Puja", "Matsya Avatar Puja"],
            temple: "Ketu temples - Kalahasti, Keezhaperumpallam",
            deity: "Lord Ganesha, Matsya Avatar, Lord Bhairava",
            color: "Grey, Smoky, Earthy browns",
            direction: "Southwest (downward)",
            bodyPart: "Feet, Skin, Claws, Spine",
            metal: "Iron, Lead"
        }
    },

    // Dosha-specific Remedies
    doshas: {
        manglikDosha: {
            description: "Mars in 1st, 4th, 7th, 8th, or 12th house from Lagna/Moon",
            severity: {
                mild: ["Mars in own sign", "Mars aspected by benefics"],
                moderate: ["Mars in neutral signs"],
                severe: ["Mars in 7th or 8th", "Mars conjunct malefics"]
            },
            remedies: {
                general: [
                    "Marry after 28 years of age",
                    "Kumbh Vivah (marriage with pot/tree)",
                    "Mangal Dosha matching with partner"
                ],
                mantras: ["Hanuman Chalisa daily", "Mangal Beej Mantra 10000 times"],
                puja: ["Mangal Shanti Puja", "Navagraha Shanti"],
                fasting: "Tuesday fasting for 21 weeks",
                charity: "Donate red items on Tuesdays",
                gemstone: "Red Coral after consultation"
            }
        },
        kaalSarpDosha: {
            description: "All planets hemmed between Rahu and Ketu",
            types: {
                ascending: "Rahu at head (Savya Kaal Sarp)",
                descending: "Ketu at head (Apasavya Kaal Sarp)"
            },
            remedies: {
                mantras: [
                    "Maha Mrityunjaya Mantra 1.25 lakh times",
                    "Rahu-Ketu beej mantras"
                ],
                puja: [
                    "Kaal Sarp Dosh Nivaran Puja at Trimbakeshwar",
                    "Nagbali Puja",
                    "Rahu Ketu Shanti"
                ],
                temple: "Visit Kalahasti, Trimbakeshwar",
                fasting: "Nag Panchami vrat",
                charity: "Feed snakes' images milk, donate blankets"
            }
        },
        pitraDosha: {
            description: "Afflictions indicating ancestral karmic debts",
            indicators: [
                "Sun afflicted by Rahu/Ketu/Saturn",
                "9th house affliction",
                "Jupiter afflicted"
            ],
            remedies: {
                general: [
                    "Perform Shraddha rituals annually",
                    "Pind Daan at Gaya",
                    "Tarpan on Amavasya"
                ],
                mantras: ["Pitra Gayatri Mantra", "Mahamrityunjaya for ancestors"],
                puja: ["Narayan Nagbali at Trimbakeshwar", "Tripindi Shraddha"],
                charity: "Feed Brahmins, crows, dogs on Amavasya"
            }
        },
        sadesati: {
            description: "Saturn's 7.5 year transit over natal Moon",
            phases: {
                rising: "Saturn in 12th from Moon - Mental stress",
                peak: "Saturn over Moon - Physical challenges",
                setting: "Saturn in 2nd from Moon - Financial issues"
            },
            remedies: {
                mantras: ["Hanuman Chalisa daily", "Shani Beej Mantra"],
                puja: ["Shani Tailabhishek every Saturday"],
                fasting: "Saturday fasting",
                charity: "Oil, iron, black items on Saturdays",
                temple: "Visit Shani temples on Saturdays"
            }
        }
    },

    // Nakshatra-based Quick Remedies
    nakshatraRemedies: {
        Ashwini: { deity: "Ashwini Kumars", remedy: "Worship twins, donate medicines" },
        Bharani: { deity: "Yama", remedy: "Shanti karma, respect for ancestors" },
        Krittika: { deity: "Agni", remedy: "Havan, fire rituals, donate ghee" },
        Rohini: { deity: "Brahma", remedy: "Creative pursuits, Moon remedies" },
        Mrigashira: { deity: "Soma", remedy: "Moon worship, white flower offerings" },
        Ardra: { deity: "Rudra", remedy: "Rudra abhishek, Shiva worship" },
        Punarvasu: { deity: "Aditi", remedy: "Mother worship, Jupiter remedies" },
        Pushya: { deity: "Brihaspati", remedy: "Guru puja, donate to teachers" },
        Ashlesha: { deity: "Nagas", remedy: "Nag puja, Sarpa dosha shanti" },
        Magha: { deity: "Pitras", remedy: "Ancestor worship, Shraddha" },
        PurvaPhalguni: { deity: "Bhaga", remedy: "Lakshmi puja, Venus remedies" },
        UttaraPhalguni: { deity: "Aryaman", remedy: "Sun worship, marital harmony" },
        Hasta: { deity: "Savitar", remedy: "Surya puja, skill development" },
        Chitra: { deity: "Vishwakarma", remedy: "Creative worship, Mars balance" },
        Swati: { deity: "Vayu", remedy: "Hanuman puja, Rahu remedies" },
        Vishakha: { deity: "Indragni", remedy: "Fire rituals, Jupiter-Mars balance" },
        Anuradha: { deity: "Mitra", remedy: "Friendship karma, Saturn remedies" },
        Jyeshtha: { deity: "Indra", remedy: "Leadership qualities, Mercury remedies" },
        Moola: { deity: "Niritti", remedy: "Ketu shanti, root cause healing" },
        PurvaAshadha: { deity: "Apas", remedy: "Water rituals, Venus remedies" },
        UttaraAshadha: { deity: "Vishwe Devas", remedy: "Sun remedies, victory puja" },
        Shravana: { deity: "Vishnu", remedy: "Vishnu worship, learning" },
        Dhanishta: { deity: "Vasus", remedy: "Wealth rituals, Mars remedies" },
        Shatabhisha: { deity: "Varuna", remedy: "Water offerings, Rahu remedies" },
        PurvaBhadrapada: { deity: "Ajaikapada", remedy: "Spiritual practices, Jupiter remedies" },
        UttaraBhadrapada: { deity: "Ahirbudhnya", remedy: "Saturn remedies, serpent worship" },
        Revati: { deity: "Pushan", remedy: "Mercury remedies, travel blessings" }
    },

    // General Remedies by House Affliction
    houseRemedies: {
        1: { issue: "Self/Health", remedy: "Sun remedies, self-improvement" },
        2: { issue: "Wealth/Speech", remedy: "Jupiter remedies, honest speech" },
        3: { issue: "Siblings/Courage", remedy: "Mars remedies, communication" },
        4: { issue: "Mother/Property", remedy: "Moon remedies, serve mother" },
        5: { issue: "Children/Education", remedy: "Jupiter remedies, Santana Gopala" },
        6: { issue: "Enemies/Health", remedy: "Mars/Saturn remedies, service" },
        7: { issue: "Marriage/Partnership", remedy: "Venus remedies, Gauri puja" },
        8: { issue: "Longevity/Hidden", remedy: "Saturn remedies, Mahamrityunjaya" },
        9: { issue: "Fortune/Father", remedy: "Jupiter/Sun remedies, Dharma" },
        10: { issue: "Career/Status", remedy: "Saturn/Sun remedies, karma yoga" },
        11: { issue: "Gains/Friends", remedy: "Jupiter remedies, charity" },
        12: { issue: "Liberation/Losses", remedy: "Ketu remedies, spiritual practices" }
    },

    // Universal Protective Mantras
    universalMantras: {
        protection: "Om Namah Shivaya",
        obstacles: "Om Gam Ganapataye Namah",
        health: "Om Tryambakam Yajamahe Sugandhim Pushtivardhanam",
        prosperity: "Om Shreem Hreem Shreem Kamale Kamalalaye Praseedha Praseedha",
        peace: "Om Shanti Shanti Shantihi"
    }
};

export default REMEDY_DATA;