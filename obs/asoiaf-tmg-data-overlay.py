import obspython as obs
from pathlib import Path
import threading
import websockets
from websockets.sync import server
import json

SETTINGS = None
WS_SERVER = None
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
    obs.obs_properties_add_int(props, "socket_port", "Socket Port", 0, 65000, 1)
    socket_btn = obs.obs_properties_add_button(props, "socket_btn", "Start Socket", _socket_toggle)

    obs.obs_properties_add_text(props, "_text_explain", "<b>Names of OBS Sources (Case sensitive)</b>", obs.OBS_TEXT_INFO)
    obs.obs_properties_add_text(props, "source_name_p1", "Player 1 Name", obs.OBS_TEXT_DEFAULT)
    obs.obs_properties_add_text(props, "source_vp_p1", "Player 1 VPs", obs.OBS_TEXT_DEFAULT)
    obs.obs_properties_add_text(props, "source_name_p2", "Player 2 Name", obs.OBS_TEXT_DEFAULT)
    obs.obs_properties_add_text(props, "source_vp_p2", "Player 2 VPs", obs.OBS_TEXT_DEFAULT)
    obs.obs_properties_add_text(props, "source_round_number", "Round Number", obs.OBS_TEXT_DEFAULT)

    obs.obs_properties_add_text(props, "source_img_slot_1", "Image Slot 1", obs.OBS_TEXT_DEFAULT)
    obs.obs_properties_add_text(props, "source_img_slot_2", "Image Slot 2", obs.OBS_TEXT_DEFAULT)
    obs.obs_properties_add_text(props, "source_img_slot_3", "Image Slot 3", obs.OBS_TEXT_DEFAULT)
    obs.obs_properties_add_text(props, "source_img_slot_4", "Image Slot 4", obs.OBS_TEXT_DEFAULT)

    return props


def _socket_toggle(props, prop, *args, **kwargs):
    socket_btn = obs.obs_properties_get(props, "socket_btn")
    obs.obs_property_set_description(socket_btn, "Stop Socket" if WS_SERVER is None else "Start Socket")

    if WS_SERVER is None:
        start_thread()
    else:
        stop_websocket()

    return True


def script_defaults(settings):
    obs.obs_data_set_default_int(settings, "socket_port", 9999)


def start_thread(*args):
    threading.Thread(target=start_websocket, daemon=True).start()


def on_message(ws):
    for message in ws:
        parts = message.split(";")
        if parts[0] == "SYNC":
            on_SYNC(parts[1:])


def on_SYNC(parts):
    [ix_first_player, round_number, player_names, vps, cards_to_show] = parts

    update_text_source("source_round_number", round_number)
    update_text_source("source_name_p1", player_names.split(",")[0] or "Player 1")
    update_text_source("source_name_p2", player_names.split(",")[1] or "Player 2")
    update_text_source("source_vp_p1", vps.split(",")[0] or "0")
    update_text_source("source_vp_p2", vps.split(",")[1] or "0")

    for ix, card in enumerate(cards_to_show.split(",")):
        update_image_source(f"source_img_slot_{ix + 1}", card)


def update_text_source(source_key, new_text):
    source_name = json.loads(obs.obs_data_get_json(SETTINGS)).get(source_key)
    source = obs.obs_get_source_by_name(source_name)
    if source is None:
        print(f"ERROR: Was not able to find source: '{source_name}' for key '{source_key}'")

    settings = obs.obs_data_create()
    obs.obs_data_set_string(settings, "text", new_text)

    obs.obs_source_update(source, settings)
    obs.obs_data_release(settings)
    obs.obs_source_release(source)


def update_image_source(source_key, new_image):
    source_name = json.loads(obs.obs_data_get_json(SETTINGS)).get(source_key)
    source = obs.obs_get_source_by_name(source_name)

    repo_path = json.loads(obs.obs_data_get_json(SETTINGS)).get("repo_path")
    if new_image == "":
        image_url = "./obs/blank.png"
    else:
        image_url = f"./generated/en/{new_image}.jpg"

    local_image_path = str(Path(repo_path).joinpath(Path(image_url)))
    image_settings = obs.obs_data_create()
    obs.obs_data_set_string(image_settings, "file", local_image_path)
    obs.obs_source_update(source, image_settings)

    obs.obs_data_release(image_settings)

    obs.obs_source_release(source)


def start_websocket():
    global WS_SERVER
    port = json.loads(obs.obs_data_get_json(SETTINGS)).get("socket_port")

    with websockets.sync.server.serve(on_message, "localhost", port) as WS_SERVER:
        print(f"Starting websocket on ws://localhost:{port}")
        WS_SERVER.serve_forever()


def stop_websocket(*args):
    print("Stopping websocket...")
    global WS_SERVER
    if WS_SERVER is not None:
        WS_SERVER.shutdown()
    WS_SERVER = None


def script_load(settings):
    print("Loaded script.")
    global SETTINGS
    SETTINGS = settings


def script_unload():
    stop_websocket()
