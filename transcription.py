

from fileinput import filename
import os
import time
import boto3
import logging

from botocore.exceptions import ClientError

BUCKET_NAME_FOLDER = "proyecto-haia"
BUCKET_NAME = f"s3://{BUCKET_NAME_FOLDER}/"

FILE_DIRECTORY = os.path.dirname(os.path.realpath(__file__))
SUBTITLE_LOCAL_DIRECTORY = os.path.join(FILE_DIRECTORY, "subtitles")
VIDEO_LOCAL_DIRECTORY = os.path.join(FILE_DIRECTORY, "upload_videos")

################################ BUCKET MANAGEMENT ################################

def clear_bucket():
    '''
        Deletes all content in bucket BUCKET_NAME_FOLDER
    '''

    s3 = boto3.resource('s3')

    bucket = s3.Bucket(BUCKET_NAME_FOLDER)

    bucket.objects.all().delete()


def upload_file(local_file_path, file_name):
    '''
        Args:
            - local_file_path: path to target file

            - file_name: name of target file in bucket
    '''

    local_file = os.path.join(local_file_path, file_name)

    s3_client = boto3.client('s3')

    response = s3_client.upload_file(local_file, BUCKET_NAME_FOLDER, file_name)

    return True


def download_file(path_to_save, file_name):
    '''
        Args:
            - path_to_save: path to save target file

            - file_name: target file in bucket
    '''

    local_file = os.path.join(path_to_save, file_name)

    s3 = boto3.client('s3')

    response = s3.download_file(BUCKET_NAME_FOLDER, file_name, local_file)

    return response


################################ AWS TRANSCRIBE ################################


def transcribe_video(video_filename, video_lang):
    '''
    Args:
        - video_filename: target video filename

        - video_lang: language of the target video
    '''

    filename_without_extension = video_filename.split(".")[0]

    transcribe = boto3.client('transcribe', 'us-east-1')

    job_uri = f"{BUCKET_NAME}{video_filename}"

    try:
        transcribe.delete_transcription_job(TranscriptionJobName=filename_without_extension)
    except ClientError as e:
        pass

    transcribe.start_transcription_job(
        TranscriptionJobName = filename_without_extension,
        Media = {'MediaFileUri': job_uri
        },
        OutputBucketName = BUCKET_NAME_FOLDER,
        LanguageCode = video_lang,
        Subtitles = {'Formats':
                        ['vtt', 'srt'],
                    'OutputStartIndex': 1
        }
    )

    while True:

        status = transcribe.get_transcription_job(TranscriptionJobName=filename_without_extension)

        if status['TranscriptionJob']['TranscriptionJobStatus'] in ['COMPLETED', 'FAILED']:

            break

        time.sleep(5)

    print(status)

    return status

################################ AWS TRANSLATE ################################

def translate_lines(lines_to_translate, video_lang, subtitle_lang):

    translate = boto3.client(service_name='translate', region_name='us-east-1', use_ssl=True)

    if len(lines_to_translate) > 50:

        text_translated = list()

        for i in range(0, len(lines_to_translate), 50):

            lines_to_translate_chunk = lines_to_translate[i:i+50]

            text_to_translate = "\n".join(lines_to_translate_chunk)

            result = translate.translate_text(
                Text=text_to_translate,
                SourceLanguageCode=video_lang,
                TargetLanguageCode=subtitle_lang
            )

            text_translated.extend( result.get('TranslatedText').split("\n") )

    else:

        text_to_translate = "\n".join(lines_to_translate)

        result = translate.translate_text(
            Text=text_to_translate,
            SourceLanguageCode=video_lang,
            TargetLanguageCode=subtitle_lang
        )

        text_translated = result.get('TranslatedText').split("\n")

    return text_translated


def generate_video_subtitles(video_filename, video_lang, subtitle_lang):
    '''
    Args:
        - video_filename: target video filename

        - video_lang: language of the target video

        - subtitle_lang: language of the subtitles
    '''

    clear_bucket()

    #success = upload_file(VIDEO_LOCAL_DIRECTORY, video_filename)

    filename_without_extension = video_filename.split(".")[0]

    #json_response = transcribe_video(video_filename, video_lang)

    #if json_response == "ERROR" or json_response["TranscriptionJob"]["TranscriptionJobStatus"] != "COMPLETED":
    #    return {
    #        "code": 404,
    #        "message": "ERROR with your petition"
    #    }


    subtitle_filename = f"{filename_without_extension}.vtt"

    #success = download_file(SUBTITLE_LOCAL_DIRECTORY, subtitle_filename)

    # Process VTT file to split lines with numbers and timestamps from lines to actually translate

    lines_to_let_equal = list()
    lines_to_translate = list()

    f = open(os.path.join(SUBTITLE_LOCAL_DIRECTORY, subtitle_filename), "r", encoding="utf8")
    cont = 0
    cont_before_vtt = 2
    for line in f:
        line = line.replace("\n", "")

        if cont < cont_before_vtt:
            lines_to_let_equal.append(line)
            cont += 1
            continue

        if cont % 4 == 0:
            lines_to_translate.append(line)
        else:
            lines_to_let_equal.append(line)
        cont += 1
    f.close()

    # Translation process

    text_translated = translate_lines(lines_to_translate, video_lang, subtitle_lang)

    # Generate VTT translated file again

    subtitles_filename = os.path.join(SUBTITLE_LOCAL_DIRECTORY, f"{subtitle_lang}_{subtitle_filename}")

    f = open( subtitles_filename , "w", encoding="utf8")
    cont_write = 0
    index_let_equal = 0
    index_translated = 0
    for _ in range(cont):

        if cont_write < cont_before_vtt:
            f.write(lines_to_let_equal[index_let_equal] + "\n")
            index_let_equal += 1
            cont_write += 1
            continue

        if cont_write % 4 == 0:
            f.write(text_translated[index_translated] + "\n")
            index_translated += 1
        else:
            f.write(lines_to_let_equal[index_let_equal] + "\n")
            index_let_equal += 1
        cont_write += 1
    f.close()

    return {
        "code": 200,
        "message": "All good.",
        "subtitles_filename": f"{subtitle_lang}_{subtitle_filename}"
    }
