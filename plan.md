music-vid automation.

The first passs will be an api + comand line interface

This task is to create an agent to orchestrate a music video from a single prompt.

The user offers a prompt (right now it can be command line) for the %topic and for the %style and then there's a pipeline that starts up ...

%lyrics=The %topic and %style gets prompt engineered and sent off to a local model asking it to generate a song 

%song=acestep-1.5 processed with <%lyrics, %style>

%lyrics_with_timestamps=%song is processed through a timestamp-aware model to extract the lyrics again, but this time with timestamps

%scene_list=inference is run on the %lyrics_with_timestamps into a group of scenes with text themes %description. They should have durations that correspond to the timestamps

%video_list = []

foreach %scene in %scene_list:
    %assets=we use brave-search api to go and find assets that corespond to the %scene
    %audio_clip=we use ffmpeg to clip the %song to cover the duration and offset of the %scene
    %video_clip=we use the %assets and %audio_clip and call ltx-2.3 video model to generate clips with a text prompt of the %description

    %video_list.append(%video_clip)

%video=nothing
for each %clip in %video_list:
    %video+= %clip

%final_video=replace %video audio with %song to make sure the %song is smooth


