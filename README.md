# equirect-events
Tools for generating simulated event camera (DVS camera) events from equirectangular images.

The main script rotates a virtual camera through the equirectangular image,
generating a series of three-point perspective snapshots, 
 calculates the per-pixel difference in luminance between the prior rotation iteration
and the current itertion,
then generates a set of simulated DVS / Event Camera events from that difference. 

Currently this tool outputs intermediate image files as well as `./out/events.dat` ,
which is a compact binary format (flatbuffer) that stores the events.  You can use
flatbuffer code generators to read this file in a variety of programming languages. 

## Dependencies

python3 and pip3

Plus some other python packages you might not have installed by default:

```
pip3 install opencv-python flatbuffers pillow py360convert
```

You might want to install `ffmpeg` if you want to create videos from the png output files.
On Mac OSX (Darwin) you can use eg 
`brew install ffmpeg`

## Run

Put an equirectangular image in 
`./data/raw_pano.jpg`

and then run:
`python3 ./remap_equi.py`

You can create a video of the 3-point perspective files using:
`vid_rot_persp.sh`

To create a video of rising and falling events from the same rotation sweep :

`./vid_persp_diff.sh`

## Examples

The following example began with an equirectangular (panoramic) image
donwloaded from [Wikimedia](https://commons.wikimedia.org/wiki/File:Rheingauer_Dom,_Geisenheim,_360_Panorama_(Equirectangular_projection).jpg). (The link contains information on the original author and license.)

Running `remap_equi.py` on this images, a series of 3600 perspective and difference images is generated such as:
![Perspective sample image](/example/persp_rot_0900.png)
![Difference sample image](/example/persp_diff_0900.png)

Note also that event files are generated (`./out/events.dat` is the flatbuffer file, `./out/events.txt` is CSV)

In addition I generated video files using `vid_rot_persp.sh` and `vid_persp_diff.sh` .

## Notes

- You can obtain a variety of equirectangular images from eg [Flickr](https://www.flickr.com/groups/equirectangular/)
- `dvs_event.fbs` contains the flatbuffer schema for encoding events as flatbuffers.  This can be a more compact representation of events.
- Currently the camera path is a simple rotation; however you could modify the code to tilt the camera (by adjusting the pitch angle), zoom in and out (by adjusting the FOV / angle of view)



