#!/usr/bin/python

import cv2
import numpy as np
import os.path
from os import path
import flatbuffers
import struct
import random
import py360convert
import csv

import EventCam.Event
import EventCam.FrameData
import EventCam.Polarity


# TODO make these command line parameters

SAVE_OUTPUT_IMAGES = True
# generate an events.dat file containing events in a flatbuffer binary format
SAVE_FLATBUF_EVENT_FILE = True
# generate CSV format event file, similar to Scaramuzze et al
SAVE_CSV_EVENT_FILE = True
# output image dimension (assumes square images)
OUT_IMG_DIM = 320
# Angle of view (degrees) for converting equirectangular images to 3-point perspective images
PERSPECTIVE_FOV = 63.5
# threshold to generate events from change in luminance: default is 10% of max intensity
LUM_CHANGE_THRESHOLD = 25
# number of divisions per degree to generate data for (equirect has 360 degrees)
NUM_DEGREE_DIVISIONS = 10

# default perspective camera pitch (degrees)-- zero points at equirect's horizon line
DEFAULT_CAMERA_PITCH = 0


def generate_csv_events(rising_locations, falling_locations, timebase, writer):
  """
  Generate CSV formatted events similar to Scaramuzze et al: http://rpg.ifi.uzh.ch/davis_data.html
  :param rising_locations: A list of pixel locations where rising threshold was triggered
  :param falling_locations: A list of pixel locations where falling threshold was triggered
  :param timebase: The last known time before events triggered
  :param writer: A CSV file writer
  :return: Updated timestamp
  """
  rising_count =  len(rising_locations)
  falling_count = len(falling_locations)
  ultimax = max(rising_count, falling_count)
  timestamp = timebase

  for idx in range(0,ultimax):
    row_list = []
    if idx < rising_count:
      timestamp += 0.000001 # 1E-6
      coord = rising_locations[idx][0]
      row = ['{0:.9f}'.format(timestamp) , coord[0], coord[1], 1]
      row_list.append(row)
    if idx < falling_count:
      timestamp += 0.000001 # 1E-6
      coord = falling_locations[idx][0]
      row = ['{0:.9f}'.format(timestamp) , coord[0], coord[1], 0]
      row_list.append(row)

    writer.writerows(row_list)

  return timestamp


def generate_flatbuffer_events(rising_locations, falling_locations, event_file):
  """
  Write flatbuffer-encoded events to a flatbuffer file

  :param rising_locations: A list of pixel locations where rising threshold was triggered
  :param falling_locations: A list of pixel locations where falling threshold was triggered
  :param event_file: The flatbuffer file where events should be written
  :return: Nothing
  """
  fbb = flatbuffers.Builder(0)

  rising_count =  len(rising_locations)
  falling_count = len(falling_locations)

  total_events = rising_count + falling_count
  EventCam.FrameData.FrameDataStartEventsVector(fbb, total_events)

  real_falling_count = 0
  for item in falling_locations:
    x =  item[0][0]
    y =  item[0][1]
    EventCam.Event.CreateEvent(fbb, x, y, EventCam.Polarity.Polarity.Falling)
    real_falling_count += 1

  real_rising_count = 0
  for item in rising_locations:
    x =  item[0][0]
    y =  item[0][1]
    EventCam.Event.CreateEvent(fbb, x, y, EventCam.Polarity.Polarity.Rising)
    real_rising_count += 1

  if real_rising_count != rising_count:
    print("rising got: %d expected: %d" %(real_rising_count, rising_count ) )

  if real_falling_count != falling_count:
    print("rising got: %d expected: %d" %(real_falling_count, falling_count ) )

  # done creating the vector of events
  all_events = fbb.EndVector(total_events)

  EventCam.FrameData.FrameDataStart(fbb)
  EventCam.FrameData.FrameDataAddFallingCount(fbb, real_falling_count)
  EventCam.FrameData.FrameDataAddRisingCount(fbb, real_rising_count)
  EventCam.FrameData.FrameDataAddEvents(fbb, all_events)

  framed_data = EventCam.FrameData.FrameDataEnd(fbb)
  fbb.Finish(framed_data)

  buf = fbb.Output()
  flatbuf_len = len(buf)
  print("rising: %d falling: %d total: %d flatbuf size: %d" %
        (rising_count, falling_count, total_events, flatbuf_len))
  event_file.write(struct.pack('<L', flatbuf_len))
  event_file.write(buf)
  event_file.flush()




