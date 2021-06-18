from flask import jsonify, Response

from omnimatsoo.handlers import aggr_blueprint
from omnimatsoo.services import ServiceClients as SVC


@aggr_blueprint.route("/", methods=["GET"])
def get_types():
    return Response("/all/, /playable-latency/<nodes>/, /playback-duration/<nodes>, /event/<event-name>/<nodes>/")


@aggr_blueprint.route("/all/", methods=["GET"])
def get_all():
    return jsonify(SVC.playback_benchmark.list_all())


@aggr_blueprint.route("/event/<event>/<nodes>/", methods=["GET"])
def get_num_events(event, nodes):
    return _get_node_aggr(
        handler=SVC.playback_benchmark.group_by_nodes_num_events,
        event_name=event,
        nodes=nodes,
    )


@aggr_blueprint.route("/playable-latency/<nodes>/", methods=["GET"])
def get_playablelatency(nodes):
    return _get_node_aggr(
        handler=SVC.playback_benchmark.group_by_nodes_playable,
        nodes=nodes,
    )


@aggr_blueprint.route("/playback-duration/<nodes>/", methods=["GET"])
def get_playbackduration(nodes):
    return _get_node_aggr(
        handler=SVC.playback_benchmark.group_by_nodes_playback_duration,
        nodes=nodes,
    )


def _get_node_aggr(handler, **kwargs):
    if "nodes" not in kwargs:
        return Response(
            response=f'bad request: "{kwargs}"',
            status=400,
            content_type="application/json",
        )
    nodes = kwargs["nodes"]
    pnodes = nodes.split(",")
    if not pnodes or not len(pnodes := list(map(int, filter(None, pnodes)))):
        return Response(
            response=f'wrong parameter format: "{nodes}"',
            status=400,
            content_type="application/json",
        )
    kwargs["nodes"] = pnodes
    try:
        ret = jsonify(handler(**kwargs))
    except IndexError:
        return Response(
            response=f'bad node numbers specified: "{nodes}"',
            status=400,
            content_type="application/json",
        )
    return ret
