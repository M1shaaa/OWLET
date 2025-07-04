#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon Aug 22 18:57:55 2022

@author: werchd01
"""
import sys
sys.path.append("eyetracker")
import eyetracker.OWLET_GUI
import os
import argparse
from eyetracker import run_owlet
from eyetracker import run_owlet_cnn
import os
from pathlib import Path
import glob


def videofile(value):
    return value

def expFolder(value):
    value = Path(value)
#    if not value.is_dir():
 #       raise argparse.ArgumentTypeError(
  #          'Filepath must point to a folder with experiment info')
    return value

def parse_arguments():
    parser = argparse.ArgumentParser(description='OWLET - Online Webcam Linked Eye Tracker')
    parser.add_argument('--subject_video', type=videofile, help='subject video to be processed')
    parser.add_argument('--experiment_info', type=expFolder, help='directory with optional experiment info')
    parser.add_argument('--display_output', action='store_true', help='show annotated video online in a separate window')
    parser.add_argument('--override_audio_matching', action='store_true', help='Manually override audio matching when processing pre-cropped task videos')
    parser.add_argument('--cnn',  action='store_true', help='Manually override audio matching when processing pre-cropped task videos')

    args = parser.parse_args()
    return args


def main():
    cwd = os.path.abspath(os.path.dirname(__file__))
    
    # owlet_dir = os.path.abspath(os.path.join(cwd, "\OWLET"))
    # print(owlet_dir)
    
    args = parse_arguments()
    
    
    if not args.subject_video:
    
        owlet_gui = eyetracker.OWLET_GUI.OWLET_Interface(cwd)
        continue_running = True
        while continue_running:  
            owlet_gui.display_GUI()
            # if owlet_gui.started:
            #     owlet_gui.start_OWLET()
            continue_running = not(owlet_gui.user_quit)
    else:

        value = Path(args.subject_video)
        if not value.is_dir():
            subVideo = args.subject_video
            videos = [subVideo]
            subDir = os.path.dirname(subVideo) #args.subject_folder
            os.chdir(subDir)
        else:
            subDir = args.subject_video        
            os.chdir(subDir)
            videos = glob.glob('*.mp4') + glob.glob('*.mov')
            videos = [ x for x in videos if "annotated" not in x ]
            videos = [ x for x in videos if "calibration" not in x ]
            videos = [ x for x in videos if "Calibration" not in x ]

        
        show_output = False
        stim_df = None        
        
        calibVideos = glob.glob('*.mp4') + glob.glob('*.mov')
        calibVideos = [ x for x in calibVideos if "calibration" in x or "Calibration" in x ]
        print(args.cnn)
        for subVideo in videos:
            if args.cnn: 
                owlet = run_owlet_cnn.OWLET_CNN()
                print("cnn")
            else: owlet = run_owlet.OWLET()
            taskVideo, calibVideo, aois, stim_file, expDir, taskName = None, None, "", None, None, ""
            
            # contains optional experiment info (task video, aois, and stimulus/trial timing info)
            if args.experiment_info:
                expDir = args.experiment_info
                os.chdir(expDir)
                taskVideo = glob.glob('*.mp4') + glob.glob('*.mov')
                
                
                aois = glob.glob('*AOIs.csv')
                stim_file = glob.glob('*trials.csv')
                print(stim_file)
                if len(taskVideo) != 1: 
                    taskVideo = None
                else: 
                    taskName = os.path.basename(os.path.normpath(expDir))
                    taskName = str(taskName).lower()
                if len(aois) != 1: 
                    aois = ""
                else: 
                    aois = aois[0]
                if len(stim_file) != 1: 
                    stim_file = None
                
            os.chdir(subDir)
            subVideo = os.path.basename(subVideo)
            subname , ext = os.path.splitext(subVideo)
            subname = str(subname).lower()
            # subname.replace("tasks", "")
            print(taskName)
            print(subname)
            if taskName != "":
                taskName = "_" + taskName
                subname = str(subname).replace(taskName, '')
                print(subname)
        
            calibVideos_tmp = [ x for x in calibVideos if str(subname) in x ]
            calibVideo = [ x for x in calibVideos_tmp if "annotated" not in x ]
            print(calibVideo)
        
            if args.display_output:
                show_output = True
          
            if taskVideo is not None:
                experiment_name = os.path.basename(os.path.normpath(expDir))
                file_name = str(subDir) + '/' + str(subname) + "_" + str(experiment_name) + "_error_log" + ".txt"
            else:
                file_name =  str(subDir) + '/' + str(subname) + "_error_log" + ".txt"
                
            if stim_file is not None and len(stim_file) == 1:
                success, stim_df = owlet.read_stim_markers(stim_file = os.path.join(expDir, stim_file[0]))
            else:
                success = False
                if not success:
                    print("Trial markers file must have 'Time' and 'Label' columns.")
                    file = open(file_name, "w")
                    file.write("Incorrect experiment info -- Trial markers file must have 'Time' and 'Label' columns.\n")
                    file.close()
                    #raise AssertionError - commented this out because it wasn't letting us process PA 
            
            if calibVideo is not None and len(calibVideo) == 1:
                calibVideo = os.path.abspath(os.path.join(subDir, calibVideo[0]))
                owlet.calibrate_gaze(calibVideo, show_output, cwd)
            
                
            
            if taskVideo is not None and len(taskVideo) == 1:
                taskVideo = os.path.abspath(os.path.join(expDir, taskVideo[0]))
                if not args.override_audio_matching:
                    found_match = owlet.match_audio(subVideo, taskVideo, cwd)
                    if found_match == False:
                        print("The task video was not found within the subject video. Processing halted.")
                        file = open(file_name, "w")
                        file.write("The task video was not found within the subject video. Processing halted..\n")
                        file.close()
                        exit()
        
            
            df = owlet.process_subject(cwd, subVideo, subDir, show_output, taskVideo, False)
            owlet.format_output(subVideo, taskVideo, subDir, expDir, df, aois, stim_df)
    
    
if __name__ == '__main__':
    main()
   
    
   


