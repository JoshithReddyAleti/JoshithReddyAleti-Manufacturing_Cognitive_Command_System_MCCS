"""Industry configuration - defines what each industry monitors.

When a user selects an industry, this config tells each MCP server
exactly what to search for, which stocks to watch, which FRED series
matter, and which geopolitical keywords are relevant.
"""

INDUSTRY_CONFIG = {
    "semiconductor": {
        "name": "Semiconductor & Chips",
        "stocks": [
            {"symbol": "SOXX", "name": "Semiconductor ETF"},
            {"symbol": "TSM", "name": "TSMC"},
            {"symbol": "NVDA", "name": "NVIDIA"},
            {"symbol": "AMD", "name": "AMD"},
            {"symbol": "INTC", "name": "Intel"},
            {"symbol": "ASML", "name": "ASML"},
        ],
        "gdelt_keywords": [
            "semiconductor chip shortage",
            "TSMC Taiwan fab",
            "chip export controls",
            "semiconductor supply chain",
            "wafer production disruption",
        ],
        "trade_keywords": [
            "semiconductor export controls chips ban",
            "chip tariff trade restriction",
        ],
        "fred_series": ["INDPRO", "MCUMFN", "NEWORDER"],
        "bls_series": ["CES3100000001", "CES3000000006"],  # Computer/electronic manufacturing
        "weather_locations": [
            {"name": "Hsinchu", "lat": 24.80, "lon": 120.97, "entities": ["tsmc-fab"]},
            {"name": "Seoul", "lat": 37.57, "lon": 126.98, "entities": ["samsung-fab"]},
            {"name": "Phoenix", "lat": 33.45, "lon": -112.07, "entities": ["intel-fab-az"]},
            {"name": "Dresden", "lat": 51.05, "lon": 13.74, "entities": ["globalfoundries-eu"]},
        ],
        "key_countries": ["taiwan", "south korea", "china", "united states", "japan", "netherlands"],
    },
    "automotive": {
        "name": "Automotive & EV",
        "stocks": [
            {"symbol": "XLI", "name": "Industrials ETF"},
            {"symbol": "TSLA", "name": "Tesla"},
            {"symbol": "F", "name": "Ford"},
            {"symbol": "GM", "name": "General Motors"},
            {"symbol": "TM", "name": "Toyota"},
            {"symbol": "RIVN", "name": "Rivian"},
        ],
        "gdelt_keywords": [
            "automotive production disruption",
            "EV battery supply shortage",
            "auto parts supply chain",
            "UAW strike automotive",
            "car manufacturing plant shutdown",
        ],
        "trade_keywords": [
            "automotive tariff import duty",
            "EV battery trade restriction",
        ],
        "fred_series": ["INDPRO", "DAUPSA", "MCUMFN"],  # DAUPSA = auto production
        "bls_series": ["CES3133600101", "CES3000000006"],  # Motor vehicle manufacturing
        "weather_locations": [
            {"name": "Detroit", "lat": 42.33, "lon": -83.05, "entities": ["auto-assembly-detroit"]},
            {"name": "Monterrey", "lat": 25.67, "lon": -100.31, "entities": ["auto-parts-mexico"]},
            {"name": "Stuttgart", "lat": 48.78, "lon": 9.18, "entities": ["auto-germany"]},
            {"name": "Nagoya", "lat": 35.18, "lon": 136.91, "entities": ["toyota-japan"]},
        ],
        "key_countries": ["united states", "mexico", "germany", "japan", "china", "south korea"],
    },
    "pharmaceutical": {
        "name": "Pharmaceutical & Biotech",
        "stocks": [
            {"symbol": "XLV", "name": "Healthcare ETF"},
            {"symbol": "PFE", "name": "Pfizer"},
            {"symbol": "JNJ", "name": "Johnson & Johnson"},
            {"symbol": "MRK", "name": "Merck"},
            {"symbol": "ABBV", "name": "AbbVie"},
            {"symbol": "LLY", "name": "Eli Lilly"},
        ],
        "gdelt_keywords": [
            "pharmaceutical supply chain disruption",
            "drug shortage API ingredient",
            "pharma manufacturing recall",
            "generic drug supply India China",
            "FDA approval delay",
        ],
        "trade_keywords": [
            "pharmaceutical export ban drug",
            "API active pharmaceutical ingredient trade",
        ],
        "fred_series": ["INDPRO", "MCUMFN", "PCE"],
        "bls_series": ["CES3232500001", "CES3000000006"],  # Pharma manufacturing
        "weather_locations": [
            {"name": "Mumbai", "lat": 19.08, "lon": 72.88, "entities": ["pharma-india"]},
            {"name": "Basel", "lat": 47.56, "lon": 7.59, "entities": ["pharma-switzerland"]},
            {"name": "New Jersey", "lat": 40.06, "lon": -74.41, "entities": ["pharma-us-east"]},
            {"name": "Shanghai", "lat": 31.23, "lon": 121.47, "entities": ["pharma-china"]},
        ],
        "key_countries": ["india", "china", "united states", "switzerland", "ireland", "germany"],
    },
    "medical_devices": {
        "name": "Medical Devices",
        "stocks": [
            {"symbol": "IHI", "name": "Medical Devices ETF"},
            {"symbol": "MDT", "name": "Medtronic"},
            {"symbol": "ABT", "name": "Abbott"},
            {"symbol": "SYK", "name": "Stryker"},
            {"symbol": "BSX", "name": "Boston Scientific"},
        ],
        "gdelt_keywords": [
            "medical device supply shortage",
            "surgical equipment recall",
            "medical device manufacturing",
            "implant supply chain",
            "diagnostic equipment shortage",
        ],
        "trade_keywords": [
            "medical device tariff import",
            "healthcare equipment trade restriction",
        ],
        "fred_series": ["INDPRO", "MCUMFN"],
        "bls_series": ["CES3239100001", "CES3000000006"],
        "weather_locations": [
            {"name": "Minneapolis", "lat": 44.98, "lon": -93.27, "entities": ["medtronic-hq"]},
            {"name": "Galway", "lat": 53.27, "lon": -9.06, "entities": ["medtech-ireland"]},
            {"name": "Tuttlingen", "lat": 47.98, "lon": 8.82, "entities": ["surgical-germany"]},
        ],
        "key_countries": ["united states", "ireland", "germany", "costa rica", "mexico", "china"],
    },
    "energy": {
        "name": "Energy & Renewables",
        "stocks": [
            {"symbol": "XLE", "name": "Energy ETF"},
            {"symbol": "TAN", "name": "Solar ETF"},
            {"symbol": "XOM", "name": "ExxonMobil"},
            {"symbol": "CVX", "name": "Chevron"},
            {"symbol": "ENPH", "name": "Enphase Energy"},
        ],
        "gdelt_keywords": [
            "energy supply disruption",
            "oil production cut OPEC",
            "solar panel supply chain",
            "natural gas shortage",
            "renewable energy manufacturing",
        ],
        "trade_keywords": [
            "energy tariff oil sanctions",
            "solar panel import duty trade",
        ],
        "fred_series": ["INDPRO", "DCOILWTICO", "MCUMFN"],  # DCOILWTICO = crude oil price
        "bls_series": ["CES1021100001", "CES3000000006"],  # Oil & gas extraction
        "weather_locations": [
            {"name": "Houston", "lat": 29.76, "lon": -95.37, "entities": ["energy-gulf"]},
            {"name": "Riyadh", "lat": 24.71, "lon": 46.67, "entities": ["energy-saudi"]},
            {"name": "Xinjiang", "lat": 43.79, "lon": 87.60, "entities": ["solar-china"]},
        ],
        "key_countries": ["united states", "saudi arabia", "russia", "china", "norway", "canada"],
    },
    "textiles": {
        "name": "Textiles & Apparel",
        "stocks": [
            {"symbol": "XRT", "name": "Retail ETF"},
            {"symbol": "NKE", "name": "Nike"},
            {"symbol": "LULU", "name": "Lululemon"},
            {"symbol": "VFC", "name": "VF Corp"},
        ],
        "gdelt_keywords": [
            "textile manufacturing disruption",
            "garment factory shutdown",
            "cotton supply shortage",
            "apparel supply chain",
            "shoe manufacturing labor",
        ],
        "trade_keywords": [
            "textile tariff import duty apparel",
            "cotton trade restriction",
        ],
        "fred_series": ["INDPRO", "MCUMFN"],
        "bls_series": ["CES3231500001", "CES3000000006"],  # Textile mills
        "weather_locations": [
            {"name": "Dhaka", "lat": 23.81, "lon": 90.41, "entities": ["garment-bangladesh"]},
            {"name": "Ho Chi Minh", "lat": 10.82, "lon": 106.63, "entities": ["textile-vietnam"]},
            {"name": "Guangzhou", "lat": 23.13, "lon": 113.26, "entities": ["textile-china"]},
        ],
        "key_countries": ["bangladesh", "vietnam", "china", "india", "turkey", "indonesia"],
    },
    "steel_metals": {
        "name": "Steel & Metals",
        "stocks": [
            {"symbol": "XLB", "name": "Materials ETF"},
            {"symbol": "NUE", "name": "Nucor"},
            {"symbol": "X", "name": "US Steel"},
            {"symbol": "CLF", "name": "Cleveland-Cliffs"},
            {"symbol": "FCX", "name": "Freeport-McMoRan"},
        ],
        "gdelt_keywords": [
            "steel production disruption",
            "aluminum supply shortage",
            "metal mining strike",
            "iron ore supply chain",
            "rare earth minerals export",
        ],
        "trade_keywords": [
            "steel tariff anti-dumping",
            "aluminum import duty trade",
        ],
        "fred_series": ["INDPRO", "MCUMFN", "WPU101"],  # WPU101 = iron/steel PPI
        "bls_series": ["CES3133100001", "CES3000000006"],  # Primary metals
        "weather_locations": [
            {"name": "Pittsburgh", "lat": 40.44, "lon": -79.99, "entities": ["steel-us"]},
            {"name": "Tangshan", "lat": 39.63, "lon": 118.18, "entities": ["steel-china"]},
            {"name": "Pilbara", "lat": -22.30, "lon": 118.60, "entities": ["iron-ore-australia"]},
        ],
        "key_countries": ["china", "united states", "india", "japan", "russia", "australia"],
    },
    "construction": {
        "name": "Construction & Building Materials",
        "stocks": [
            {"symbol": "XHB", "name": "Homebuilders ETF"},
            {"symbol": "VMC", "name": "Vulcan Materials"},
            {"symbol": "MLM", "name": "Martin Marietta"},
            {"symbol": "SHW", "name": "Sherwin-Williams"},
        ],
        "gdelt_keywords": [
            "construction material shortage",
            "cement supply disruption",
            "building material price surge",
            "lumber supply chain",
            "HVAC manufacturing",
        ],
        "trade_keywords": [
            "construction material tariff lumber",
            "building products import duty",
        ],
        "fred_series": ["INDPRO", "HOUST", "MCUMFN"],  # HOUST = housing starts
        "bls_series": ["CES2000000001", "CES3000000006"],  # Construction employment
        "weather_locations": [
            {"name": "Dallas", "lat": 32.78, "lon": -96.80, "entities": ["construction-south"]},
            {"name": "Dubai", "lat": 25.20, "lon": 55.27, "entities": ["construction-gulf"]},
        ],
        "key_countries": ["united states", "china", "india", "uae", "saudi arabia", "germany"],
    },
    "aerospace": {
        "name": "Aerospace & Defense",
        "stocks": [
            {"symbol": "ITA", "name": "Aerospace & Defense ETF"},
            {"symbol": "BA", "name": "Boeing"},
            {"symbol": "LMT", "name": "Lockheed Martin"},
            {"symbol": "RTX", "name": "RTX (Raytheon)"},
            {"symbol": "NOC", "name": "Northrop Grumman"},
            {"symbol": "GD", "name": "General Dynamics"},
        ],
        "gdelt_keywords": [
            "aerospace supply chain disruption",
            "defense manufacturing delay",
            "aircraft production shortage",
            "titanium supply aerospace",
            "Boeing delivery delay",
        ],
        "trade_keywords": [
            "defense export controls ITAR",
            "aerospace tariff trade restriction",
        ],
        "fred_series": ["INDPRO", "MCUMFN", "NEWORDER"],
        "bls_series": ["CES3136400001", "CES3000000006"],
        "weather_locations": [
            {"name": "Seattle", "lat": 47.61, "lon": -122.33, "entities": ["boeing-everett"]},
            {"name": "Toulouse", "lat": 43.60, "lon": 1.44, "entities": ["airbus-toulouse"]},
            {"name": "Fort Worth", "lat": 32.75, "lon": -97.33, "entities": ["lockheed-ftworth"]},
            {"name": "Wichita", "lat": 37.69, "lon": -97.34, "entities": ["spirit-aero"]},
        ],
        "key_countries": ["united states", "france", "united kingdom", "israel", "japan", "germany"],
    },
    "electronics": {
        "name": "Consumer Electronics",
        "stocks": [
            {"symbol": "XLK", "name": "Technology ETF"},
            {"symbol": "AAPL", "name": "Apple"},
            {"symbol": "SONY", "name": "Sony"},
            {"symbol": "005930.KS", "name": "Samsung"},
            {"symbol": "DELL", "name": "Dell"},
        ],
        "gdelt_keywords": [
            "electronics manufacturing disruption",
            "smartphone production delay",
            "display panel shortage",
            "consumer electronics supply chain",
            "electronics factory shutdown",
        ],
        "trade_keywords": [
            "electronics tariff import ban",
            "consumer tech trade restriction",
        ],
        "fred_series": ["INDPRO", "MCUMFN", "RSXFS"],
        "bls_series": ["CES3133400001", "CES3000000006"],
        "weather_locations": [
            {"name": "Shenzhen", "lat": 22.54, "lon": 114.06, "entities": ["electronics-shenzhen"]},
            {"name": "Seoul", "lat": 37.57, "lon": 126.98, "entities": ["samsung-korea"]},
            {"name": "Cupertino", "lat": 37.32, "lon": -122.03, "entities": ["apple-hq"]},
            {"name": "Ho Chi Minh", "lat": 10.82, "lon": 106.63, "entities": ["electronics-vietnam"]},
        ],
        "key_countries": ["china", "south korea", "vietnam", "india", "united states", "japan"],
    },
    "chemicals": {
        "name": "Chemicals & Materials",
        "stocks": [
            {"symbol": "XLB", "name": "Materials ETF"},
            {"symbol": "DD", "name": "DuPont"},
            {"symbol": "DOW", "name": "Dow Inc"},
            {"symbol": "LYB", "name": "LyondellBasell"},
            {"symbol": "EMN", "name": "Eastman Chemical"},
        ],
        "gdelt_keywords": [
            "chemical plant explosion shutdown",
            "petrochemical supply disruption",
            "polymer resin shortage",
            "chemical manufacturing accident",
            "hazardous material transport",
        ],
        "trade_keywords": [
            "chemical tariff import restriction",
            "petrochemical sanctions trade",
        ],
        "fred_series": ["INDPRO", "MCUMFN", "WPU06"],
        "bls_series": ["CES3232500001", "CES3000000006"],
        "weather_locations": [
            {"name": "Houston", "lat": 29.76, "lon": -95.37, "entities": ["chemical-gulf-coast"]},
            {"name": "Ludwigshafen", "lat": 49.48, "lon": 8.44, "entities": ["basf-germany"]},
            {"name": "Jubail", "lat": 27.01, "lon": 49.66, "entities": ["sabic-saudi"]},
        ],
        "key_countries": ["united states", "germany", "china", "saudi arabia", "japan", "south korea"],
    },
    "food_beverage": {
        "name": "Food & Beverage",
        "stocks": [
            {"symbol": "XLP", "name": "Consumer Staples ETF"},
            {"symbol": "KO", "name": "Coca-Cola"},
            {"symbol": "PEP", "name": "PepsiCo"},
            {"symbol": "MDLZ", "name": "Mondelez"},
            {"symbol": "ADM", "name": "Archer-Daniels-Midland"},
        ],
        "gdelt_keywords": [
            "food supply chain disruption",
            "agriculture drought crop failure",
            "food processing plant shutdown",
            "grain export ban",
            "food safety recall contamination",
        ],
        "trade_keywords": [
            "food export ban agricultural tariff",
            "grain trade restriction embargo",
        ],
        "fred_series": ["INDPRO", "MCUMFN", "WPU01"],
        "bls_series": ["CES3131100001", "CES3000000006"],
        "weather_locations": [
            {"name": "Chicago", "lat": 41.88, "lon": -87.63, "entities": ["grain-midwest"]},
            {"name": "Sao Paulo", "lat": -23.55, "lon": -46.63, "entities": ["agriculture-brazil"]},
            {"name": "Odessa", "lat": 46.48, "lon": 30.73, "entities": ["grain-ukraine"]},
        ],
        "key_countries": ["united states", "brazil", "ukraine", "india", "china", "argentina"],
    },
}


