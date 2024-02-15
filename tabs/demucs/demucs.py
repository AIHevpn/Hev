import gradio as gr
import os
from scipy.io.wavfile import write

def inference(audio):
  os.makedirs("out", exist_ok=True)
  write('test.wav', audio[0], audio[1])
  os.system("python3 -m demucs.separate -n mdx_extra test.wav -o out")
  return ".tabs/demucs/mdx_extra/test/vocals.wav",".tabs/demucs/mdx_extra/test/bass.wav",\
".tabs/demucs/mdx_extra/test/drums.wav",".tabs/demucs/mdx_extra/test/other.wav"

description = "Gradio demo for Demucs: Music Source Separation in the Waveform Domain. To use it, simply upload your audio, or click one of the examples to load them. Read more at the links below. This space will be switched to GPU only when I need it :)"
article = "<p style='text-align: center'><a href='https://arxiv.org/abs/1911.13254' target='_blank'>Music Source Separation in the Waveform Domain</a> | <a href='https://github.com/facebookresearch/demucs' target='_blank'>Github Repo</a></p>"

examples=[['test.mp3']]

def demucs_tab():
iface = gr.Interface(
  inference,
  gr.inputs.Audio(type="numpy", label="Input"),
  [gr.outputs.Audio(type="file", label="Vocals"),gr.outputs.Audio(type="file", label="Bass"),gr.outputs.Audio(type="file", label="Drums"),gr.outputs.Audio(type="file", label="Other")],
  examples=examples
  )
