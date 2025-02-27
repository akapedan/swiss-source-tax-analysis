def get_translations():
    """
    Returns translations for UI elements in different languages.
    """
    return {
        'en': {
            'income_range': "Select Income Range (CHF):",
            'tarif_code': "Tariff Code:",
            'church_tax': "Church Tax Option:",
            'number_of_children': "Number of Children:",
            'language_region': "Select Language Region:",
            'select_cantons': "Select Cantons:",
            'monthly_income': "Monthly Taxable Income (CHF)",
            'tax_rate': "Source Tax Rate (%)",
            'source_tax_progression': "Source Tax Rate Progression by Canton (2025)",
            'income_range_text': "Income Range",
            'no_data_available': "No data available for the selected combination of tariff code and church tax option"
        },
        'de': {
            'income_range': "Einkommensbereich auswählen (CHF):",
            'tarif_code': "Tarifcode:",
            'church_tax': "Kirchensteuer-Option:",
            'number_of_children': "Anzahl Kinder:",
            'language_region': "Sprachregion auswählen:",
            'select_cantons': "Kantone auswählen:",
            'monthly_income': "Monatliches steuerbares Einkommen (CHF)",
            'tax_rate': "Quellensteuersatz (%)",
            'source_tax_progression': "Quellensteuersatz-Progression nach Kanton (2025)",
            'income_range_text': "Einkommensbereich",
            'no_data_available': "Keine Daten verfügbar für die ausgewählte Kombination aus Tarifcode und Kirchensteuer-Option"
        },
        'fr': {
            'income_range': "Sélectionner la plage de revenus (CHF):",
            'tarif_code': "Code tarifaire:",
            'church_tax': "Option d'impôt ecclésiastique:",
            'number_of_children': "Nombre d'enfants:",
            'language_region': "Sélectionner la région linguistique:",
            'select_cantons': "Sélectionner les cantons:",
            'monthly_income': "Revenu mensuel imposable (CHF)",
            'tax_rate': "Taux d'impôt à la source (%)",
            'source_tax_progression': "Progression du taux d'impôt à la source par canton (2025)",
            'income_range_text': "Plage de revenus",
            'no_data_available': "Aucune donnée disponible pour la combinaison sélectionnée de code tarifaire et d'option d'impôt ecclésiastique"
        },
        'it': {
            'income_range': "Seleziona intervallo di reddito (CHF):",
            'tarif_code': "Codice tariffa:",
            'church_tax': "Opzione imposta ecclesiastica:",
            'number_of_children': "Numero di figli:",
            'language_region': "Seleziona regione linguistica:",
            'select_cantons': "Seleziona cantoni:",
            'monthly_income': "Reddito mensile imponibile (CHF)",
            'tax_rate': "Aliquota d'imposta alla fonte (%)",
            'source_tax_progression': "Progressione dell'aliquota d'imposta alla fonte per cantone (2025)",
            'income_range_text': "Intervallo di reddito",
            'no_data_available': "Nessun dato disponibile per la combinazione selezionata di codice tariffa e opzione imposta ecclesiastica"
        }
    }

