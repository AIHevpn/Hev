import os, sys
import gradio as gr
import regex as re
import shutil
import datetime
import random
import yt_dlp


from core import (
    run_infer_script,
    run_batch_infer_script,
)

from assets.i18n.i18n import I18nAuto

from rvc.lib.utils import format_title

i18n = I18nAuto()

now_dir = os.getcwd()
sys.path.append(now_dir)

model_root = os.path.join(now_dir, "logs")
audio_root = os.path.join(now_dir, "assets", "audios")

model_root_relative = os.path.relpath(model_root, now_dir)
audio_root_relative = os.path.relpath(audio_root, now_dir)

sup_audioext = {
    "wav",
    "mp3",
    "flac",
    "ogg",
    "opus",
    "m4a",
    "mp4",
    "aac",
    "alac",
    "wma",
    "aiff",
    "webm",
    "ac3",
}

names = [
    os.path.join(root, file)
    for root, _, files in os.walk(model_root_relative, topdown=False)
    for file in files
    if (
        file.endswith((".pth", ".onnx"))
        and not (file.startswith("G_") or file.startswith("D_"))
    )
]

indexes_list = [
    os.path.join(root, name)
    for root, _, files in os.walk(model_root_relative, topdown=False)
    for name in files
    if name.endswith(".index") and "trained" not in name
]

audio_paths = [
    os.path.join(root, name)
    for root, _, files in os.walk(audio_root_relative, topdown=False)
    for name in files
    if name.endswith(tuple(sup_audioext))
    and root == audio_root_relative
    and "_output" not in name
]


def output_path_fn(input_audio_path):
    original_name_without_extension = os.path.basename(input_audio_path).rsplit(".", 1)[
        0
    ]
    new_name = original_name_without_extension + "_output.wav"
    output_path = os.path.join(os.path.dirname(input_audio_path), new_name)
    return output_path


def change_choices():
    names = [
        os.path.join(root, file)
        for root, _, files in os.walk(model_root_relative, topdown=False)
        for file in files
        if (
            file.endswith((".pth", ".onnx"))
            and not (file.startswith("G_") or file.startswith("D_"))
        )
    ]

    indexes_list = [
        os.path.join(root, name)
        for root, _, files in os.walk(model_root_relative, topdown=False)
        for name in files
        if name.endswith(".index") and "trained" not in name
    ]

    audio_paths = [
        os.path.join(root, name)
        for root, _, files in os.walk(audio_root_relative, topdown=False)
        for name in files
        if name.endswith(tuple(sup_audioext))
        and root == audio_root_relative
        and "_output" not in name
    ]

    return (
        {"choices": sorted(names), "__type__": "update"},
        {"choices": sorted(indexes_list), "__type__": "update"},
        {"choices": sorted(audio_paths), "__type__": "update"},
    )


def get_indexes():
    indexes_list = [
        os.path.join(dirpath, filename)
        for dirpath, _, filenames in os.walk(model_root_relative)
        for filename in filenames
        if filename.endswith(".index") and "trained" not in filename
    ]

    return indexes_list if indexes_list else ""


def save_to_wav(record_button):
    if record_button is None:
        pass
    else:
        path_to_file = record_button
        new_name = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S") + ".wav"
        target_path = os.path.join(audio_root_relative, os.path.basename(new_name))

        shutil.move(path_to_file, target_path)
        return target_path, output_path_fn(target_path)


def save_to_wav2(upload_audio):
    file_path = upload_audio
    formated_name = format_title(os.path.basename(file_path))
    target_path = os.path.join(audio_root_relative, formated_name)

    if os.path.exists(target_path):
        os.remove(target_path)

    shutil.copy(file_path, target_path)
    return target_path, output_path_fn(target_path)


def delete_outputs():
    gr.Info(f"Outputs cleared!")
    for root, _, files in os.walk(audio_root_relative, topdown=False):
        for name in files:
            if name.endswith(tuple(sup_audioext)) and name.__contains__("_output"):
                os.remove(os.path.join(root, name))


def match_index(model_file_value):
    if model_file_value:
        model_folder = os.path.dirname(model_file_value)
        index_files = get_indexes()
        for index_file in index_files:
            if os.path.dirname(index_file) == model_folder:
                return index_file
    return ""




