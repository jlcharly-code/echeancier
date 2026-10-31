from datetime import date, timedelta
from decimal import Decimal, ROUND_HALF_UP
from django.shortcuts import render
from .models import Contrat, TauxChange

ZERO = Decimal("0")
CENT = Decimal("0.01")


def _vide():
    return {"DOP": ZERO, "EUR": ZERO}


def _en_eur(montants, taux):
    if taux is None:
        return None
    total = montants["EUR"] + montants["DOP"] / taux.dop_par_eur
    return total.quantize(CENT, rounding=ROUND_HALF_UP)


def totaux(request):
    today = date.today()
    taux = TauxChange.objects.first()  # le plus récent
    lignes = {}
    total_m, total_r = _vide(), _vide()
    bientot = []

    for c in Contrat.objects.select_related("rubrique"):
        l = lignes.setdefault(c.rubrique.nom, {"m": _vide(), "r": _vide()})
        if c.en_cours():
            l["m"][c.devise] += c.montant_mensuel
            total_m[c.devise] += c.montant_mensuel
        restant = c.total_restant()
        if restant:
            l["r"][c.devise] += restant
            total_r[c.devise] += restant
        if c.date_fin and today <= c.date_fin <= today + timedelta(days=90):
            bientot.append(c)

    rubriques = [
        {
            "nom": nom,
            "m_dop": l["m"]["DOP"], "m_eur": l["m"]["EUR"], "m_conv": _en_eur(l["m"], taux),
            "r_dop": l["r"]["DOP"], "r_eur": l["r"]["EUR"], "r_conv": _en_eur(l["r"], taux),
        }
        for nom, l in sorted(lignes.items())
    ]
    total = {
        "m_dop": total_m["DOP"], "m_eur": total_m["EUR"], "m_conv": _en_eur(total_m, taux),
        "r_dop": total_r["DOP"], "r_eur": total_r["EUR"], "r_conv": _en_eur(total_r, taux),
    }
    return render(request, "suivi/totaux.html", {
        "rubriques": rubriques, "total": total, "taux": taux, "bientot": bientot,
    })
