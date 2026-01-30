"""
Political Regime Classifications

Based on HRF's political regime classifications document.
Countries marked with * have notes/special considerations.

Categories:
- democratic: Open democratic societies
- hybrid_authoritarian: Hybrid authoritarian regimes
- fully_authoritarian: Fully authoritarian regimes
- unclassified: Countries with special situations (e.g., Haiti)
"""

# The Americas
AMERICAS_DEMOCRATIC = [
    "Argentina",
    "Belize",
    "Brazil",
    "Canada",
    "Chile",
    "Colombia",
    "Costa Rica",
    "Dominican Republic",  # *
    "Ecuador",
    "Guatemala",  # *
    "Guyana",
    "Jamaica",  # *
    "Mexico",
    "Panama",
    "Paraguay",
    "Peru",
    "Suriname",
    "United States of America",
    "United States",
    "USA",
    "Uruguay",
    # Caribbean Nations *
    "Saint Kitts and Nevis",
    "Dominica",
    "Antigua and Barbuda",
    "Saint Vincent and the Grenadines",
    "Grenada",
    "St Lucia",
    "Saint Lucia",
    "Barbados",
    "Bahamas",
    "Trinidad and Tobago",
]

AMERICAS_HYBRID_AUTHORITARIAN = [
    "Bolivia",
    "El Salvador",
    "Honduras",
]

AMERICAS_FULLY_AUTHORITARIAN = [
    "Cuba",
    "Nicaragua",
    "Venezuela",
]

AMERICAS_UNCLASSIFIED = [
    "Haiti",  # Currently not classified due to ongoing crisis
]

# Middle East and North Africa
MENA_DEMOCRATIC = [
    "Israel",  # *
]

MENA_HYBRID_AUTHORITARIAN = [
    "Iraq",
    "Lebanon",
]

MENA_FULLY_AUTHORITARIAN = [
    "Algeria",
    "Bahrain",
    "Egypt",
    "Iran",
    "Jordan",
    "Kuwait",
    "Libya",
    "Morocco",
    "Oman",
    "Qatar",
    "Saudi Arabia",
    "Syria",
    "Tunisia",
    "United Arab Emirates",
    "UAE",
    "Yemen",
]

# Europe and Central Asia
EUROPE_DEMOCRATIC = [
    "Albania",
    "Armenia",
    "Austria",
    "Belgium",
    "Bosnia and Herzegovina",
    "Bulgaria",
    "Croatia",
    "Czech Republic",
    "Czechia",
    "Cyprus",
    "Denmark",
    "Estonia",
    "Finland",
    "France",
    "Germany",
    "Greece",
    "Iceland",
    "Ireland",
    "Italy",
    "Latvia",
    "Lithuania",
    "Luxembourg",  # *
    "Moldova",
    "Montenegro",
    "Kosovo",
    "North Macedonia",
    "Netherlands",
    "Norway",
    "Poland",
    "Portugal",
    "Romania",
    "Sweden",
    "Switzerland",
    "Slovakia",
    "Slovenia",
    "Spain",
    "Ukraine",
    "United Kingdom",
    "UK",
    "Britain",
    "Great Britain",
    # European Microstates *
    "San Marino",
    "Monaco",
    "Liechtenstein",
    "Andorra",
    "Malta",
]

EUROPE_HYBRID_AUTHORITARIAN = [
    "Georgia",
    "Hungary",
    "Serbia",
]

EUROPE_FULLY_AUTHORITARIAN = [
    "Azerbaijan",
    "Belarus",
    "Kazakhstan",
    "Russia",
    "Russian Federation",
    "Tajikistan",
    "Turkmenistan",
    "Turkey",
    "Uzbekistan",
    "Kyrgyzstan",
]

# Asia-Pacific
ASIA_PACIFIC_DEMOCRATIC = [
    "Australia",
    "Bhutan",
    "Japan",
    "Mongolia",
    "Nepal",
    "New Zealand",
    "Papua New Guinea",
    "South Korea",
    "Republic of Korea",
    "Taiwan",
    "Timor-Leste",
    "East Timor",
    "Sri Lanka",
    # Pacific Island Nations *
    "Micronesia",
    "Tuvalu",
    "Nauru",
    "Palau",
    "Marshall Islands",
    "Tonga",
    "Kiribati",
    "Samoa",
    "Vanuatu",
    "Solomon Islands",
]

ASIA_PACIFIC_HYBRID_AUTHORITARIAN = [
    "Bangladesh",  # *
    "Fiji",
    "India",
    "Malaysia",
    "Maldives",
    "Pakistan",
    "Philippines",
    "Singapore",
    "Thailand",
    "Indonesia",
]

