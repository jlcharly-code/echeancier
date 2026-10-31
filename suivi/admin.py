from django.contrib import admin
from .models import Rubrique, Contrat, TauxChange


@admin.register(Rubrique)
class RubriqueAdmin(admin.ModelAdmin):
    search_fields = ["nom"]


@admin.register(Contrat)
class ContratAdmin(admin.ModelAdmin):
    list_display = ["nom", "rubrique", "montant_mensuel", "devise", "date_debut", "date_fin", "mois_restants", "total_restant"]
    list_filter = ["rubrique", "devise"]
    search_fields = ["nom"]


@admin.register(TauxChange)
class TauxChangeAdmin(admin.ModelAdmin):
    list_display = ["date", "dop_par_eur"]
