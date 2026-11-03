from datetime import date
from django.core.exceptions import ValidationError
from django.db import models


def _mois_entre(debut, fin):
    return (fin.year - debut.year) * 12 + fin.month - debut.month


class Rubrique(models.Model):
    nom = models.CharField(max_length=100, unique=True)
    parent = models.ForeignKey(
        "self", null=True, blank=True, on_delete=models.PROTECT,
        related_name="sous_rubriques", limit_choices_to={"parent__isnull": True},
        verbose_name="rubrique parente",
        help_text="Laisser vide pour une rubrique principale ; choisir par ex. « Téléphonie » pour Free ou Claro.",
    )

    class Meta:
        ordering = ["nom"]

    def clean(self):
        if self.parent_id and self.parent_id == self.pk:
            raise ValidationError("Une rubrique ne peut pas être sa propre parente.")
        if self.parent_id and self.pk and self.sous_rubriques.exists():
            raise ValidationError("Cette rubrique a des sous-rubriques : elle ne peut pas avoir de parente (un seul niveau).")

    def __str__(self):
        return f"{self.parent.nom} › {self.nom}" if self.parent_id else self.nom


class Contrat(models.Model):
    DEVISES = [("DOP", "Pesos dominicains (RD$)"), ("EUR", "Euros (€)")]
    PAYS = [("FR", "France"), ("DO", "République dominicaine")]

    rubrique = models.ForeignKey(Rubrique, on_delete=models.PROTECT)
    pays = models.CharField(max_length=2, choices=PAYS)
    nom = models.CharField(max_length=150)
    montant_mensuel = models.DecimalField(max_digits=12, decimal_places=2)
    devise = models.CharField(max_length=3, choices=DEVISES, default="DOP")
    date_debut = models.DateField()
    date_fin = models.DateField(null=True, blank=True, help_text="Laisser vide pour un abonnement sans échéance.")

    class Meta:
        ordering = ["rubrique__nom", "nom"]

    def __str__(self):
        return self.nom

    def en_cours(self):
        today = date.today()
        return self.date_debut <= today and (self.date_fin is None or self.date_fin >= today)

    def mois_restants(self):
        if not self.date_fin:
            return None
        today = date.today()
        if self.date_fin < today:
            return 0
        return max(0, _mois_entre(max(today, self.date_debut), self.date_fin))

    def total_restant(self):
        mois = self.mois_restants()
        return None if mois is None else self.montant_mensuel * mois


class TauxChange(models.Model):
    date = models.DateField(default=date.today)
    dop_par_eur = models.DecimalField("1 € = … DOP", max_digits=10, decimal_places=4)

    class Meta:
        ordering = ["-date", "-id"]
        verbose_name = "taux de change"
        verbose_name_plural = "taux de change"

    def __str__(self):
        return f"1 € = {self.dop_par_eur} DOP ({self.date:%d/%m/%Y})"