def get_youtube_video_id(url, ignore_playlist=True):
    """
    Examples:
    http://youtu.be/SA2iWivDJiE
    http://www.youtube.com/watch?v=_oPAwA_Udwc&feature=feedu
    http://www.youtube.com/embed/SA2iWivDJiE
    http://www.youtube.com/v/SA2iWivDJiE?version=3&amp;hl=en_US
    """
    query = urlparse(url)
    if query.hostname == 'youtu.be':
        if query.path[1:] == 'watch':
            return query.query[2:]
        return query.path[1:]

    if query.hostname in {'www.youtube.com', 'youtube.com', 'music.youtube.com'}:
        if not ignore_playlist:
            # use case: get playlist id not current video in playlist
            with suppress(KeyError):
                return parse_qs(query.query)['list'][0]
        if query.path == '/watch':
            return parse_qs(query.query)['v'][0]
        if query.path[:7] == '/watch/':
            return query.path.split('/')[1]
        if query.path[:7] == '/embed/':
            return query.path.split('/')[2]
        if query.path[:3] == '/v/':
            return query.path.split('/')[2]

    # returns None for invalid YouTube url
    return None


def yt_download(link, cfile):
    ydl_opts = {
        'format': 'bestaudio',
        'outtmpl': 'assets/audios/{cfile}',
        'nocheckcertificate': True,
        'ignoreerrors': True,
        'no_warnings': True,
        'quiet': True,
        'extractaudio': True,
        'postprocessors': [{'key': 'FFmpegExtractAudio', 'preferredcodec': 'wav'}],
    }
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        result = ydl.extract_info(link, download=True)
        download_path = ydl.prepare_filename(result, outtmpl='assets/audios/{cfile}.wav')

    return download_path




