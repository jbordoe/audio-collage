#!/usr/bin/python
from moviepy.editor import *

import sys
import argparse

import cv2
import vptree
import numpy as np
import tempfile

from lib import util

parser=argparse.ArgumentParser(description='Create a collage based on a given audio file based on snippets from a video file')
parser.add_argument(
    '-i', '--source_file', type=str, required=True, help='Path of audio file to be replicated')
parser.add_argument(
    '-s', '--sample_file', type=str, required=True, help='Path of video file to be sampled.')
parser.add_argument(
    '-d', '--declick_ms', type=int, required=False, help='Decklick interval in milliseconds.')
parser.add_argument(
    '-f', '--declick_fn', type=str, choices=['sigmoid', 'linear'], required=False, help='Decklicking function.')
parser.add_argument(
    '-o', '--outpath', type=str, required=False, default='./collage.mp4', help='Path of output file.')

args = parser.parse_args()

sourcefile = args.source_file
samplefile = args.sample_file

outpath    = args.outpath

declick_fn = args.declick_fn
default_dc_ms = {
    'sigmoid': 20,
    'linear': 70,
}
if declick_fn:
    declick_ms = args.declick_ms or default_dc_ms[declick_fn]
else:
    declick_ms = 0

sample_audio = None

# Using moviepy here ot quickly extract the audio
# TODO: can this be done with opencv?
videoclip_mpy = VideoFileClip(samplefile)
with tempfile.TemporaryDirectory() as vid_audio_dir:
    print('Reading video file.')
    audioclip = videoclip_mpy.audio

    print('Extracting audio from video.')
    vid_audio_name = vid_audio_dir + '/temp.wav'
    audioclip.write_audiofile(vid_audio_name)
    sample_audio = util.Util.read_audio(vid_audio_name)

video_frames = []
print('Reading frames from  video file.')
videoclip = cv2.VideoCapture(samplefile)
while(True):
    # Capture each frame
    ret, frame = videoclip.read()

    if ret == True:
        video_frames.append(frame)
    else:
        break

samples = {}

windows = [1000,500]
windows = [i + declick_ms for i in windows]


print('Chopping sample audio.')
for window in windows:
    sample_group = util.Util.chop_audio(sample_audio, window)

    for s in sample_group:
        util.Util.extract_features(s)

    tree = vptree.VPTree(sample_group, util.Util.audio_dist)
    samples[window] = tree

selected_snippets = []

source_audio = util.Util.read_audio(sourcefile)
util.Util.extract_features(source_audio)
source_sr = source_audio.sample_rate

pointer = 0

vfps = videoclip.get(cv2.CAP_PROP_FPS)
# Video duration in seconds
vlen = (videoclip.get(cv2.CAP_PROP_FRAME_COUNT) / videoclip.get(cv2.CAP_PROP_FPS))
v_frames = len(video_frames) # could also use CAP_PROP_FRAME_COUNT
# ratio of video to audio frames
vf2as = v_frames / sample_audio.timeseries.size
# duration, in seconds of video represented by each audio sample
vs2as = vlen / sample_audio.timeseries.size

print('Generating collage with samples.')
while pointer < source_audio.timeseries.size:
    pct_complete = int((pointer / source_audio.timeseries.size) * 100) if pointer else 0
    pct_remaining = 100 - pct_complete

    sys.stdout.write('\r')
    sys.stdout.write('▓'*pct_complete + '_'*pct_remaining + '{}%'.format(pct_complete))
    sys.stdout.flush()

    best_snippet = None
    best_snippet_dist = 999999
    best_snippet_window = None
    for window in windows:
        window_size_frames = int((window / 1000) * source_sr)
        source_chunk = util.Util.AudioFile(
                source_audio.timeseries[pointer:pointer + window_size_frames - 1],
                source_sr,
                )
        util.Util.extract_features(source_chunk)

        group = samples[window]
        nearest_dist, nearest = group.get_nearest_neighbor(source_chunk)

        if nearest_dist < best_snippet_dist:
            best_snippet_dist = nearest_dist
            best_snippet = nearest
            best_snippet_window = window_size_frames

    v_start = int(min(
        best_snippet.offset_frames * vf2as,
	v_frames - 1
    ))
    v_end = int(min(
        (best_snippet.offset_frames + best_snippet.timeseries.size) * vf2as,
        v_frames - 1
    ))

    selected_snippets.append(video_frames[v_start:v_end])
    pointer += best_snippet_window - int((declick_ms /1000) * source_sr)


sys.stdout.write('\r')
print('Collage generated.')

#output_data = []
#i = 0
#for snippet in selected_snippets:
#    if declick_fn:
#        snippet = util.Util.declick(snippet, declick_fn, declick_ms)
#
#    x = snippet.timeseries
#    if declick_ms and output_data and i < len(selected_snippets)-1:
#        overlap_frames = int((declick_ms * snippet.sample_rate) / 1000)
#        overlap = np.add(output_data[-overlap_frames:], x[:overlap_frames])
#        output_data = output_data[:-overlap_frames]
#        x = np.concatenate([overlap, x[overlap_frames:]])
#
#    output_data.extend(x)
#    i += 1

print('Saving collage file.')
out = cv2.VideoWriter(
    outpath,
    int(videoclip.get(cv2.CAP_PROP_FOURCC)),
    vfps,
    (
        int(videoclip.get(cv2.CAP_PROP_FRAME_WIDTH)),
        int(videoclip.get(cv2.CAP_PROP_FRAME_HEIGHT))
    )
)

# Cleanup
videoclip.release()
out.release()
print('Done!')
