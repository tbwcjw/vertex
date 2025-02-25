from flask import Blueprint, Response, jsonify, request
from configloader import ConfigLoader
import pkg_resources

#not sure about this
__title__ = "vertex"
__author__ = "tbwcjw"
__email__ = "me@tbwcjw.online"
__license__ = "MIT"

config = ConfigLoader()
stats_bp = Blueprint('stats', __name__)

@stats_bp.route('/stats', methods=["GET"])
def handle_stats():
    #disabled outright
    if not config.get('stats.stats_enabled'):
        handle_invalid()

    mode = request.args.get('mode')

    cases = {
        #'everything': handle_everything,
        'version': handle_version,
        #'conn': handle_conn,
        #'torr': handle_torr
    }

    return cases.get(mode, handle_invalid)()

def handle_invalid():
    return Response("invalid mode", mimetype='text/plain')

def handle_version():
    if not config.get('stats.version_enabled'):
        handle_invalid()
    self_string = f"{__title__} - {__author__} <{__email__}> - {__license__} license\n\npackages:\n"
    installed_packages = pkg_resources.working_set
    packages_string = "\n".join([f"{package.project_name}=={package.version}" for package in installed_packages])
    return Response(self_string+packages_string, mimetype='text/plain')