import logging
import random
from struct import unpack
from hashlib import md5

from django.db import IntegrityError

from rest_framework import viewsets, serializers
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from src.contrib.permission import AuthOnly

from src.apps.distributed_efforts.services import RatingNetworkPairerService
from src.apps.runs.models import Run
from src.apps.runs.serializers import RunSerializerForClient
from src.apps.trainings.models import Network
from src.apps.trainings.serializers import NetworkSerializerForTasks
from src.apps.startposes.models import StartPos
from src.apps.distributed_efforts.models import UserLastVersion

logger = logging.getLogger(__name__)

class TaskCreateSerializer(serializers.Serializer):
    allow_rating_task = serializers.BooleanField(default=True)
    allow_selfplay_task = serializers.BooleanField(default=True)
    task_rep_factor = serializers.IntegerField(default=1)
    git_revision = serializers.CharField(default="", allow_blank=True)
    client_instance_id = serializers.CharField(default="", allow_blank=True)

    def validate(self, data):
        if not data.get('allow_rating_task') and not data.get('allow_selfplay_task'):
            raise Response({"error": "allow_rating_task and allow_selfplay_task are both false"},status=400)
        return data

class DistributedTaskViewSet(viewsets.ViewSet):
    permission_classes = [AuthOnly]

    # noinspection PyMethodMayBeStatic
    def create(self, request):
        current_run = Run.objects.select_current()
        if current_run is None:
            return Response({"error": "No active run."}, status=404)
        if not request.user:
            return Response({"error": "Unknown user."}, status=403)
        if not current_run.is_allowed_username(request.user.username):
            return Response({"error": "This run is currently closed except for private testing."}, status=403)

        serializer = TaskCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        git_revision = str(data["git_revision"])
        # Git revision hashes are at least 40 chars, we can also optionally allow plus revisions and other stuff
        if len(git_revision) < 40 or len(git_revision) > 80:
            return Response(
                {"error": "This version of KataGo is not usable for distributed because either it's had custom modifications or has been compiled without version info."},
                status=400,
            )
        elif not current_run.is_git_in_whitelist(git_revision):
            return Response(
                {"error": "This version of KataGo is not enabled for distributed. If this exact version was working previously, then changes in the run require a newer version - please update KataGo to the latest version or release. But if this is already the official newest version of KataGo, or you think that not enabling this version is an oversight, please ask server admins to enable the following version hash: " + git_revision},
                status=400,
            )

        # Update server records of what version of the client the user is using
        try:
            UserLastVersion.objects.update_or_create(
                user=request.user,
                defaults={"git_revision": git_revision}
            )
        # Make sure that on a db race between django instances, we don't fail, recording stuff in this table is only informational
        except IntegrityError:
            pass

        allow_rating_task = data["allow_rating_task"]
        allow_selfplay_task = data["allow_selfplay_task"]
        if not allow_rating_task and current_run.rating_game_probability >= 1.0:
            return Response({"error": "allow_rating_task is false but this server is only serving rating games right now"},status=400)
        if not allow_selfplay_task and current_run.rating_game_probability <= 0.0:
            return Response({"error": "allow_selfplay_task is false but this server is only serving selfplay games right now"},status=400)

        task_rep_factor = data["task_rep_factor"]
        if task_rep_factor < 1 or task_rep_factor > 64:
            return Response({"error": "task_rep_factor was not an integer from 1 to 64"},status=400)

        serializer_context = {"request": request}  # Used by NetworkSerializer hyperlinked field to build and url ref
        run_content = RunSerializerForClient(current_run, context=serializer_context)

        network_delay = None
        if current_run.max_network_usage_delay > 0:
            min_delay = current_run.min_network_usage_delay
            max_delay = current_run.max_network_usage_delay
            (min_delay,max_delay) = (min(min_delay,max_delay),max(min_delay,max_delay))
            if min_delay < 0:
                min_delay = 0
            delay_seed = str(data["client_instance_id"]) + ":" + request.user.username
            randval = float(unpack('L', md5(delay_seed.encode("utf-8")).digest()[:8])[0]) / 2**64
            network_delay = min_delay + (max_delay - min_delay) * randval

        if not allow_selfplay_task or (allow_rating_task and random.random() < current_run.rating_game_probability):
            pairer = RatingNetworkPairerService(current_run, network_delay)
            pairing = pairer.generate_pairing()
            if pairing is not None:
                (white_network, black_network) = pairing
                white_network_content = NetworkSerializerForTasks(white_network, context=serializer_context)
                black_network_content = NetworkSerializerForTasks(black_network, context=serializer_context)
                response_body = {
                    "kind": "rating",
                    "run": run_content.data,
                    "config": current_run.rating_client_config,
                    "white_network": white_network_content.data,
                    "black_network": black_network_content.data,
                }
                return Response(response_body)

        start_poses = []
        for rep in range(task_rep_factor):
            if not current_run.startpos_locked and random.random() < current_run.selfplay_startpos_probability:
                start_pos = StartPos.objects.select_weighted_random()
                if start_pos is not None:
                    start_poses.append(start_pos.data)

        try:
            best_network = Network.objects.select_most_recent(current_run,for_training_games=True,network_delay=network_delay)
            if best_network is None:
                return Response({"error": "No networks found for run enabled for training games."}, status=400)
        except Network.DoesNotExist:
            return Response({"error": "No networks found for run enabled for training games."}, status=400)

        best_network_content = NetworkSerializerForTasks(best_network, context=serializer_context)
        response_body = {
            "kind": "selfplay",
            "run": run_content.data,
            "config": current_run.selfplay_client_config,
            "network": best_network_content.data,
            "start_poses": start_poses,
        }
        return Response(response_body)