def get_tarif_translations():
    """
    Returns translations for tarif codes in different languages.
    """
    return {
        'en': {
            'A': 'A - Tariff for single persons',
            'B': 'B - Tariff for married sole earners',
            'C': 'C - Tariff for married double earners',
            'D': 'D - Tariff for persons who receive AHV contribution refunds',
            'E': 'E - Tariff for income taxed under the simplified procedure',
            'G': 'G - Tariff for replacement income not paid through employers',
            'H': 'H - Tariff for single persons with children',
            'L': 'L - Tariff for cross-border commuters from Germany (Tariff code A)',
            'M': 'M - Tariff for cross-border commuters from Germany (Tariff code B)',
            'N': 'N - Tariff for cross-border commuters from Germany (Tariff code C)',
            'P': 'P - Tariff for cross-border commuters from Germany (Tariff code H)',
            'Q': 'Q - Tariff for cross-border commuters from Germany (Tariff code G)'
        },
        'de': {
            'A': 'A - Tarif für alleinstehende Personen',
            'B': 'B - Tarif für verheiratete Alleinverdiener',
            'C': 'C - Tarif für verheiratete Doppelverdiener',
            'D': 'D - Tarif für Personen, denen Beiträge an die AHV zurückerstattet werden',
            'E': 'E - Tarif für Einkünfte, die im vereinfachten Abrechnungsverfahren besteuert werden',
            'G': 'G - Tarif für Ersatzeinkünfte, die nicht über die Arbeitgeber ausbezahlt werden',
            'H': 'H - Tarif für alleinstehende Personen mit Kindern',
            'L': 'L - Tarif für Grenzgänger aus Deutschland (Tarifcode A)',
            'M': 'M - Tarif für Grenzgänger aus Deutschland (Tarifcode B)',
            'N': 'N - Tarif für Grenzgänger aus Deutschland (Tarifcode C)',
            'P': 'P - Tarif für Grenzgänger aus Deutschland (Tarifcode H)',
            'Q': 'Q - Tarif für Grenzgänger aus Deutschland (Tarifcode G)'
        },
        'fr': {
            'A': 'A - Tarif pour personnes seules',
            'B': 'B - Tarif pour personnes mariées à revenu unique',
            'C': 'C - Tarif pour personnes mariées à double revenu',
            'D': 'D - Tarif pour personnes qui reçoivent des remboursements de cotisations AVS',
            'E': 'E - Tarif pour revenus imposés selon la procédure simplifiée',
            'G': 'G - Tarif pour revenus de remplacement non versés par les employeurs',
            'H': 'H - Tarif pour personnes seules avec enfants',
            'L': 'L - Tarif pour frontaliers d\'Allemagne (Code tarifaire A)',
            'M': 'M - Tarif pour frontaliers d\'Allemagne (Code tarifaire B)',
            'N': 'N - Tarif pour frontaliers d\'Allemagne (Code tarifaire C)',
            'P': 'P - Tarif pour frontaliers d\'Allemagne (Code tarifaire H)',
            'Q': 'Q - Tarif pour frontaliers d\'Allemagne (Code tarifaire G)'
        },
        'it': {
            'A': 'A - Tariffa per persone sole',
            'B': 'B - Tariffa per coniugi con reddito unico',
            'C': 'C - Tariffa per coniugi con doppio reddito',
            'D': 'D - Tariffa per persone che ricevono rimborsi di contributi AVS',
            'E': 'E - Tariffa per redditi tassati secondo la procedura semplificata',
            'G': 'G - Tariffa per redditi sostitutivi non versati dai datori di lavoro',
            'H': 'H - Tariffa per persone sole con figli',
            'L': 'L - Tariffa per frontalieri dalla Germania (Codice tariffa A)',
            'M': 'M - Tariffa per frontalieri dalla Germania (Codice tariffa B)',
            'N': 'N - Tariffa per frontalieri dalla Germania (Codice tariffa C)',
            'P': 'P - Tariffa per frontalieri dalla Germania (Codice tariffa H)',
            'Q': 'Q - Tariffa per frontalieri dalla Germania (Codice tariffa G)'
        }
    }

def get_kirchensteuer_translations():
    """
    Returns translations for church tax options in different languages.
    """
    return {
        'en': {
            'N': 'Without Church Tax',
            'Y': 'With Church Tax'
        },
        'de': {
            'N': 'Ohne Kirchensteuer',
            'Y': 'Mit Kirchensteuer'
        },
        'fr': {
            'N': 'Sans impôt ecclésiastique',
            'Y': 'Avec impôt ecclésiastique'
        },
        'it': {
            'N': 'Senza imposta ecclesiastica',
            'Y': 'Con imposta ecclesiastica'
        }
    }

def get_language_region_translations():
    """
    Returns translations for language regions in different languages.
    """
    return {
        'en': {
            'German': 'German',
            'French': 'French',
            'Italian': 'Italian',
            'Multilingual': 'Multilingual'
        },
        'de': {
            'German': 'Deutsch',
            'French': 'Französisch',
            'Italian': 'Italienisch',
            'Multilingual': 'Mehrsprachig'
        },
        'fr': {
            'German': 'Allemand',
            'French': 'Français',
            'Italian': 'Italien',
            'Multilingual': 'Multilingue'
        },
        'it': {
            'German': 'Tedesco',
            'French': 'Francese',
            'Italian': 'Italiano',
            'Multilingual': 'Multilingue'
        }
    }
