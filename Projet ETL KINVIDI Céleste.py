################ PROJET ETL ##############################

#On importe l'URL
url = "https://journal-officiel-datadila.opendatasoft.com/api/explore/v2.1/catalog/datasets/balo/records"


#On commence d'abord par créer une liste de nos banques
banques = [
    {"societes_noms": "Banque Populaire Méditérranée", "siren":"058801481"},{"societes_noms":"Banque Populaire Alsace Lorraine Champagne", "siren":"356801571"},{"societes_noms":"Banque Populaire du Nord", "siren": "457506566"},
    {"societes_noms":"Banque Populaire Bourgogne Franche-Comté ", "siren":"542820352"}, {"societes_noms":"Banque Populaire Val de France ", "siren":"549800373"}, {"societes_noms":"Banque Populaire Rives de Paris", "siren":"552002313"},
    {"societes_noms":"Bred - Banque Populaire", "siren":"552091795"}, {"societes_noms":"Banque Populaire du Sud","siren":"554200808"}, {"societes_noms":"Banque Populaire Occitane", "siren":"560801300"}, {"societes_noms":"Banque Populaire Auvergne Rhône Alpes", "siren":"605520071"},
    {"societes_noms":"Banque Populaire Aquitaine Centre Atlantique", "siren":"755501590"},{"societes_noms": "Banque Populaire Grand Ouest", "siren":"857500227"}]

#On construit une fonction pour localiser le produit net bancaire
def extraire_pnb(data,champ):
  for record in data["results"]:
    if "Comptes annuels" not in str(record.get("facette_categorie_libelle", "")):
        continue #On ne regarde que les comptes annuels

    texte = " ".join(str(record.get(champ, "")).split())
    pos = texte.lower().find("produit net bancaire")
    if pos == 1:
        continue

    mots = texte[pos:pos + 300].split()

    chiffres = []
    for mot in mots[3:]:
        if mot.isdigit():
            chiffres.append(mot)
        else:
            break

    if len(chiffres) >= 2 and len(chiffres) % 2 == 0:
        moitie = len(chiffres) // 2
        return {
            "n": int("".join(chiffres[:moitie])),
            "n-1": int("".join(chiffres[moitie:])),
            "date": record.get("dateparution"),
        }
  return None

print(extraire_pnb(data,"ftcontent"))

#Exemple :
import requests

siren = banques[0]["siren"]
params = {"limit":20, "where": f'siren="{siren}" and dateparution >= "2026-01-01"'}
r = requests.get(url, params=params)
r.raise_for_status()
data = r.json()

#On récupère le champ qui contien le texte du bilan
print(data["results"][0])

#Et on fait fonctionner la fonction
print(extraire_pnb(data, "ftcontent"))

print(data["total_count"])
for rec in data["results"]:
    print(rec["dateparution"], rec["facette_categorie_libelle"])
    print(str(rec["ftcontent"])[:300])
    print("---")
    
#On fait boucler sur les 12 banques
resultats = []
for banque in banques:
    siren = banque["siren"]
    nom = banque.get("societes_noms")
    params = {"limit":100, "where": f'siren="{siren}" and dateparution >= "2026-01-01"'}
    
    try:
        r = requests.get(url, params=params, timeout=30)
        r.raise_for_status()
        pnb = extraire_pnb(r.json(), "ftcontent")
    except requests.RequestException as e:
        print(f"Erreur pour {nom} : {e}")
        pnb = None
        
    print(nom, "->", pnb)
        
    resultats.append({
            "Banque": nom,
            "SIREN": siren,
            "Date de parution": pnb["date"]
 if pnb else None,
         "PNB année n": pnb["n"] if pnb
         else None,
         "PNB année n-1": pnb["n-1"] if pnb else None,})
    
    
#On importe le projet sur un fichier Excel
import pandas as pd
from pathlib import Path

df = pd.DataFrame(resultats)
chemin = Path.home() / "Downloads" / "PNB_banques.xlsx"   #Path.home permet de trouver automatiquement le dossier de l'utilisateur
df.to_excel(chemin, index=False)
print("Fichier enregistré :", chemin)