#!/usr/bin/env bash

stage=0
AMIcorpus=example/ami/amicorpus # If you already have amicorpus, please set the path to that location and skip stage 0.
oracle_rttm_path=example/ami/rttm
testset_path=example/ami/ami_testset

if [ $stage -le 0 ]; then
    echo "Stage 0: Download ami test corpus."
    ./example/ami/amiBuild.wget.sh
    AMIcorpus=example/ami/amicorpus 
fi

if [ $stage -le 1 ]; then
    echo "Stage 1: Preparing data."
    mkdir -p $testset_path
    for audio_path in $(find $AMIcorpus/*/audio -name *.wav)
    do
        audio_name=`basename $audio_path`
        new_audio_name=$(basename "$audio_name" .Mix-Headset.wav).wav
        for test_name in $(cat example/ami/ami_testset_list.txt)
        do
            if [ $audio_name == $test_name ]; then
                ln -s `pwd`/$audio_path $testset_path/$new_audio_name
            fi
        done
    done
fi

if [ $stage -le 2 ]; then
    echo "Stage 2: Analyzing ami test corpus."
    python3 RTTManz.py --rttm_path $oracle_rttm_path --audio_path $testset_path
fi
