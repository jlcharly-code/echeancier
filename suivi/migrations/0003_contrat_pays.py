from django.db import migrations, models


def deviner_pays(apps, schema_editor):
    """Contrats existants : ceux en pesos sont rattachés à la République dominicaine, les autres à la France.
    À vérifier ensuite dans l'administration."""
    Contrat = apps.get_model("suivi", "Contrat")
    Contrat.objects.filter(devise="DOP").update(pays="DO")


class Migration(migrations.Migration):

    dependencies = [
        ("suivi", "0002_rubrique_parent"),
    ]

    operations = [
        migrations.AddField(
            model_name="contrat",
            name="pays",
            field=models.CharField(choices=[("FR", "France"), ("DO", "République dominicaine")], default="FR", max_length=2),
            preserve_default=False,
        ),
        migrations.RunPython(deviner_pays, migrations.RunPython.noop),
    ]
