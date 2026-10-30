# praat_analysis.praat
# Standalone Praat check: duration, pitch, intensity and silent intervals.
#
# Usage (create the output folder first):
#   praat --run praat_analysis.praat take1.wav reports/take1
#
# Outputs:
#   praat_report.txt      key,value metrics
#   silences.TextGrid     silent / sounding intervals

form Analyse speech
    sentence Audio_file
    sentence Output_dir
    real Pitch_floor 75
    real Pitch_ceiling 500
    real Silence_threshold -25
    real Min_silence 0.3
    real Min_sounding 0.1
endform

sound = Read from file: audio_file$
if numberOfSelected("Sound") <> 1
    exitScript: "Could not read " + audio_file$
endif

duration = Get total duration

selectObject: sound
pitch = To Pitch: 0.01, pitch_floor, pitch_ceiling
selectObject: pitch
pitchMean = Get mean: 0, 0, "Hertz"
pitchMin = Get minimum: 0, 0, "Hertz", "Parabolic"
pitchMax = Get maximum: 0, 0, "Hertz", "Parabolic"

if pitchMean = undefined
    pitchMeanText$ = "NA"
else
    pitchMeanText$ = fixed$(pitchMean, 1)
endif
if pitchMin = undefined
    pitchMinText$ = "NA"
else
    pitchMinText$ = fixed$(pitchMin, 1)
endif
if pitchMax = undefined
    pitchMaxText$ = "NA"
else
    pitchMaxText$ = fixed$(pitchMax, 1)
endif

selectObject: sound
intensity = To Intensity: 75, 0, "yes"
selectObject: intensity
intensityMean = Get mean: 0, 0, "energy"
intensityMax = Get maximum: 0, 0, "Parabolic"
intensityMin = Get minimum: 0, 0, "Parabolic"

selectObject: sound
grid = To TextGrid (silences): silence_threshold, min_silence, min_sounding, "silent", "sounding"

pauseCount = 0
pauseTotal = 0
longestPause = 0
numberOfIntervals = Get number of intervals: 1
for i from 1 to numberOfIntervals
    label$ = Get label of interval: 1, i
    if label$ = "silent"
        start = Get starting time of interval: 1, i
        end = Get end time of interval: 1, i
        pauseDuration = end - start
        pauseCount = pauseCount + 1
        pauseTotal = pauseTotal + pauseDuration
        if pauseDuration > longestPause
            longestPause = pauseDuration
        endif
    endif
endfor

voicedDuration = duration - pauseTotal
if duration > 0
    pauseRate = pauseCount / (duration / 60)
else
    pauseRate = 0
endif

selectObject: grid
Save as text file: output_dir$ + "/silences.TextGrid"

writer = CreateWriter: output_dir$ + "/praat_report.txt"
writeFileLine: writer, "metric,value"
writeFileLine: writer, "file," + audio_file$
writeFileLine: writer, "duration_s," + fixed$(duration, 3)
writeFileLine: writer, "voiced_duration_s," + fixed$(voicedDuration, 3)
writeFileLine: writer, "pitch_floor_hz," + fixed$(pitch_floor, 1)
writeFileLine: writer, "pitch_ceiling_hz," + fixed$(pitch_ceiling, 1)
writeFileLine: writer, "pitch_mean_hz," + pitchMeanText$
writeFileLine: writer, "pitch_min_hz," + pitchMinText$
writeFileLine: writer, "pitch_max_hz," + pitchMaxText$
writeFileLine: writer, "intensity_mean_db," + fixed$(intensityMean, 2)
writeFileLine: writer, "intensity_min_db," + fixed$(intensityMin, 2)
writeFileLine: writer, "intensity_max_db," + fixed$(intensityMax, 2)
writeFileLine: writer, "silence_threshold_db," + fixed$(silence_threshold, 1)
writeFileLine: writer, "pause_count," + string$(pauseCount)
writeFileLine: writer, "pause_total_s," + fixed$(pauseTotal, 3)
writeFileLine: writer, "pause_rate_per_min," + fixed$(pauseRate, 2)
writeFileLine: writer, "longest_pause_s," + fixed$(longestPause, 3)
close: writer

writeInfoLine: "duration_s=", fixed$(duration, 3)
appendInfoLine: "pitch_mean_hz=", pitchMeanText$
appendInfoLine: "pause_count=", pauseCount
appendInfoLine: "pause_total_s=", fixed$(pauseTotal, 3)
appendInfoLine: "report=", output_dir$ + "/praat_report.txt"