ASIA_PACIFIC_FULLY_AUTHORITARIAN = [
    "Afghanistan",
    "Brunei",
    "Burma",
    "Myanmar",
    "Cambodia",
    "China",
    "PRC",
    "People's Republic of China",
    "Laos",
    "North Korea",
    "DPRK",
    "Democratic People's Republic of Korea",
    "Vietnam",
]

# Africa
AFRICA_DEMOCRATIC = [
    "Botswana",
    "Ghana",
    "Lesotho",
    "Liberia",
    "Namibia",
    "South Africa",
    # African Island Nations *
    "Cape Verde",
    "Cabo Verde",
    "Mauritius",
    "Sao Tome and Principe",
    "Seychelles",
]

AFRICA_HYBRID_AUTHORITARIAN = [
    "Benin",  # *
    "Côte d'Ivoire",
    "Cote d'Ivoire",
    "Ivory Coast",
    "The Gambia",
    "Gambia",
    "Kenya",
    "Madagascar",
    "Malawi",
    "Senegal",
    "Sierra Leone",
    "Togo",  # *
    "Zambia",
]

AFRICA_FULLY_AUTHORITARIAN = [
    "Angola",
    "Burundi",
    "Burkina Faso",
    "Cameroon",
    "Central African Republic",
    "CAR",
    "Chad",
    "Comoros",
    "Democratic Republic of Congo",
    "DRC",
    "DR Congo",
    "Congo-Kinshasa",
    "Djibouti",
    "Equatorial Guinea",  # *
    "Eritrea",
    "Ethiopia",
    "Gabon",  # *
    "Guinea",
    "Guinea-Bissau",
    "Mali",
    "Mauritania",
    "Mozambique",
    "Niger",
    "Nigeria",
    "Republic of Congo",  # * (Brazzaville)
    "Congo-Brazzaville",
    "Rwanda",
    "Somalia",  # *
    "South Sudan",
    "Sudan",
    "Swaziland",
    "Eswatini",
    "Uganda",
    "Tanzania",  # *
    "Zimbabwe",
]

# Aggregated lists
ALL_DEMOCRATIC = (
    AMERICAS_DEMOCRATIC +
    MENA_DEMOCRATIC +
    EUROPE_DEMOCRATIC +
    ASIA_PACIFIC_DEMOCRATIC +
    AFRICA_DEMOCRATIC
)

ALL_HYBRID_AUTHORITARIAN = (
    AMERICAS_HYBRID_AUTHORITARIAN +
    MENA_HYBRID_AUTHORITARIAN +
    EUROPE_HYBRID_AUTHORITARIAN +
    ASIA_PACIFIC_HYBRID_AUTHORITARIAN +
    AFRICA_HYBRID_AUTHORITARIAN
)

ALL_FULLY_AUTHORITARIAN = (
    AMERICAS_FULLY_AUTHORITARIAN +
    MENA_FULLY_AUTHORITARIAN +
    EUROPE_FULLY_AUTHORITARIAN +
    ASIA_PACIFIC_FULLY_AUTHORITARIAN +
    AFRICA_FULLY_AUTHORITARIAN
)

ALL_AUTHORITARIAN = ALL_HYBRID_AUTHORITARIAN + ALL_FULLY_AUTHORITARIAN

ALL_UNCLASSIFIED = AMERICAS_UNCLASSIFIED


def get_regime_classification(country: str) -> dict:
    """
    Get the regime classification for a country.

    Returns a dict with:
    - classification: 'democratic', 'hybrid_authoritarian', 'fully_authoritarian', 'unclassified', or 'unknown'
    - region: The geographic region
    - is_authoritarian: Boolean indicating if the country is any form of authoritarian
    """
    country_normalized = country.strip()

    # Check each category
    if country_normalized in ALL_DEMOCRATIC:
        region = _get_region(country_normalized, 'democratic')
        return {
            'classification': 'democratic',
            'region': region,
            'is_authoritarian': False
        }

    if country_normalized in ALL_HYBRID_AUTHORITARIAN:
        region = _get_region(country_normalized, 'hybrid')
        return {
            'classification': 'hybrid_authoritarian',
            'region': region,
            'is_authoritarian': True
        }

    if country_normalized in ALL_FULLY_AUTHORITARIAN:
        region = _get_region(country_normalized, 'authoritarian')
        return {
            'classification': 'fully_authoritarian',
            'region': region,
            'is_authoritarian': True
        }

    if country_normalized in ALL_UNCLASSIFIED:
        return {
            'classification': 'unclassified',
            'region': 'americas',
            'is_authoritarian': False  # Unknown, treat as not authoritarian
        }

    return {
        'classification': 'unknown',
        'region': 'unknown',
        'is_authoritarian': False  # Unknown, treat as not authoritarian
    }


