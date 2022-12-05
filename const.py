from enum import Enum


class Cars(str, Enum):
    GCBART = 'Wymagane samochody ratownictwa technicznego'
    PR = 'Wymagane samochody ze zbiornikiem na piane'
    WRD = 'Wymagane radiowozy WRD'
    OPI = "Wymagane radiowozy"
    HELIP = "Potrzeba Helikopteru Policyjnego"
    ARMATKI = "Wymagane armatki wodne"
    RSD = "Wymagane Ruchome Stanowisko Dowodzenia"
    OPPPICKUP = "Wymagany specjalistyczny sprzęt OPP (Pickup)"
    APRD = "Wymagane APRD"
    K9 = "Potrzeba Jednostki K-9"
    SH = "Wymagany SH lub SD"
    SW = "Wymagane samochody wężowe"
    RCHEM = "Wymagane SP Rchem"
    AMBULANS = "Wymagane ambulanse"
    SCDZ = "Potrzebny Dźwig SP"
    SLOP = "Wymagane SLOp lub SLRr"
    DIL = "Wymagane samochody dowodzenia i łączności"
    SRWYS = 'Potrzebne Ratownictwo Wyskościowe'
    GBA = "Wymagane samochody pożarnicze"
    POWODZ = 'Wymagany sprzęt przeciwpowodziowy'
    SPGAZ = "Wymagane samochody SPGaz"
    SCCN = "Wymagane cysterny z wodą"
    SPKP = "spkp"

MISSING_CARS_MAP = {
    "radiowóz OPI": Cars.OPI,
    "Helikopter Policyjny": Cars.HELIP,
    "Helikopterów Policyjnych": Cars.HELIP,
    "samochody(-ów) pożarnicze(-ych)": Cars.GBA,
    "samochody(ów) pożarnicze(ych)": Cars.GBA,
    "samochód pożarniczy": Cars.GBA,
    'SH lub SD': Cars.SH,
    "Dźwigi SP": Cars.SCDZ,
    "Dźwig SP": Cars.SCDZ,
    "Samochód Ratownictwa Technicznego": Cars.GCBART,
    "SPGaz": Cars.SPGAZ,
    "cystern(-y) z wodą": Cars.SCCN,
    "cystern(y) z wodą": Cars.SCCN,
    "cysterna z wodą": Cars.SCCN,
    "SLOp lub SLRr": Cars.SLOP,
    "samochód dowodzenia i łączności": Cars.DIL,
    "Rchem": Cars.RCHEM,
    "Samochód Ratownictwa wysokościowego": Cars.SRWYS,
    "Samochodów Ratownictwa wysokościowego": Cars.SRWYS,
    "Samochód wężowy": Cars.SW,
    "Samochód ze zbiornikiem na pianę": Cars.PR,
    "Samochodów ze zbiornikiem na pianę": Cars.PR,
    "Jednostka K9": Cars.K9,
    "Jednostek K9": Cars.K9,
    "Ambulanse P": Cars.AMBULANS,
    "Ambulansów P": Cars.AMBULANS,
    "ambulanse(ów)": Cars.AMBULANS,
    "Ambulans P": Cars.AMBULANS,
    "Samochody ze zbiornikiem na pianę": Cars.PR,
    "policjanci SPKP": Cars.SPKP,
    "radiowozy WRD": Cars.WRD,
    "radiowóz WRD": Cars.WRD,
    "sprzęty przeciwpowodziowe": Cars.POWODZ,
    "sprzęt przeciwpowodziowy": Cars.POWODZ,
    "armatka wodna": "",
    "armatki wodne": "",
    "specjalistyczne sprzęty OPP": "",
    "Ruchome Stanowisko Dowodzenia": "",
    "ambulanse OPP": "",
    "ambulans OPP": "",

}


