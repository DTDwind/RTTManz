#!/usr/bin/env bash

stage=2
AMIcorpus=example/ami/amicorpus # If you already have amicorpus, please set the path to that location and skip stage 0.
oracle_rttm_path=example/ami/rttm

if [ $stage -le 0 ]; then
    echo "Stage 0: Download ami test corpus."
    ./example/ami/amiBuild.wget.sh
    AMIcorpus=example/ami/amicorpus 
fi

if [ $stage -le 1 ]; then
    echo "Stage 1: Preparing data."
    mkdir -p example/ami/ami_testset
    testset_path=example/ami/ami_testset
    for audio_path in $(find $AMIcorpus/*/audio -name *.wav)
    do
        audio_name=`basename $audio_path`
        # echo  $audio_path
        for test_name in $(cat example/ami/ami_testset_list.txt)
        do
            if [ $audio_name == $test_name ]; then
                ln -s $audio_path $testset_path
            fi
        done
    done
fi

if [ $stage -le 2 ]; then
    echo "Stage 2: Analyzing ami test corpus."
    python3 RTTManz.py --rttm_path $oracle_rttm_path --audio_path $testset_path
fi
