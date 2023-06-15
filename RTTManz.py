# Copyright 2023  Yu-Sen Cheng (DTDwind
#  Apache 2.0  (http://www.apache.org/licenses/LICENSE-2.0)

import os, sys
import argparse
import itertools
import numpy as np
import soundfile as sf
from pathlib import Path
from collections import defaultdict
from tabulate import tabulate

def get_args():
    parser = argparse.ArgumentParser(
        description=""" use rttm file and audio file anayze diarization infomation """)

    parser.add_argument("--rttm_path", type=str, help="Input the folder only contain RTTM file")
    parser.add_argument("--audio_path", type=str, help="Input audio folder file")
    parser.add_argument("--sec_per_frame", type=float, default=0.01, help="Frame shift value in seconds")
                        

    args = parser.parse_args()

    if args.sec_per_frame < 0.0001 or args.sec_per_frame > 1:
        raise ValueError("--sec_per_frame should be in [0.0001, 1]; got {0}".format(args.sec_per_frame))

    return args

class Segment:
    """Stores all information about a rttm segment"""
    def __init__(self, reco_id, start_time, dur, label):
        self.reco_id = reco_id              # recording ID
        self.start_time = start_time        # start time of segment
        self.end_time = start_time + dur    # end time of segment
        self.dur = dur                      # duration of segment
        self.label = label                  # label of segment

class Reco:
    """Stores all information about a reco"""
    def __init__(self, reco_name, channel="", length="", frame_num="", overlap="", non_overlap="", speech_time="", non_speech_time="", speaker_number="", speaker_ratio=""):
        self.name = reco_name
        self.channel = channel
        self.length = length
        self.frame_num = frame_num
        self.overlap = overlap                  # overlap frame number
        self.non_overlap = non_overlap          # non-overlap and have speech frame number
        self.speech_time = speech_time          # save with speech frame number
        self.non_speech_time = non_speech_time  # save with non-speech frame number
        self.speaker_number = speaker_number
        self.speaker_ratio = speaker_ratio

def groupby(iterable, keyfunc):
    """Wrapper around ``itertools.groupby`` which sorts data first."""
    iterable = sorted(iterable, key=keyfunc)
    for key, group in itertools.groupby(iterable, keyfunc):
        yield key, group

