# RTTManz
A simple Python package for analyzing the necessary data in Speaker Diarization using oracle RTTM files and audio files.

## Installation
```
$ conda create -n RTTManz python=3.8
$ conda activate RTTManz
```
After the environment is activated, clone and install the package as:
```
$ git clone https://github.com/DTDwind/RTTManz.git
$ cd RTTManz
$ pip install -e .
```

## How to run
After installation, run
```
python3 RTTManz.py --rttm_path [INPUT_RTTMS_PATH] --audio_path [INPUT_AUDIOS_PATH]
```
Example pipeline:
```
./AMI_run.sh
```