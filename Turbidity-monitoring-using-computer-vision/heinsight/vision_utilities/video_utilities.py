
import os 
import cv2
from heinsight.vision_utilities.image_analysis import height_width


def folder_of_images_to_video(folder_path,
                              output_video_file_location=None,
                              output_video_name=None,
                              fps=30,
                              display_image_name=False,
                              ):
    """
    For this, assuming that the images names are the time stamp of when the image was taken, since the images will be
    have text placed on it, based on the file name. take a folder of images, and turn it into a video with file name
    written on each frame in the video

    can either give the output video file location OR output video name

    :param str, folder_path: path to folder of images to turn into a video
    :param str, output_video_file_location: path to save the video file to
    :param str, output_video_name: name of the video that will be created; it needs to include the file type in it too
    :param int, fps: frames per second; the frames per second for the output video
    :param bool, display_image_name: if True, then overlap the name of the image on each frame in the video
    :return:
    """
    folder = folder_path
    if output_video_file_location is None:
        if output_video_name is None:
            output_video_name = 'output_video.mp4'
        output_video_file_location = os.path.join(folder_path, output_video_name)

    if output_video_name is None:
        output_video_name = output_video_file_location.split('/')[-1]

    # use the first image in the folder to get the width and height of all the images
    only_once = 0
    for filename in os.listdir(folder):
        if only_once > 0:
            break
        path_to_first_image = os.path.join(folder, filename)
        first_image = cv2.imread(path_to_first_image)
        image_height, image_width = height_width(image=first_image)
        only_once += 1



    # Define the codec and create VideoWriter object
    output_file_type = output_video_name.split('.')[-1]
    if output_file_type == 'mp4':
        #fourcc = 0x00000021
        fourcc = cv2.VideoWriter_fourcc(*"mp4v")
    else:
        fourcc = cv2.VideoWriter_fourcc(*'XVID')

    output_video = cv2.VideoWriter(output_video_file_location,
                                   fourcc,
                                   fps,
                                   (image_width, image_height))

    green = (0, 255, 0)
    colour = green
    bottom_of_the_image_row = image_height
    bottom_of_the_image_row -= 30
    text_position = (0, bottom_of_the_image_row)
    font = cv2.FONT_HERSHEY_SIMPLEX
    font_scale = 0.70
    
    files =  os.listdir(folder)
    #print(files)
    sorted_files =  sorted(files)
    #print(sorted_files)

    for index, filename_with_extension in enumerate(sorted_files):
        image = cv2.imread(os.path.join(folder, filename_with_extension))
        if display_image_name is True:
            split_up_filename_path = filename_with_extension.split('.')
            filename_without_file_type = split_up_filename_path[0]
            text = filename_without_file_type
            cv2.putText(image, text, text_position, font, font_scale, colour)
        output_video.write(image)

    output_video.release()
    cv2.destroyAllWindows()

    print('COMPLETED')