def run(args):
    rttm_path = Path(args.rttm_path)
    audio_path = Path(args.audio_path)

    segments = [] # initialize a list to store all segments
    rttm_list = os.listdir(rttm_path)
    
    for rttm_file in rttm_list:
        with open(rttm_path/rttm_file, "r") as f: # open the rttm file
            for line in f.readlines():
                parts = line.strip().split() # split the line into parts
                segments.append(Segment(parts[1], float(parts[3]), float(parts[4]), parts[7]))

    # We group the segment list into a dictionary indexed by reco_id
    reco2segs = defaultdict(list,
        {reco_id : list(g) for reco_id, g in groupby(segments, lambda x: x.reco_id)})

    # Analysis each reco
    reco_dict = {}
    for reco_id in reco2segs:
        unique_labels = set([segment.label for segment in segments if segment.reco_id == reco_id])
        num_speaker = len(unique_labels) # number of speaker

        # set label to index
        speaker2index = {}
        index = 0
        for label in unique_labels:
            speaker2index[label] = index
            index += 1

        segs = sorted(reco2segs[reco_id], key=lambda x: x.start_time)
        data, samplerate = sf.read(audio_path/(reco_id+".wav"))

        # Calculate audio file time
        length_in_seconds = len(data) / samplerate
        hours = int(length_in_seconds // 3600)
        minutes = int((length_in_seconds % 3600) // 60)
        seconds = length_in_seconds % 60
        length_in_hms = f"{hours:02d}:{minutes:02d}:{seconds:.4f}"

        if len(data.shape) == 1:
            reco_dict[reco_id] = Reco(reco_id, channel=1, length=length_in_hms, speaker_number=num_speaker)
        else:
            reco_dict[reco_id] = Reco(reco_id, channel=data.shape[1], length=length_in_hms, speaker_number=num_speaker)

        frame_num = int(length_in_seconds/args.sec_per_frame)

        reco_dict[reco_id].frame_num = frame_num
        targets_mat = np.zeros((frame_num, num_speaker), np.int8)
        
        for seg in segs:
            start_frame = int(seg.start_time / args.sec_per_frame)
            end_frame = min(int(seg.end_time / args.sec_per_frame), frame_num)
            num_frames = end_frame - start_frame
            if (num_frames <= 0):
                continue

            speaker_index = speaker2index[seg.label] # retrieve the index of the speaker
            targets_mat[start_frame:end_frame, speaker_index] = 1 # set the corresponding frames to 1 for the speaker in targets_mat

        sums   = np.sum(targets_mat, axis=0)
        ratios = np.round(sums / np.sum(sums), decimals=2)

        num_speakers_per_frame             = np.sum(targets_mat, axis=1)
        num_frames_with_multiple_speakers  = np.sum(num_speakers_per_frame > 1)
        reco_dict[reco_id].overlap         = num_frames_with_multiple_speakers
        reco_dict[reco_id].non_overlap     = np.sum(num_speakers_per_frame == 1)
        reco_dict[reco_id].speech_time     = np.sum(num_speakers_per_frame > 0)
        reco_dict[reco_id].non_speech_time = np.sum(num_speakers_per_frame == 0)
        reco_dict[reco_id].speaker_ratio   = ratios

    # statistics result
    data = []
    total_frame = 0
    total_speech_time = 0
    total_overlap_frame = 0
    max_speaker_num = 0
    min_speaker_num = 1e16
    counter = 0

    for reco_id in reco_dict:
        counter += 1
        row = []
        row.append(reco_id)
        row.append(reco_dict[reco_id].channel)
        row.append(reco_dict[reco_id].length)
        speech_time = reco_dict[reco_id].speech_time * args.sec_per_frame
        row.append(speech_time)
        non_speech_time = reco_dict[reco_id].non_speech_time * args.sec_per_frame
        row.append(non_speech_time)
        overlap_time = reco_dict[reco_id].overlap * args.sec_per_frame
        row.append(overlap_time)
        non_overlap_time = reco_dict[reco_id].non_overlap * args.sec_per_frame
        row.append(non_overlap_time)
        speaker_number = reco_dict[reco_id].speaker_number
        row.append(speaker_number)
        total_frame += reco_dict[reco_id].frame_num

        if speaker_number > max_speaker_num:
            max_speaker_num = speaker_number
        if speaker_number < min_speaker_num:
            min_speaker_num = speaker_number

        speaker_ratio = ":".join(map(str, reco_dict[reco_id].speaker_ratio))
        row.append(speaker_ratio)
        data.append(row)
        total_speech_time += speech_time
        total_overlap_frame += reco_dict[reco_id].overlap
    
    # print result
    headers = ["Reco ID", "Channels", "Time", "Speech Time (s)", "Non-speech Time (s)", "Overlap Time (s)", "Non-overlap Time (s)", "Speaker Number", "Speaker Ratio"]
    print(tabulate(data, headers=headers, tablefmt="grid"))

    data = []
    row = []
    row.append(counter)

    total_time_in_seconds = total_frame * args.sec_per_frame
    hours = int(total_time_in_seconds // 3600)
    minutes = int((total_time_in_seconds % 3600) // 60)
    seconds = total_time_in_seconds % 60
    total_time = f"{hours:02d}:{minutes:02d}:{seconds:.4f}"
    row.append(total_time)
    tbt = total_speech_time
    hours = int(total_speech_time // 3600)
    minutes = int((total_speech_time % 3600) // 60)
    seconds = total_speech_time % 60
    total_speech_time = f"{hours:02d}:{minutes:02d}:{seconds:.4f}"
    row.append(total_speech_time)
    total_overlap_time = (total_overlap_frame * args.sec_per_frame)
    overlap_ratio = total_overlap_time/tbt
    row.append("{:.2%}".format(overlap_ratio))
    row.append(max_speaker_num)
    row.append(min_speaker_num)
    data.append(row)

    print("")
    headers = ["Reco Number", "Total Time", "Total Speech Time", "Overlap Ratio", "Max Speaker Number", "Min Speaker Number"]
    print(tabulate(data, headers=headers, tablefmt="grid"))

def main():
    args = get_args()
    try:
        run(args)
    except Exception:
        raise

if __name__ == "__main__":
    main()

