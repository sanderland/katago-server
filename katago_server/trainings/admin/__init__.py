from django.contrib import admin
from solo.admin import SingletonModelAdmin

from katago_server.trainings.admin.network_admin import NetworkAdmin
from katago_server.trainings.models import Network, NetworkBayesianRankingConfiguration

admin.site.register(Network, NetworkAdmin)
admin.site.register(NetworkBayesianRankingConfiguration, SingletonModelAdmin)