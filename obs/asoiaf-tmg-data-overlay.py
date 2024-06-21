import os
import time
import obspython as obs
from pathlib import Path
import threading
import websockets
from websockets.sync import server
import json
from PIL import Image


SETTINGS = None
WS_SERVER = None
WS_PORT = 9999
DEFAULT_PATH = ""

try:
    DEFAULT_PATH = str(Path(f"{script_path()}/.."))
except:
    DEFAULT_PATH = str(Path.cwd())


def script_description():
    return """
    <p>Hook into asoiaf-tmg-data web server and create image sources.<p>
    """


def script_properties():
    props = obs.obs_properties_create()
    obs.obs_properties_add_path(props, "repo_path", "Repository Path", obs.OBS_PATH_DIRECTORY, "", DEFAULT_PATH)
    # obs.obs_properties_add_editable_list(props, "scenes", "Scene Whitelist", obs.OBS_EDITABLE_LIST_TYPE_STRINGS, None, None)
    obs.obs_properties_add_button(props, "start_socket", "Start Websocket", start_thread)
    obs.obs_properties_add_button(props, "stop_socket", "Stop Websocket", stop_websocket)

    return props


def script_defaults(settings):
    pass


def start_thread(*args):
    threading.Thread(target=start_websocket, daemon=True).start()


def on_message(ws):
    for message in ws:
        parts = message.split(";")
        if parts[0] == "SHOW":
            on_SHOW(parts[1:])
        elif parts[0] == "CLEAR":
            on_CLEAR()


def on_SHOW(images_to_show):
    clear_image_sources()
    if len(images_to_show) == 1:
        create_image_source(f"web/{images_to_show[0]}")


def on_CLEAR():
    clear_image_sources()


def clear_image_sources():
    scene = obs.obs_scene_from_source(obs.obs_frontend_get_current_scene())
    scene_item = obs.obs_scene_find_source(scene, "asoiaf-tmg-data")
    if scene_item is None:
        print("Clear Images: No scene item found.")
        return
    source = obs.obs_sceneitem_get_source(scene_item)
    if source is None:
        print("Clear Images: Source not found.")
        return

    obs.obs_source_remove(source)
    obs.obs_scene_release(scene)
    # janky race condition
    time.sleep(0.05)


def create_image_source(image_url):
    repo_path = json.loads(obs.obs_data_get_json(SETTINGS)).get("repo_path")
    local_image_path = str(Path(repo_path).joinpath(Path(image_url)))
    if not os.path.exists(local_image_path):
        print(f"File not found: {local_image_path}")
        return
    image_size = Image.open(local_image_path).height
    scale = int(48300 / image_size) / 100

    image_settings = obs.obs_data_create()
    obs.obs_data_set_string(image_settings, "file", local_image_path)
    image_source = obs.obs_source_create("image_source", "asoiaf-tmg-data", image_settings, None)
    scene = obs.obs_scene_from_source(obs.obs_frontend_get_current_scene())
    obs.obs_scene_add(scene, image_source)

    name = obs.obs_source_get_name(image_source)

    scene_item = obs.obs_scene_find_source(scene, name)
    image_location = obs.vec2()
    image_scale = obs.vec2()
    image_location.x = 10
    image_location.y = 480
    image_scale.x = scale
    image_scale.y = scale
    obs.obs_sceneitem_set_pos(scene_item, image_location)
    obs.obs_sceneitem_set_scale(scene_item, image_scale)

    obs.obs_source_update(image_source, image_settings)
    obs.obs_data_release(image_settings)
    obs.obs_source_release(image_source)
    obs.obs_scene_release(scene)


def start_websocket():
    global WS_SERVER
    with websockets.sync.server.serve(on_message, "localhost", WS_PORT) as WS_SERVER:
        print(f"Starting websocket on ws://localhost:{WS_PORT}")
        WS_SERVER.serve_forever()


def stop_websocket(*args):
    print("Stopping websocket...")
    if WS_SERVER is not None:
        WS_SERVER.shutdown()


def script_load(settings):
    print("Loaded script.")
    global SETTINGS
    SETTINGS = settings


def script_unload():
    stop_websocket()