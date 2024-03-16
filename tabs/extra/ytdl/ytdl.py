import gradio as gr
import yt_dlp

def download_youtube_audio(youtube_url, custom_file_name):
    # Define yt-dlp options
    ydl_opts = {
        'format': 'bestaudio/best',
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'wav',
            'preferredquality': '192',
        }],
        'outtmpl': f'{cfile}.wav',
    }
    
    # Download the audio
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        ydl.download([youtube_url])
    
    return f'Downloaded and saved as {cfile}.wav  Code by Blane'


def ytdl():
    with gr.Column():
        gr.Markdown("download youtube acappela"):
            youtube_url = gr.Textbox(
                label=("url to audio"),
                value="",
                max_lines=1,
                interactive=True,
                placeholder=("https://youtu.be/iN0-dRNsmRM?si=42PgawH73GIrvYLs"),
            )
            cfile = gr.Textbox(
                label=("custom file name"),
                value="",
                interactive=True,
                placeholder=("cfile"),
            )

        outputs = gr.Textbox(
            label=("Output Information"),
            value="",
        )

        ytdl_button = gr.Button(
            ("Fusion"), variant="primary", interactive=False
        )

        ytdl_button.click(
            ytdl,
            [
                url,
                cfile,
            ],
            outputs,
            api_name="ytdl",
        )

