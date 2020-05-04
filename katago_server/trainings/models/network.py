import os

from django.core.files.storage import FileSystemStorage
from math import log10, e

from django.contrib.postgres.fields import JSONField
from django.db.models import Model, BigIntegerField, IntegerField, FileField, CharField, DateTimeField, UUIDField, FloatField, \
    ForeignKey, PROTECT, BigAutoField, BooleanField
from django.utils.translation import gettext_lazy as _
from django.core.validators import RegexValidator

from katago_server.contrib.validators import FileValidator
from katago_server.runs.models import Run
from katago_server.trainings.managers.network_pd_manager import NetworkPdManager
from katago_server.trainings.managers.network_queryset import NetworkQuerySet

network_data_storage = FileSystemStorage(location="/data/network")

def upload_network_to(instance, _filename):
    return os.path.join("networks", f"{instance.name}.bin.gz")

validate_zip = FileValidator(max_size=1024 * 1024 * 1024, content_types=("application/zip",))
alphanumericdashes = RegexValidator(r'^[-0-9a-zA-Z]*$', 'Only alphanumeric or dash characters are allowed.')

class Network(Model):
    objects = NetworkQuerySet.as_manager()
    pd = NetworkPdManager()

    class Meta:
        verbose_name = _("Network")
        verbose_name_plural = _("Networks")
        ordering = ['-created_at']

    id = BigAutoField(primary_key=True)
    # TODO enforce that name is UNIQUE
    name = CharField(_("neural network name"), max_length=128, default="", validators=[alphanumericdashes], db_index=True)
    run = ForeignKey(Run, verbose_name=_("run"), on_delete=PROTECT, related_name="%(class)s_games", db_index=True)
    created_at = DateTimeField(_("creation date"), auto_now_add=True)
    parent_network = ForeignKey("self", null=True, blank=True, related_name="variants", on_delete=PROTECT)
    network_size = CharField(_("network size"), max_length=32, default="", help_text=_("String describing blocks and channels in network."))
    is_random = BooleanField(_("random"), default=False, help_text=_("If true, this network represents just random play rather than an actual network"))
    model_file = FileField(
        _("model file url"),
        upload_to=upload_network_to,
        validators=(validate_zip,),
        storage=network_data_storage,
        max_length=200,
        default="",
        help_text=_("Url to download network model file.")
    )
    model_file_bytes = BigIntegerField(_("model file bytes"), default=0,  help_text=_("Number of bytes in network model file."))
    model_file_sha256 = CharField(_("model file SHA256"), max_length=64, default="", help_text=_("SHA256 hash of network model file for integrity verification."))
    log_gamma = FloatField(_("log gamma"), default=0, help_text=_("Estimated BayesElo strength of network."))
    log_gamma_uncertainty = FloatField(_("log gamma uncertainty"), default=0, help_text=_("Estimated stdev of BayesElo strength of network."))
    log_gamma_lower_confidence = FloatField(
        _("log gamma lower confidence"), default=0, db_index=True, help_text=_("Lower confidence bound on BayesElo strength of network.")
    )
    log_gamma_upper_confidence = FloatField(
        _("log gamma upper confidence"), default=0, db_index=True, help_text=_("Upper confidence bound on BayesElo strength of network.")
    )

    def __str__(self):
        return f"net-{self.id} ({self.elo}±{2 * self.elo_uncertainty})"

    @property
    def size(self):
        return f"{self.network_size}"

    @property
    def elo(self):
        return round(self.log_gamma * 400 * log10(e), ndigits=1)

    @property
    def elo_uncertainty(self):
        return round(self.log_gamma_uncertainty * 400 * log10(e), ndigits=1)

    @property
    def ranking(self):
        return f"{self.elo} ±{2 * self.elo_uncertainty}"

    def save(self, *args, **kwargs):
        if not self.pk:  # only act on creation
            # default the parent net to actual last net
            if not self.parent_network:
                # Insert parent network
                self.parent_network = Network.objects.last()
        return super(Network, self).save(*args, **kwargs)
