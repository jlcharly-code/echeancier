from datetime import date, timedelta
from decimal import Decimal, ROUND_HALF_UP
from django.http import HttpResponse
from django.shortcuts import render
from .ics import construire_ics
from .models import Contrat, Rubrique, TauxChange

ZERO = Decimal("0")
CENT = Decimal("0.01")


def _vide():
    return {"DOP": ZERO, "EUR": ZERO}


def _en_eur(montants, taux):
    if taux is None:
        return None
    total = montants["EUR"] + montants["DOP"] / taux.dop_par_eur
    return total.quantize(CENT, rounding=ROUND_HALF_UP)


def _ligne(nom, m, r, taux, niveau=0, a_enfants=False):
    return {
        "nom": nom, "niveau": niveau, "a_enfants": a_enfants,
        "m_dop": m["DOP"], "m_eur": m["EUR"], "m_conv": _en_eur(m, taux),
        "r_dop": r["DOP"], "r_eur": r["EUR"], "r_conv": _en_eur(r, taux),
    }


def totaux(request):
    today = date.today()
    taux = TauxChange.objects.first()  # le plus récent
    noms_pays = dict(Contrat.PAYS)
    pays = request.GET.get("pays")
    if pays not in noms_pays:
        pays = None

    contrats = Contrat.objects.select_related("rubrique__parent")
    if pays:
        contrats = contrats.filter(pays=pays)

    donnees = {}  # id de rubrique -> montants propres
    par_pays = {}  # code pays -> montants
    total_m, total_r = _vide(), _vide()
    bientot = []

    for c in contrats:
        d = donnees.setdefault(c.rubrique_id, {"m": _vide(), "r": _vide()})
        p = par_pays.setdefault(c.pays, {"m": _vide(), "r": _vide()})
        if c.en_cours():
            d["m"][c.devise] += c.montant_mensuel
            p["m"][c.devise] += c.montant_mensuel
            total_m[c.devise] += c.montant_mensuel
        restant = c.total_restant()
        if restant:
            d["r"][c.devise] += restant
            p["r"][c.devise] += restant
            total_r[c.devise] += restant
        if c.date_fin and today <= c.date_fin <= today + timedelta(days=90):
            bientot.append(c)

    rubriques = []
    for top in Rubrique.objects.filter(parent__isnull=True).prefetch_related("sous_rubriques"):
        enfants = [(s, donnees[s.pk]) for s in top.sous_rubriques.all() if s.pk in donnees]
        propres = donnees.get(top.pk)
        if propres is None and not enfants:
            continue
        m, r = _vide(), _vide()
        for d in ([propres] if propres else []) + [e[1] for e in enfants]:
            for dev in m:
                m[dev] += d["m"][dev]
                r[dev] += d["r"][dev]
        rubriques.append(_ligne(top.nom, m, r, taux, 0, bool(enfants)))
        for s, d in enfants:
            rubriques.append(_ligne(s.nom, d["m"], d["r"], taux, 1))

    total = _ligne("TOTAL", total_m, total_r, taux)
    lignes_pays = [
        _ligne(noms_pays[code], par_pays[code]["m"], par_pays[code]["r"], taux)
        for code in noms_pays if code in par_pays
    ]
    return render(request, "suivi/totaux.html", {
        "rubriques": rubriques, "total": total, "taux": taux, "bientot": bientot,
        "pays": pays, "pays_nom": noms_pays.get(pays), "pays_choix": Contrat.PAYS,
        "lignes_pays": lignes_pays,
    })


def calendrier_ics(request):
    contrats = Contrat.objects.select_related("rubrique").filter(date_fin__gte=date.today())
    reponse = HttpResponse(construire_ics(contrats), content_type="text/calendar; charset=utf-8")
    reponse["Content-Disposition"] = 'attachment; filename="echeancier.ics"'
    return reponse