def _get_region(country: str, classification_type: str) -> str:
    """Determine the region for a country."""
    if classification_type == 'democratic':
        if country in AMERICAS_DEMOCRATIC:
            return 'americas'
        if country in MENA_DEMOCRATIC:
            return 'middle_east_north_africa'
        if country in EUROPE_DEMOCRATIC:
            return 'europe_central_asia'
        if country in ASIA_PACIFIC_DEMOCRATIC:
            return 'asia_pacific'
        if country in AFRICA_DEMOCRATIC:
            return 'africa'
    elif classification_type == 'hybrid':
        if country in AMERICAS_HYBRID_AUTHORITARIAN:
            return 'americas'
        if country in MENA_HYBRID_AUTHORITARIAN:
            return 'middle_east_north_africa'
        if country in EUROPE_HYBRID_AUTHORITARIAN:
            return 'europe_central_asia'
        if country in ASIA_PACIFIC_HYBRID_AUTHORITARIAN:
            return 'asia_pacific'
        if country in AFRICA_HYBRID_AUTHORITARIAN:
            return 'africa'
    elif classification_type == 'authoritarian':
        if country in AMERICAS_FULLY_AUTHORITARIAN:
            return 'americas'
        if country in MENA_FULLY_AUTHORITARIAN:
            return 'middle_east_north_africa'
        if country in EUROPE_FULLY_AUTHORITARIAN:
            return 'europe_central_asia'
        if country in ASIA_PACIFIC_FULLY_AUTHORITARIAN:
            return 'asia_pacific'
        if country in AFRICA_FULLY_AUTHORITARIAN:
            return 'africa'
    return 'unknown'


def is_authoritarian_regime(country: str) -> bool:
    """Check if a country is classified as any form of authoritarian regime."""
    return get_regime_classification(country)['is_authoritarian']


def is_fully_authoritarian(country: str) -> bool:
    """Check if a country is classified as fully authoritarian."""
    return country.strip() in ALL_FULLY_AUTHORITARIAN


def is_hybrid_authoritarian(country: str) -> bool:
    """Check if a country is classified as hybrid authoritarian."""
    return country.strip() in ALL_HYBRID_AUTHORITARIAN


# Known despots, dictators, and authoritarian leaders (for keyword matching)
KNOWN_AUTHORITARIAN_LEADERS = [
    # Current leaders of fully authoritarian regimes
    "Xi Jinping",
    "Kim Jong Un",
    "Kim Jong-un",
    "Vladimir Putin",
    "Putin",
    "Alexander Lukashenko",
    "Lukashenko",
    "Bashar al-Assad",
    "Assad",
    "Nicolás Maduro",
    "Nicolas Maduro",
    "Maduro",
    "Daniel Ortega",
    "Ortega",
    "Miguel Díaz-Canel",
    "Díaz-Canel",
    "Diaz-Canel",
    "Ayatollah Khamenei",
    "Khamenei",
    "Mohammed bin Salman",
    "MBS",
    "Abdel Fattah el-Sisi",
    "el-Sisi",
    "Sisi",
    "Ilham Aliyev",
    "Aliyev",
    "Gurbanguly Berdimuhamedow",
    "Serdar Berdimuhamedow",
    "Emomali Rahmon",
    "Islam Karimov",
    "Shavkat Mirziyoyev",
    "Hun Sen",
    "Hun Manet",
    "Recep Tayyip Erdoğan",
    "Erdogan",
    "Paul Kagame",
    "Kagame",
    "Yoweri Museveni",
    "Museveni",
    "Isaias Afwerki",
    "Teodoro Obiang",
    "Obiang",

    # Historical despots/dictators (commonly referenced)
    "Stalin",
    "Joseph Stalin",
    "Mao Zedong",
    "Mao Tse-tung",
    "Mao",
    "Adolf Hitler",
    "Hitler",
    "Pol Pot",
    "Fidel Castro",
    "Castro",
    "Muammar Gaddafi",
    "Gaddafi",
    "Qaddafi",
    "Saddam Hussein",
    "Saddam",
    "Robert Mugabe",
    "Mugabe",
    "Idi Amin",
    "Pinochet",
    "Augusto Pinochet",
    "Francisco Franco",
    "Franco",
    "Benito Mussolini",
    "Mussolini",
    "Kim Il-sung",
    "Kim Jong-il",
    "Hugo Chávez",
    "Hugo Chavez",
    "Chavez",
]

# Authoritarian organizations and entities
AUTHORITARIAN_ENTITIES = [
    "Chinese Communist Party",
    "CCP",
    "CPC",
    "Communist Party of China",
    "United Russia",
    "Kremlin",
    "FSB",
    "KGB",
    "IRGC",
    "Islamic Revolutionary Guard Corps",
    "Hezbollah",
    "Hamas",
    "Wagner Group",
    "Colectivos",
    "Basij",
]
