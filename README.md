# Audio Collager

## Overview

Attempt to reconstruct target audio using snippets of source audio.

## Background

This tool is inspired by the Scott Johnson album *[John Somebody](https://scottjohnsoncomposer.com/compositions/johnsomebody.html)* ([this track](https://scottjohnsoncomposer.com/compositions/audioclips/InvoluntarySong.ogg) in particular) in which samples of speech and laughter are cut up, rearranged and looped to create rhythm and melody.


## Setup
* Python 3
* `pip install -r requirements.txt`

## Run
Here's a simple example run
```bash
 python collage_files.py -i toots.wav -s toots.wav -o tootssq.wav
```
Run `python collage_files.py --help` for more details.

## Examples

Let's begin with two breakbats:

* Black Heat [Zimba Ku](docs/audio/breaks/black_heat__zimba_ku.wav) ([source](https://www.youtube.com/watch?v=mybkf-H8mkA))
* The Winstons [Amen Brother](docs/audio/breaks/amen_brother.wav) ([source](https://www.youtube.com/watch?v=GxZuq57_bYM))

We want to recrreate the drum pattern of the former using audio from the latter.

```bash
python collage_files.py -i docs/audio/breaks/black_heat__zimba_ku.wav -s docs/audio/breaks/amen_brother.wav -o amen_zimba.wav -f sigmoid 
```
You can listen to the output [here](docs/audio/breaks/out/amen_zimba.wav)
