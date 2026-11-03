"""Export iCalendar (.ics) des fins de contrat, sans dépendance externe."""
from datetime import date, datetime, timedelta, timezone

ALARMES_JOURS = (30, 7)  # rappels avant la fin du contrat


def _echapper(texte):
    return (texte.replace("\\", "\\\\").replace(";", "\\;")
            .replace(",", "\\,").replace("\n", "\\n"))


def _plier(ligne):
    """RFC 5545 : 75 octets max par ligne, suite = CRLF + espace."""
    if len(ligne.encode("utf-8")) <= 75:
        return ligne
    morceaux, courant, taille, limite = [], "", 0, 75
    for car in ligne:
        n = len(car.encode("utf-8"))
        if taille + n > limite:
            morceaux.append(courant)
            courant, taille, limite = car, n, 74
        else:
            courant += car
            taille += n
    morceaux.append(courant)
    return "\r\n ".join(morceaux)


def construire_ics(contrats):
    maintenant = datetime.now(timezone.utc)
    stamp = maintenant.strftime("%Y%m%dT%H%M%SZ")
    sequence = int(maintenant.timestamp())  # croît à chaque export : les agendas mettent à jour
    lignes = [
        "BEGIN:VCALENDAR",
        "VERSION:2.0",
        "PRODID:-//Echeancier//FR",
        "CALSCALE:GREGORIAN",
        "X-WR-CALNAME:Échéancier",
    ]
    for c in contrats:
        if not c.date_fin or c.date_fin < date.today():
            continue
        montant = format(c.montant_mensuel, ",.2f").replace(",", " ").replace(".", ",")
        detail = f"{c.nom} ({c.rubrique}, {c.get_pays_display()}) : {montant} {c.devise} par mois"
        lignes += [
            "BEGIN:VEVENT",
            f"UID:contrat-{c.pk}-fin@echeancier.local",
            f"DTSTAMP:{stamp}",
            f"SEQUENCE:{sequence}",
            f"DTSTART;VALUE=DATE:{c.date_fin:%Y%m%d}",
            f"DTEND;VALUE=DATE:{c.date_fin + timedelta(days=1):%Y%m%d}",
            f"SUMMARY:{_echapper('Fin de contrat : ' + c.nom)}",
            f"DESCRIPTION:{_echapper(detail)}",
        ]
        for jours in ALARMES_JOURS:
            lignes += [
                "BEGIN:VALARM",
                "ACTION:DISPLAY",
                f"DESCRIPTION:{_echapper(f'Dans {jours} jours : fin du contrat {c.nom}')}",
                f"TRIGGER:-P{jours}D",
                "END:VALARM",
            ]
        lignes.append("END:VEVENT")
    lignes.append("END:VCALENDAR")
    return "\r\n".join(_plier(l) for l in lignes) + "\r\n"
