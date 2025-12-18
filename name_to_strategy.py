"""
Script complet pour parser Trade_monitor.csv et construire des StrategyComparison
"""

import re
from typing import List, Tuple, Optional
from src.models.strategy import Strategy, OptionLeg, Position 

def separate_parts(info_strategy: str) -> Tuple[str, str, str]:
    """
    Sépare une ligne comme 'Avi  SFRF6 96.50/96.625/96.75 Call Fly  buy to open' en 3 parties
    basé sur les grands espaces (2+ espaces consécutifs)
    - partie 1: 'Avi'
    - partie 2: 'SFRF6 96.50/96.625/96.75 Call Fly'
    - partie 3: 'buy to open'
    """
    # Split sur les espaces multiples (2 ou plus)
    parts = re.split(r'\s{3,}', info_strategy.strip())
    
    # Si une seule partie, la mettre dans parts[1] (stratégie)
    if len(parts) == 1:
        return "", parts[0], ""
    
    # Garantir 3 éléments
    while len(parts) < 3:
        parts.append("")
    
    return parts[0], parts[1], parts[2]

def extract_strikes(strategy_str: str) -> List[float]:
    """Extraction avancée des strikes - gère tous les formats"""
    strikes = []

    # Nettoyer: retirer codes produit au début (ERJ4, SFRM4, etc.)
    cleaned_str = re.sub(r"^\s*[A-Z]{2,5}\d\s+", "", strategy_str, flags=re.IGNORECASE)

    # Chercher d'abord les séquences avec / (priorité)
    # Pattern: nombres séparés par / (avec ou sans décimales)
    slash_pattern = r"(\d{2,3}\.?\d{0,5}(?:/\d{1,5}\.?\d{0,5})+)"
    slash_sequences = re.findall(slash_pattern, cleaned_str)

    for sequence in slash_sequences:
        parts = sequence.split("/")
        first = parts[0]

        if "." in first:
            # Format avec décimales: 106.4/106.8/107 ou 95.06/12/18
            base = first.split(".")[0]

            # Premier élément
            try:
                strike = float(first)
                if 50 < strike < 200:
                    strikes.append(strike)
            except:
                pass

            # Éléments suivants
            for part in parts[1:]:
                if "." in part:
                    # Décimale complète: 106.8, 95.125
                    try:
                        strike = float(part)
                        if 50 < strike < 200:
                            strikes.append(strike)
                    except:
                        pass
                elif len(part) <= 2:
                    # Suffixe 2 chiffres: "12" → 95.12
                    try:
                        strike = float(base + "." + part)
                        if 50 < strike < 200:
                            strikes.append(strike)
                    except:
                        pass
                elif len(part) == 3:
                    # 3 chiffres: probablement entier "107"
                    try:
                        strike = float(part)
                        if 50 < strike < 200:
                            strikes.append(strike)
                    except:
                        pass
                else:
                    # 4+ chiffres: format collé "9712"
                    try:
                        strike = float(part[:2] + "." + part[2:])
                        if 50 < strike < 200:
                            strikes.append(strike)
                    except:
                        pass

        elif len(first) == 2:
            # Format: 95/95.06/95.125/95.18 (premier = 2 chiffres)
            base = first
            try:
                strike = float(first)
                if 50 < strike < 200:
                    strikes.append(strike)
            except:
                pass

            for part in parts[1:]:
                if "." in part:
                    try:
                        strike = float(part)
                        if 50 < strike < 200:
                            strikes.append(strike)
                    except:
                        pass
                elif len(part) <= 2:
                    try:
                        strike = float(base + "." + part)
                        if 50 < strike < 200:
                            strikes.append(strike)
                    except:
                        pass

    # Si pas de séquence trouvée, extraction simple
    if not strikes:
        simple_pattern = r"\b(\d{2,3}\.?\d{0,5})\b"
        matches = re.findall(simple_pattern, cleaned_str)
        for match in matches:
            try:
                strike = float(match)
                if 50 < strike < 200:
                    strikes.append(strike)
            except:
                pass

    # Dédupliquer et trier
    return sorted(list(strikes))

def detect_strategy_type(strategy_str: str, num_strikes: int) -> Tuple[str, str]:
    """Détection simple du type de stratégie"""
    strategy_lower = strategy_str.lower()

    # Déterminer si call ou put
    if "put" in strategy_lower or " p " in strategy_lower or " ps" in strategy_lower:
        option_type = "put"
    else:
        option_type = "call"

    # Détecter le type basé sur les mots-clés et le nombre de strikes
    if "fly" in strategy_lower:
        if (
            "broken" in strategy_lower
            or "brk" in strategy_lower
            or "bkn" in strategy_lower
        ):
            return f"broken_{option_type}_fly", option_type
        return f"{option_type}_fly", option_type
    elif "condor" in strategy_lower:
        return f"{option_type}_condor", option_type
    elif (
        "spread" in strategy_lower or " cs" in strategy_lower or " ps" in strategy_lower
    ):
        return f"{option_type}_spread", option_type
    elif num_strikes == 2:
        return f"{option_type}_spread", option_type
    elif num_strikes == 3:
        return f"{option_type}_fly", option_type
    elif num_strikes == 4:
        return f"{option_type}_condor", option_type

    return "unknown", option_type

def str_to_strat(info_strategy : str) -> Optional[Strategy]:
    """
    Convertit une string de stratégie en objet Strategy
    Ex: 'Avi  SFRF6 96.50/96.625/96.75 Call Fly  buy to open'
    """
    Legs : List[OptionLeg] = []
    client, name, action = separate_parts(info_strategy)
    
    # Si pas de nom de stratégie, retourner None
    if not name:
        return None
    
    strikes = extract_strikes(name)
    strategy_type, opt_type = detect_strategy_type(name, len(strikes))

    # Extraire underlying et expiry
    pattern = r"\b([A-Z]{2,4})([FGHJKMNQUVXZ]\d)\b"
    match = re.search(pattern, name, re.IGNORECASE)
    
    # Si pas de match, impossible de créer les tickers
    if not match:
        return None
    
    underlying = match.group(1).upper()
    expiry = match.group(2).upper()
    
    # Convertir call/put en C/P pour Bloomberg
    opt_type_code = "C" if opt_type == "call" else "P"

    # Définir les signes selon le type de stratégie
    if "fly" in strategy_type and len(strikes) == 3:
        # Fly: +strike1 -2×strike2 +strike3
        signs = [("long",1), ("short",2), ("long",1)]
    elif "condor" in strategy_type and len(strikes) == 4:
        # Condor: +strike1 -strike2 -strike3 +strike4
        signs = [("long",1), ("short",1), ("short",1), ("long",1)]
    elif "spread" in strategy_type and len(strikes) == 2:
        # Spread: +strike1 -strike2
        signs = [("long", 1), ("short", 1)]
    else: 
        # Par défaut: tous long avec quantité 1
        signs = [("long", 1)] * len(strikes)

    # Créer les legs
    for i, strike in enumerate(strikes):
        if i >= len(signs):
            break
            
        ticker = f"{underlying}{expiry} {strike}{opt_type_code} Comdty"
        position = Position.LONG if signs[i][0] == "long" else Position.SHORT
        quantity = signs[i][1]
        
        Leg_i = OptionLeg(ticker=ticker, position=position, quantity=quantity)
        Legs.append(Leg_i)
    
    # Créer la stratégie
    strategy = Strategy(
        name=name,
        legs=Legs,
        client=client if client else None,
        action=action if action else None,
    )
    return strategy
