"""Page /docs (Swagger UI) avec les textes de l'interface traduits en français.

Swagger UI n'a pas de version française : on ajoute un petit script qui
remplace les textes anglais connus par leur équivalent français.
"""
from fastapi.openapi.docs import get_swagger_ui_html

SCRIPT_TRADUCTION = """
<script>
(function () {
  var t = {
    "Try it out": "Essayer",
    "Execute": "Exécuter",
    "Cancel": "Annuler",
    "Clear": "Effacer",
    "Parameters": "Paramètres",
    "No parameters": "Aucun paramètre",
    "Request body": "Corps de la requête",
    "Responses": "Réponses",
    "Response body": "Corps de la réponse",
    "Response headers": "En-têtes de la réponse",
    "Response content type": "Type de contenu de la réponse",
    "Server response": "Réponse du serveur",
    "Request URL": "URL de la requête",
    "Name": "Nom",
    "Details": "Détails",
    "Links": "Liens",
    "No links": "Aucun lien",
    "Media type": "Type de média",
    "Example Value": "Exemple",
    "Example": "Exemple",
    "Schema": "Schéma",
    "Schemas": "Schémas",
    "Download": "Télécharger",
    "Successful Response": "Réponse réussie",
    "Validation Error": "Erreur de validation",
    "Controls Accept header.": "Contrôle l'en-tête Accept.",
    "Send empty value": "Envoyer une valeur vide",
    "No content": "Aucun contenu",
    "Undocumented": "Non documenté"
  };
  function traduire(racine) {
    var parcours = document.createTreeWalker(racine, NodeFilter.SHOW_TEXT);
    var noeud;
    while ((noeud = parcours.nextNode())) {
      var brut = noeud.nodeValue;
      var cle = brut.trim();
      if (Object.prototype.hasOwnProperty.call(t, cle)) {
        noeud.nodeValue = brut.replace(cle, t[cle]);
      }
    }
  }
  var enAttente = false;
  new MutationObserver(function () {
    if (enAttente) return;
    enAttente = true;
    setTimeout(function () { enAttente = false; traduire(document.body); }, 50);
  }).observe(document.body, { childList: true, subtree: true, characterData: true });
  traduire(document.body);
})();
</script>
"""


def page_documentation(titre: str) -> str:
    page = get_swagger_ui_html(openapi_url="/openapi.json", title=f"{titre} - Documentation")
    html = page.body.decode("utf-8")
    html = html.replace("<html>", '<html lang="fr">', 1)
    return html.replace("</body>", SCRIPT_TRADUCTION + "\n</body>")