if __name__ == '__main__':
  """
  Rotate through the equirectangular image,
  some fraction of a degree at a time,
  projecting the equirectangular image to a 3-point perspective image,
  store the perspective images to a file,
  then take the difference in brightness between successive frames,
  storing the difference to a file
  """

  gray_pano_path = "./data/gray_pano.png"
  raw_pano_path = "./data/raw_pano.jpg"
  
  if not path.exists(gray_pano_path):
    if path.exists(raw_pano_path):
      print("converting color jpg to png file...")
      raw_img = cv2.imread(raw_pano_path)
      #print("raw_img: %s" % raw_img)
      gray_img = cv2.cvtColor(raw_img, cv2.COLOR_BGR2GRAY)
      cv2.imwrite(gray_pano_path, gray_img)
         
  
  # luma changes less than this threshold are ignored (255 is max change)
  change_threshold = LUM_CHANGE_THRESHOLD # 10% of max intensity
  # Field of View (degrees) in horizontal and vertical directions
  # iphone6 FOV is about 63.5 degrees
  fov_h = PERSPECTIVE_FOV
  fov_v = PERSPECTIVE_FOV
  
  # input equirectangular file name
  img = cv2.imread(gray_pano_path)
  # blur to reduce moire on output
  fuzz_kernel = np.ones((5,5),np.float32)/25
  img = cv2.filter2D(img,-1,fuzz_kernel)
  img = cv2.blur(img,(3,3))


  (base_height, base_width, _) = img.shape
  degs_per_pixel = base_width / 360.0
  face_size = int(round(degs_per_pixel * fov_v))
  print("raw face_size: %d new size: %d" % (face_size,OUT_IMG_DIM))
  face_size = OUT_IMG_DIM

  # number of divisions to iterate, per degree
  degree_divisions = NUM_DEGREE_DIVISIONS
  # number of degrees to jump per iteration
  degrees_jump = -1
  
  # elevation pitch of camera
  pitch = DEFAULT_CAMERA_PITCH
  
  # used to store prior perspective image, for differencing
  prior_persp = None 
  # used to store the output differnce image 
  out_image = np.zeros((face_size, face_size, 3))
  
  # rotate over the entire 360 degree panorama
  min_degrees = int((-180 * degree_divisions) + degrees_jump)
  max_degrees = int(180 * degree_divisions)


  flatbuf_event_file = None
  if SAVE_FLATBUF_EVENT_FILE:
    flatbuf_event_file = open("./out/events.dat", 'wb')

  csv_event_file = None
  csv_event_writer = None
  if SAVE_CSV_EVENT_FILE:
    csv_event_file = open("./out/events.txt",'w')
    csv_event_writer = csv.writer(csv_event_file,delimiter=' ')

  timestamp = 0.0
  diff_count = 0
  for yaw_fine in range(max_degrees, min_degrees, degrees_jump):
    yaw = yaw_fine / float(degree_divisions)

    # the current panorama angle, from 360..0
    pano_angle = 180 - yaw
    cur_persp_name = "./out/persp_rot_%04d.png" % diff_count
    print("yaw: %f" % yaw)

    persp = None
    if path.exists(cur_persp_name):
      # load the existing perspective from disk
      persp = cv2.imread(cur_persp_name)
      gray_persp = cv2.cvtColor(persp, cv2.COLOR_BGR2GRAY)
    else:
      persp = py360convert.e2p(img, fov_deg=(fov_h, fov_v), u_deg=yaw, v_deg=0, out_hw=(face_size,face_size), in_rot_deg=0, mode='bilinear')

      # using py360convert requires pillow as well:
      # pip3 install py360convert
      # pip3 install pillow
      # note that after installing py360convert, you can run
      # convert360 --convert e2p --i data/rheingauer.jpg --o out/example_e2p.png --w 320 --h 320 --u_deg 90 --v_deg 0 --h_fov 63.5 --v_fov 63.5

      # for image diffs we only care about luminance
      gray_persp = cv2.cvtColor(persp, cv2.COLOR_BGR2GRAY)
      # store the perspective image to a file
      if SAVE_OUTPUT_IMAGES:
        cv2.imwrite(cur_persp_name, gray_persp)

    img_height, img_width = gray_persp.shape

    # subtract the last perspective image from the current one and save result
    if prior_persp is not None:
      # detect which pixels have changed by the threshold value
      
      # increases in luminance
      high_diff = cv2.subtract(gray_persp, prior_persp)
      # decreases in luminance
      low_diff = cv2.subtract(prior_persp, gray_persp)

      # apply threshold
      res,high_change = cv2.threshold(high_diff, change_threshold, 255, cv2.THRESH_BINARY)
      res,low_change = cv2.threshold(low_diff, change_threshold, 255, cv2.THRESH_BINARY)

      if SAVE_OUTPUT_IMAGES:
        out_image[:,:,2] = high_change # Red channel
        out_image[:,:,0] = low_change # Blue channel
        cv2.imwrite("./out/persp_diff_%04d.png" % diff_count, out_image)

      diff_count += 1

      rising_locations = cv2.findNonZero(high_change)
      if rising_locations is not None:
        rising_locations = cv2.randShuffle(rising_locations)
      else:
        rising_locations = []

      falling_locations = cv2.findNonZero(low_change)
      if falling_locations is not None:
        falling_locations = cv2.randShuffle(falling_locations)
      else:
        falling_locations = []

      if SAVE_CSV_EVENT_FILE:
        timestamp = generate_csv_events(rising_locations, falling_locations, timestamp, csv_event_writer)

      if SAVE_FLATBUF_EVENT_FILE:
        generate_flatbuffer_events(rising_locations, falling_locations, flatbuf_event_file)


    prior_persp = gray_persp


  if SAVE_FLATBUF_EVENT_FILE:
    flatbuf_event_file.flush()
    flatbuf_event_file.close()

  if SAVE_CSV_EVENT_FILE:
    csv_event_file.flush()
    csv_event_file.close()

