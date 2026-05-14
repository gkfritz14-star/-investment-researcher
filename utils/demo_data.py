"""
Synthetic demo data for testing and grading without a live URL.
Represents a realistic pension fund investment team page.

This data is fictional and created for demonstration purposes only.
"""

DEMO_PAGE_TEXT = """
Midwest Public Employees Retirement System (MPERS)
Investment Division | Leadership Team

Our Investment Team

The MPERS Investment Division manages approximately $28 billion in assets across a 
diversified portfolio. The team is led by experienced professionals with deep expertise 
in institutional asset management.

Chief Investment Officer
Katherine Brennan, CFA
Katherine Brennan joined MPERS as Chief Investment Officer in January 2021. She brings 
over 22 years of institutional investment experience, having previously served as Head of 
Global Multi-Asset at Vanguard Institutional and before that as a Senior Portfolio Manager 
at the Pennsylvania State Employees' Retirement System. Katherine holds an MBA from Wharton 
and a BA in Economics from Georgetown University. She oversees all investment strategy and 
asset allocation decisions for the fund.

Deputy CIO
Marcus Delgado
Marcus Delgado serves as Deputy Chief Investment Officer, with direct oversight of the 
public markets portfolio including domestic and international equities and fixed income. 
Before joining MPERS in 2018, Marcus spent eight years at BlackRock's Multi-Asset Strategies 
group in New York. He holds a Master's in Financial Mathematics from Carnegie Mellon and is 
a CFA charterholder.

Director of Private Markets
Priya Nair, CFA, CAIA
Priya Nair leads MPERS' private markets program, which includes private equity, private credit, 
real assets, and infrastructure investments totaling approximately $7 billion. She joined MPERS 
in 2019 from Hamilton Lane, where she was a Senior Associate focused on co-investments and 
secondary transactions. Priya received her MBA from University of Chicago Booth School of 
Business and her undergraduate degree from University of Michigan.

Director of Risk Management
Jonathan Whitfield
Jonathan Whitfield oversees enterprise risk management, performance attribution, and 
quantitative analytics for the investment division. He joined MPERS in 2016 from Mercer 
Investment Consulting, where he advised public pension clients on liability-driven investment 
strategies. Jonathan holds an MS in Statistics from University of Chicago and a BA in 
Mathematics from Northwestern University.

Senior Investment Analyst — Real Assets
Sofia Marchetti
Sofia Marchetti is responsible for manager selection and monitoring within the real assets 
portfolio, including real estate, infrastructure, and natural resources. She joined MPERS 
in 2022 after four years at TIAA, where she focused on commercial real estate debt 
origination. Sofia holds an MS in Real Estate Finance from NYU Stern.

Investment Committee Members (External)
Robert Chen — Managing Director, Bridgewater Associates (retired)
Laura Okafor — Professor of Finance, University of Illinois at Chicago
Thomas Reeves — Former Treasurer, State of Wisconsin

Contact Information
Investment Division
Midwest Public Employees Retirement System
123 Capital Avenue, Suite 400
Springfield, IL 62701
investment@mpers.gov

Reports & Publications
2024 Annual Investment Report
2024 Investment Policy Statement
Quarterly Performance Reports
"""

DEMO_SOURCE_URL = "https://www.mpers-demo.gov/investment-division/leadership"
DEMO_TITLE = "Investment Division Leadership — Midwest Public Employees Retirement System"

DEMO_EXPECTED_TEAM = [
    {"name": "Katherine Brennan", "title": "Chief Investment Officer"},
    {"name": "Marcus Delgado", "title": "Deputy CIO"},
    {"name": "Priya Nair", "title": "Director of Private Markets"},
    {"name": "Jonathan Whitfield", "title": "Director of Risk Management"},
    {"name": "Sofia Marchetti", "title": "Senior Investment Analyst — Real Assets"},
]

DEMO_BASELINE_EXPECTED = [
    # These are name-like strings the regex WOULD find (mix of real and false positives)
    "Katherine Brennan",
    "Marcus Delgado",
    "Priya Nair",
    "Jonathan Whitfield",
    "Sofia Marchetti",
    "Robert Chen",       # committee member
    "Laura Okafor",      # committee member
    "Thomas Reeves",     # committee member
    "Bridgewater Associates",  # false positive
    "University Illinois",     # false positive
    "Investment Division",     # false positive
    "Annual Investment",       # false positive
]

