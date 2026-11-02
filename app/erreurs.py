"""Messages d'erreur en français (FastAPI les renvoie en anglais par défaut)."""

MESSAGES_HTTP = {
    "Not Found": "Ressource introuvable",
    "Method Not Allowed": "Méthode non autorisée",
}


def traduire_erreur(erreur: dict) -> str:
    type_erreur = erreur.get("type", "")
    ctx = erreur.get("ctx", {})
    if type_erreur == "missing":
        return "Champ obligatoire"
    if type_erreur == "string_too_short":
        return f"Texte trop court (minimum {ctx.get('min_length')} caractère(s))"
    if type_erreur == "string_too_long":
        return f"Texte trop long (maximum {ctx.get('max_length')} caractères)"
    if type_erreur == "string_pattern_mismatch":
        return "Format invalide"
    if type_erreur in ("int_parsing", "int_from_float"):
        return "Doit être un nombre entier"
    if type_erreur == "greater_than_equal":
        return f"Doit être supérieur ou égal à {ctx.get('ge')}"
    if type_erreur == "less_than_equal":
        return f"Doit être inférieur ou égal à {ctx.get('le')}"
    if type_erreur == "string_type":
        return "Doit être du texte"
    if type_erreur == "json_invalid":
        return "JSON invalide"
    return "Valeur invalide"


def traduire_erreurs_validation(erreurs: list) -> list:
    resultat = []
    for e in erreurs:
        loc = e.get("loc", ())
        champ = ".".join(str(p) for p in loc[1:]) or "requête"
        resultat.append({"champ": champ, "message": traduire_erreur(e)})
    return resultat
