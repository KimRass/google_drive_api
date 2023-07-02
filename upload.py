# `pip install google-api-python-client`

import argparse
import mimetypes
from pathlib import Path
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

# from libs.utils.logger import Logger
# from cmd_args_up_gdrive import CMDArgsUpGdrive
# from utils import *
from logger import Logger
from credentials import load_credentials


def get_args():
    parser = argparse.ArgumentParser()

    parser.add_argument("--download_dir_id")
    parser.add_argument("--save_dir", default=None)

    return parser.parse_args()


def create_folder(drive_service, name, parent_fol_id=None):
    file_metadata = {"name": name, "mimeType": "application/vnd.google-apps.folder"}
    if parent_fol_id:
        file_metadata["parents"] = [parent_fol_id]
    file = drive_service.files().create(body=file_metadata, fields="id").execute()
    return file.get("id")


def upload_file(drive_service, tar_file, name, save_fol=None):
    file_metadata = {"name": name}
    if save_fol:
        file_metadata["parents"] = [save_fol]
    media = MediaFileUpload(tar_file, mimetype=mimetypes.guess_type(tar_file)[0])
    drive_service.files()\
    .create(body=file_metadata, media_body=media, fields="id")\
    .execute()


def upload_directory(drive_service, upload_dir):
    upload_dir = Path(upload_dir)

    fol_id = create_folder(drive_service, name=upload_dir.name)

    dir2id = {str(upload_dir): fol_id}

    files_count = len(
        [
            file_or_dir
            for file_or_dir in upload_dir.glob("**/*")
            if file_or_dir.is_file()
        ]
    )

    i = 1
    for file_or_dir in upload_dir.glob("**/*"):
        if file_or_dir.is_dir():
            fol_id = create_folder(
                drive_service,
                name=file_or_dir.name,
                parent_fol_id=dir2id[str(file_or_dir.parent)],
            )
            dir2id[str(file_or_dir)] = fol_id
        if file_or_dir.is_file():
            upload_file(
                drive_service,
                tar_file=file_or_dir,
                name=file_or_dir.name,
                save_fol=dir2id[str(file_or_dir.parent)],
            )

            logger.info(f"[{i}/{files_count}] name: {file_or_dir.name}")
            i += 1


def main():
    args = get_args()
    download_dir_id = args.download_dir_id
    save_dir = Path(args.save_dir) if args.save_dir else args.save_dir

    global logger
    logger = Logger().get_logger()

    args_up_gdrive = CMDArgsUpGdrive("cmd_args_up_gdrive", ["upload_dir"])
    args = args_up_gdrive.values

    creds = load_credentials()
    drive_service = build("drive", "v3", credentials=creds)

    upload_directory(drive_service, args.upload_dir)


if __name__ == "__main__":
    main()