# Inference tab
def inference_tab():
    default_weight = random.choice(names) if names else None
    with gr.Row():
        with gr.Row():
            model_file = gr.Dropdown(
                label=i18n("Voice Model"),
                choices=sorted(names, key=lambda path: os.path.getsize(path)),
                interactive=True,
                value=default_weight,
                allow_custom_value=True,
            )

            index_file = gr.Dropdown(
                label=i18n("Index File"),
                choices=get_indexes(),
                value=match_index(default_weight) if default_weight else "",
                interactive=True,
                allow_custom_value=True,
            )
        with gr.Column():
            refresh_button = gr.Button(i18n("Refresh"))
            unload_button = gr.Button(i18n("Unload Voice"))

            unload_button.click(
                fn=lambda: (
                    {"value": "", "__type__": "update"},
                    {"value": "", "__type__": "update"},
                ),
                inputs=[],
                outputs=[model_file, index_file],
            )

            model_file.select(
                fn=lambda model_file_value: match_index(model_file_value),
                inputs=[model_file],
                outputs=[index_file],
            )
    # download acappela tab
    with gr.Tab("download acapella"):
        with gr.Column():
            link = gr.Textbox(
                label=("input Audio")
            )
            cfile = gr.Textbox(
                label=("name Audio (No space)")
             )
            output = gr.Audio(
                label=("Output")
            ),
            
            download = gr.Button(label=("download audio!"),
            
            download_button.click(
            fn=yt_download,
            inputs=[link, cfile],
            outputs=[output],
            )
                
    # Single inference tab
    with gr.Tab(i18n("Single")):
        with gr.Column():
            upload_audio = gr.Audio(
                label=i18n("Upload Audio"), type="filepath", editable=False
            )
            with gr.Row():
                audio = gr.Dropdown(
                    label=i18n("Select Audio"),
                    choices=sorted(audio_paths),
                    value=audio_paths[0] if audio_paths else "",
                    interactive=True,
                    allow_custom_value=True,
                )

        with gr.Accordion(i18n("Advanced Settings"), open=False):
            with gr.Column():
                clear_outputs_infer = gr.Button(
                    i18n("Clear Outputs (Deletes all audios in assets/audios)")
                )
                output_path = gr.Textbox(
                    label=i18n("Output Path"),
                    placeholder=i18n("Enter output path"),
                    value=(
                        output_path_fn(audio_paths[0])
                        if audio_paths
                        else os.path.join(now_dir, "assets", "audios", "output.wav")
                    ),
                    interactive=True,
                )
                split_audio = gr.Checkbox(
                    label=i18n("Split Audio"),
                    visible=True,
                    value=False,
                    interactive=True,
                )
                autotune = gr.Checkbox(
                    label=i18n("Autotune"),
                    visible=True,
                    value=False,
                    interactive=True,
                )
                pitch = gr.Slider(
                    minimum=-24,
                    maximum=24,
                    step=1,
                    label=i18n("Pitch"),
                    value=0,
                    interactive=True,
                )
                filter_radius = gr.Slider(
                    minimum=0,
                    maximum=7,
                    label=i18n(
                        "If >=3: apply median filtering to the harvested pitch results. The value represents the filter radius and can reduce breathiness"
                    ),
                    value=3,
                    step=1,
                    interactive=True,
                )
                index_rate = gr.Slider(
                    minimum=0,
                    maximum=1,
                    label=i18n("Search Feature Ratio"),
                    value=0.75,
                    interactive=True,
                )
                hop_length = gr.Slider(
                    minimum=1,
                    maximum=512,
                    step=1,
                    label=i18n("Hop Length"),
                    value=128,
                    interactive=True,
                )
            with gr.Column():
                f0method = gr.Radio(
                    label=i18n("Pitch extraction algorithm"),
                    choices=[
                        "crepe",
                        "crepe-tiny",
                        "rmvpe",
                        "fcpe",
                        "hybrid[rmvpe+fcpe]",
                        "hybrid[rmvpe+fcpe+crepe-tiny]",
                    ],
                    value="hybrid[rmvpe+fcpe]",
                    interactive=True,
                )

        convert_button1 = gr.Button(i18n("Convert"))

        with gr.Row():  # Defines output info + output audio download after conversion
            vc_output1 = gr.Textbox(label=i18n("Output Information"))
            vc_output2 = gr.Audio(label=i18n("Export Audio"))

    # Batch inference tab
    with gr.Tab(i18n("Batch")):
        with gr.Row():
            with gr.Column():
                input_folder_batch = gr.Textbox(
                    label=i18n("Input Folder"),
                    placeholder=i18n("Enter input path"),
                    value=os.path.join(now_dir, "assets", "audios"),
                    interactive=True,
                )
                output_folder_batch = gr.Textbox(
                    label=i18n("Output Folder"),
                    placeholder=i18n("Enter output path"),
                    value=os.path.join(now_dir, "assets", "audios"),
                    interactive=True,
                )
        with gr.Accordion(i18n("Advanced Settings"), open=False):
            with gr.Column():
                clear_outputs_batch = gr.Button(
                    i18n("Clear Outputs (Deletes all audios in assets/audios)")
                )
                split_audio_batch = gr.Checkbox(
                    label=i18n("Split Audio"),
                    visible=True,
                    value=False,
                    interactive=True,
                )
                autotune_batch = gr.Checkbox(
                    label=i18n("Autotune"),
                    visible=True,
                    value=False,
                    interactive=True,
                )
                pitch_batch = gr.Slider(
                    minimum=-24,
                    maximum=24,
                    step=1,
                    label=i18n("Pitch"),
                    value=0,
                    interactive=True,
                )
                filter_radius_batch = gr.Slider(
                    minimum=0,
                    maximum=7,
                    label=i18n(
                        "If >=3: apply median filtering to the harvested pitch results. The value represents the filter radius and can reduce breathiness"
                    ),
                    value=3,
                    step=1,
                    interactive=True,
                )
                index_rate_batch = gr.Slider(
                    minimum=0,
                    maximum=1,
                    label=i18n("Search Feature Ratio"),
                    value=0.75,
                    interactive=True,
                )
                hop_length_batch = gr.Slider(
                    minimum=1,
                    maximum=512,
                    step=1,
                    label=i18n("Hop Length"),
                    value=128,
                    interactive=True,
                )
            with gr.Column():
                f0method_batch = gr.Radio(
                    label=i18n("Pitch extraction algorithm"),
                    choices=[
                        "crepe",
                        "crepe-tiny",
                        "rmvpe",
                        "hybrid[rmvpe+fcpe]",
                    ],
                    value="rmvpe",
                    interactive=True,
                )

        convert_button2 = gr.Button(i18n("Convert"))

        with gr.Row():  # Defines output info + output audio download after conversion
            vc_output3 = gr.Textbox(label=i18n("Output Information"))

    def toggle_visible(checkbox):
        return {"visible": checkbox, "__type__": "update"}

    refresh_button.click(
        fn=change_choices,
        inputs=[],
        outputs=[model_file, index_file, audio],
    )
    audio.change(
        fn=output_path_fn,
        inputs=[audio],
        outputs=[output_path],
    )
    upload_audio.upload(
        fn=save_to_wav2,
        inputs=[upload_audio],
        outputs=[audio, output_path],
    )
    upload_audio.stop_recording(
        fn=save_to_wav,
        inputs=[upload_audio],
        outputs=[audio, output_path],
    )
    clear_outputs_infer.click(
        fn=delete_outputs,
        inputs=[],
        outputs=[],
    )
    clear_outputs_batch.click(
        fn=delete_outputs,
        inputs=[],
        outputs=[],
    )
    convert_button1.click(
        fn=run_infer_script,
        inputs=[
            pitch,
            filter_radius,
            index_rate,
            hop_length,
            f0method,
            audio,
            output_path,
            model_file,
            index_file,
            split_audio,
            autotune,
        ],
        outputs=[vc_output1, vc_output2],
    )
    convert_button2.click(
        fn=run_batch_infer_script,
        inputs=[
            pitch_batch,
            filter_radius_batch,
            index_rate_batch,
            hop_length_batch,
            f0method_batch,
            input_folder_batch,
            output_folder_batch,
            model_file,
            index_file,
            split_audio_batch,
            autotune_batch,
        ],
        outputs=[vc_output3],
    )