DEMO_PROFILES = [
    {
        "name": "Katherine Brennan",
        "title": "Chief Investment Officer",
        "organization": "Midwest Public Employees Retirement System",
        "source_url": DEMO_SOURCE_URL,
        "ai_profile": (
            "Katherine Brennan serves as Chief Investment Officer of MPERS, overseeing approximately "
            "$28 billion in assets under management. She joined in January 2021, bringing over 22 years "
            "of institutional investment experience. Prior to MPERS, Brennan served as Head of Global "
            "Multi-Asset at Vanguard Institutional, leading a team managing multi-asset strategies for "
            "large institutional clients. Earlier she was a Senior Portfolio Manager at the Pennsylvania "
            "State Employees' Retirement System. Brennan holds an MBA from the Wharton School and a BA "
            "in Economics from Georgetown University. She is a CFA charterholder known for her emphasis "
            "on liability-driven investment strategies and risk-adjusted returns."
        ),
        "linkedin_url": "",
        "key_facts": [
            "CFA charterholder",
            "22+ years institutional investment experience",
            "Former Head of Global Multi-Asset at Vanguard",
            "MBA from Wharton",
            "Oversees $28B AUM",
        ],
        "confidence": "high",
        "search_notes": "Demo data — synthetic profile",
        "baseline_bio": "Katherine Brennan joined MPERS as Chief Investment Officer in January 2021.",
    },
    {
        "name": "Marcus Delgado",
        "title": "Deputy CIO",
        "organization": "Midwest Public Employees Retirement System",
        "source_url": DEMO_SOURCE_URL,
        "ai_profile": (
            "Marcus Delgado is Deputy Chief Investment Officer at MPERS with direct oversight of the "
            "public markets portfolio, including domestic and international equities and fixed income. "
            "He joined MPERS in 2018 after eight years at BlackRock's Multi-Asset Strategies group in "
            "New York, where he worked on portfolio construction and risk management for institutional "
            "clients. His BlackRock tenure gave him deep expertise in factor investing and systematic "
            "strategies. Delgado holds a Master's in Financial Mathematics from Carnegie Mellon University "
            "and is a CFA charterholder. He is recognized for his quantitative approach to asset "
            "allocation and his work building out the fund's smart-beta equity portfolio."
        ),
        "linkedin_url": "",
        "key_facts": [
            "CFA charterholder",
            "8 years at BlackRock Multi-Asset Strategies",
            "MS in Financial Mathematics from Carnegie Mellon",
            "Oversees public markets portfolio",
        ],
        "confidence": "high",
        "search_notes": "Demo data — synthetic profile",
        "baseline_bio": "Marcus Delgado serves as Deputy CIO with direct oversight of the public markets portfolio.",
    },
    {
        "name": "Priya Nair",
        "title": "Director of Private Markets",
        "organization": "Midwest Public Employees Retirement System",
        "source_url": DEMO_SOURCE_URL,
        "ai_profile": (
            "Priya Nair leads MPERS' private markets program as Director of Private Markets, overseeing "
            "approximately $7 billion across private equity, private credit, real assets, and "
            "infrastructure. She joined MPERS in 2019 from Hamilton Lane, where she focused on "
            "co-investments and secondary transactions as a Senior Associate. Her Hamilton Lane "
            "experience provided extensive exposure to manager selection, deal underwriting, and "
            "portfolio monitoring across global private markets. Nair holds an MBA from the University "
            "of Chicago Booth School of Business and a BA from the University of Michigan. She holds "
            "both the CFA and CAIA designations, reflecting her breadth of expertise across traditional "
            "and alternative investments."
        ),
        "linkedin_url": "",
        "key_facts": [
            "CFA and CAIA charterholder",
            "Former Senior Associate at Hamilton Lane",
            "Oversees $7B private markets portfolio",
            "MBA from University of Chicago Booth",
        ],
        "confidence": "high",
        "search_notes": "Demo data — synthetic profile",
        "baseline_bio": "Priya Nair leads MPERS' private markets program including private equity and infrastructure.",
    },
    {
        "name": "Jonathan Whitfield",
        "title": "Director of Risk Management",
        "organization": "Midwest Public Employees Retirement System",
        "source_url": DEMO_SOURCE_URL,
        "ai_profile": (
            "Jonathan Whitfield serves as Director of Risk Management at MPERS, responsible for "
            "enterprise risk management, performance attribution, and quantitative analytics for the "
            "investment division. He joined MPERS in 2016 from Mercer Investment Consulting, where he "
            "spent six years advising public pension clients on liability-driven investment strategies "
            "and asset-liability management. His consulting background provided broad perspective on "
            "risk frameworks across the public pension universe. Whitfield holds an MS in Statistics "
            "from the University of Chicago and a BA in Mathematics from Northwestern University. He "
            "is known for his rigorous approach to factor risk decomposition and his work implementing "
            "the fund's stress-testing framework."
        ),
        "linkedin_url": "",
        "key_facts": [
            "MS in Statistics from University of Chicago",
            "Former Mercer Investment Consulting",
            "Specialist in liability-driven investment",
            "Leads enterprise risk management",
        ],
        "confidence": "high",
        "search_notes": "Demo data — synthetic profile",
        "baseline_bio": "Jonathan Whitfield oversees enterprise risk management and quantitative analytics.",
    },
    {
        "name": "Sofia Marchetti",
        "title": "Senior Investment Analyst — Real Assets",
        "organization": "Midwest Public Employees Retirement System",
        "source_url": DEMO_SOURCE_URL,
        "ai_profile": (
            "Sofia Marchetti is Senior Investment Analyst for Real Assets at MPERS, responsible for "
            "manager selection and monitoring within the real assets portfolio including real estate, "
            "infrastructure, and natural resources. She joined MPERS in 2022 following four years at "
            "TIAA, where she worked in commercial real estate debt origination, evaluating and "
            "structuring loans across office, multifamily, and industrial properties. Her TIAA "
            "experience gave her granular knowledge of real estate credit markets and property-level "
            "underwriting. Marchetti holds an MS in Real Estate Finance from NYU Stern School of "
            "Business. She is actively involved in the fund's transition to a net-zero aligned real "
            "assets portfolio."
        ),
        "linkedin_url": "",
        "key_facts": [
            "MS in Real Estate Finance from NYU Stern",
            "Former TIAA real estate debt origination",
            "Covers real estate, infrastructure, natural resources",
            "Focus on net-zero aligned investing",
        ],
        "confidence": "medium",
        "search_notes": "Demo data — synthetic profile",
        "baseline_bio": "Sofia Marchetti is responsible for manager selection in the real assets portfolio.",
    },
]
