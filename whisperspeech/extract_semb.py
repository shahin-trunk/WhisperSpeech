# AUTOGENERATED! DO NOT EDIT! File to edit: ../nbs/2C. Whisper semantic embedding extraction.ipynb.

# %% auto 0
__all__ = ['load_model', 'encode_semantic', 'extract_semantic']

# %% ../nbs/2C. Whisper semantic embedding extraction.ipynb 3
import torch
import torchaudio

from pathlib import Path
from fastprogress import progress_bar, master_bar
from fastcore.script import *

import whisper
from .extract_acoustic import load

# %% ../nbs/2C. Whisper semantic embedding extraction.ipynb 7
def load_model():
    return whisper.load_model('tiny.en')

# %% ../nbs/2C. Whisper semantic embedding extraction.ipynb 28
# same as above but rolled into a function
def encode_semantic(whmodel, audio):
    """Encode the given `audio` (tensor or file name) into Whisper embeddings and lists of text tokens.
    Uses the given `whmodel` (see `load_model`).
    """
    if isinstance(audio, (Path, str)):
        audio = load(audio, newsr=whisper.audio.SAMPLE_RATE)
    mel = whisper.log_mel_spectrogram(audio[0,0])
    embs = []
    toks = []
    for start in range(0, mel.shape[-1], whisper.audio.N_FRAMES):
        sample = mel[:,start:]
        with torch.no_grad():
            padded = whisper.audio.pad_or_trim(sample, whisper.audio.N_FRAMES).unsqueeze(0)
            emb = whmodel.encoder(padded)
            tokens = whmodel.decode(emb, whisper.DecodingOptions(language='en', suppress_blank=False, suppress_tokens=False))[0].tokens
            embs.append(emb.cpu())
            toks.append(tokens)
    return torch.stack(embs, axis=0), toks

# %% ../nbs/2C. Whisper semantic embedding extraction.ipynb 30
@call_parse
def extract_semantic(
        srcdir:Path,  # source dir, should contain *.flac files
        outdir:Path,  # output dir, will get the *.semb and *.ttoks files
        layer='last', # the layer to extract the embeddings from
    ): 
    "Convert audio files to .semb files with Whisper embeddings and .ttoks with text tokens"
    model = load_model()
    suffix = '.semb'
    
    if layer != 'last':
        layer = int(layer)
        N = len(model.encoder.blocks)
        for i in range(N,layer,-1):
            print("Removing layer", i)
            del model.encoder.blocks[i-1]
        model.encoder.ln_post = torch.nn.Identity()
        suffix += f'-{layer}'
    
    outdir.mkdir(exist_ok=True, parents=True)
    for name in progress_bar(list(srcdir.rglob('*.flac'))):
        embs, toks = encode_semantic(model, name)
        torch.save(embs, outdir/name.with_suffix(suffix).name)
        torch.save(toks, outdir/name.with_suffix('.ttoks').name)
