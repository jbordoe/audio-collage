from dataclasses import dataclass

import numpy as np
from numpy.linalg import norm
from dtw import accelerated_dtw as dtw

import librosa
import soundfile as sf
import math

class Util:
    @dataclass
    class AudioFile:
        timeseries: np.ndarray
        sample_rate: int
        offset_frames: int = None
        mfcc: np.ndarray = None
        chroma_stft: np.ndarray = None

    @staticmethod
    def read_audio(path):
        timeseries, sample_rate = librosa.load(path)
        return Util.AudioFile(timeseries, sample_rate)

    @staticmethod
    def save_audio(audiofile, path):
        sf.write(path, audiofile.timeseries, audiofile.sample_rate, format='wav')

    @staticmethod
    def chop_audio(audiofile, window_size_ms):
        pointer = 0
        timeseries = audiofile.timeseries
        sample_rate = audiofile.sample_rate

        window_size_frames = int((window_size_ms / 1000) * sample_rate)
        slices = []
        while pointer < timeseries.size:
            slice_ts = timeseries[pointer:(pointer+window_size_frames-1)]
            pointer += max(50, window_size_frames // 4)
            slices.append(
                Util.AudioFile(
                    slice_ts,
                    sample_rate,
                    offset_frames=pointer
                )
            )
        return slices

    @staticmethod
    def declick(audiofile, dc_type, fade_ms):
        x = audiofile.timeseries
        sr = audiofile.sample_rate

        fade_frames = (sr * fade_ms) / 1000
        frames = x.size

        declick_functions = {
            'sigmoid': Util.__declick_vector_sigmoid,
            'linear':  Util.__declick_vector_linear,
        }
        fn = declick_functions[dc_type](frames, fade_frames)
        declicked = x * fn

        return Util.AudioFile(declicked, sr, offset_frames=audiofile.offset_frames)

    def __declick_vector_linear(n_frames, fade_frames):
        return [
            min(
                min(i/fade_frames, 1),
                min((n_frames-i)/fade_frames, 1)
            )
            for i in np.arange(0, n_frames, 1)
        ]
   
    def __declick_vector_sigmoid(n_frames, fade_frames):
        return [
            min(
                1/(1+math.exp((0.5-(i/fade_frames))*15)),
                1/(1+math.exp((0.5-((n_frames-i)/fade_frames))*15))
            )
            for i in np.arange(0, n_frames, 1)
        ]
   
    @staticmethod
    def extract_features(audiofile):
        audiofile.mfcc = librosa.feature.mfcc(audiofile.timeseries, audiofile.sample_rate)
        audiofile.chroma_stft = librosa.feature.chroma_stft(y=audiofile.timeseries, sr=audiofile.sample_rate)

    @staticmethod
    def audio_dist(a1, a2):
        #return Util.dist(a1.chroma_stft, a2.chroma_stft) * Util.dist(a1.mfcc, a2.mfcc)
        return Util.dist(a1.mfcc, a2.mfcc)

    @staticmethod
    def dist(mfcc1, mfcc2):
        dist, cost, acc_cost, path = dtw(
                mfcc1.T, mfcc2.T, dist=lambda x, y: norm(x - y, ord=1)
                )
        return dist
