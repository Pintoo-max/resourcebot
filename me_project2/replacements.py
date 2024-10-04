# replacements.py

def replace_names(text, replacements):
    for old, new in replacements.items():
        text = text.replace(old, new)
    return text

replacements = {
    "CO-OPERATIVE": "COOPERATIVE",
    "GREATER BOMBAY": "MUMBAI",
    "ABHYUDAYA CO-OP BANK LTD": "ABHYUDAYA COOPERATIVE BANK",
    "THE ANDHRA PRADESH STATE COOP BANK LTD": "ANDHRA-PRADESH-STATE-COOPERATIVE-BANK",
    "AU SMALL FINANCE BANK LIMITED": "AU-SMALL-FINANCE-BANK",
    "BASSEIN CATHOLIC CO-OP BANK LTD": "BASSEIN-CATHOLIC-COOPERATIVE-BANK",
    "KAMLA NAGAR, AGRA": "KAMLA-NAGAR-AGRA",
    "AHMADABAD":"AHMEDABAD",
    "RAJAJIPURAM": "RAJAJI PURAM",
    "BIHAR": "",
    "Maharashtra":"",
    "Bihar":"",
    "Manipur":"",
    "Arunachal Pradesh":"",
    "Assam":"",
    "Gujarat":"",
    "Karnataka":"",
    "Kerala":"",
    "Chhattisgarh":"",
    "Haryana":"",
    "Himachal Pradesh":"",
    "Goa":"",
    "Andhra Pradesh":"",
    "Jharkhand":"",
    "Delhi":"",
    "Rajasthan":"",
    "Punjab":"",
    "Madhya Pradesh":"",
    "Odisha":"",
    "Nagaland":"",
    "Mizoram":"",
    "Tamil Nadu":"",
    "Sikkim":"",
    "Telengana":"",
    "Meghalaya":"",
    "WEST BENGAL":"",
    "Uttar Pradesh":"",
    "Tripura":"",
    "Uttarakhand":"",
    "Jammu & Kashmir":"",
    }