def get_industry_config(industry_id: str) -> dict:
    """Get configuration for a specific industry. Returns default if not found."""
    if industry_id and industry_id in INDUSTRY_CONFIG:
        return INDUSTRY_CONFIG[industry_id]
    # Default: general manufacturing
    return {
        "name": "General Manufacturing",
        "stocks": [
            {"symbol": "XLI", "name": "Industrials ETF"},
            {"symbol": "XLB", "name": "Materials ETF"},
            {"symbol": "SOXX", "name": "Semiconductor ETF"},
            {"symbol": "IYT", "name": "Transportation ETF"},
        ],
        "gdelt_keywords": [
            "manufacturing disruption supply chain",
            "factory shutdown production halt",
        ],
        "trade_keywords": [
            "tariff trade war manufacturing",
            "export controls sanctions",
        ],
        "fred_series": ["INDPRO", "MCUMFN", "AMTMNO"],
        "bls_series": ["CES3000000001", "CES3000000006"],
        "weather_locations": [
            {"name": "Houston", "lat": 29.76, "lon": -95.37, "entities": ["port-houston"]},
            {"name": "Shanghai", "lat": 31.23, "lon": 121.47, "entities": ["port-shanghai"]},
            {"name": "Rotterdam", "lat": 51.92, "lon": 4.48, "entities": ["port-rotterdam"]},
        ],
        "key_countries": ["united states", "china", "germany", "japan", "taiwan"],
    }
