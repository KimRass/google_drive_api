# `pip install google-api-python-client`
# `pip install getfilelistpy`

import io
import os
from pathlib import Path
import pandas as pd
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload
from getfilelistpy import getfilelist

# from libs.utils.logger import Logger
# from libs.utils.df_utils import DFUtils
# from cmd_args_down_gdrive import CMDArgsDownGdrive
# from utils import *
from credentials import load_credentials


def fetch_sub_dirs(path, output_file, names, gdrive_ids):
    df = pd.DataFrame({"name": names, "gdrive_id": gdrive_ids})
    df_utils = DFUtils("df_utils")
    df_utils.save(df, path, output_file)

    dup_df = df[df["name"].duplicated(keep=False)]
    if (dup_count := len(dup_df)) > 0:
        logger.critical(f"{dup_count} folders are duplicates ...")
        dup_output_file = "_dup.".join([*output_file.rsplit(".", 1)])
        df_utils.save(dup_df, path, dup_output_file)


def filter_files(file_list, exts):
    logger.info(f"Filtering files by extensions {exts} ...")

    matched_list = list()
    for ext in exts:
        matched_list += [
            {
                "files": [
                    {"id": files["id"], "name": files["name"]}
                    for files in files_dirtree["files"]
                    if len(files["name"]) >= len(ext) + 2
                    and files["name"][-len(ext) :].lower() == ext
                ],
                "folderTree": files_dirtree["folderTree"],
            }
            for files_dirtree in file_list
        ]

    files_count_bef = sum([len(i["files"]) for i in file_list])
    files_count_aft = sum([len(i["files"]) for i in matched_list])
    if (dropped_count := files_count_bef - files_count_aft) > 0:
        message = f"{dropped_count:,} files dropped".format(dropped_count)
    else:
        message = "Nothing dropped"
    logger.info(f"{message}")

    return matched_list


def download_files(drive_service, path, dirid2dirname, file_list):
    files_count = sum([len(i["files"]) for i in file_list])

    i = 1
    for files_dirtree in file_list:
        dirtree = files_dirtree["folderTree"]
        for files in files_dirtree["files"]:
            fileid = files["id"]
            filename = files["name"]

            logger.info(f"[{i}/{files_count}] id  : {fileid}")
            logger.info(f"[{i}/{files_count}] name: {filename}")

            save_dir_single_file = path / "/".join(map(dirid2dirname.get, dirtree))
            os.makedirs(save_dir_single_file, exist_ok=True)

            request = drive_service.files().get_media(fileId=fileid)
            fh = io.FileIO(save_dir_single_file / filename, mode="wb")
            downloader = MediaIoBaseDownload(fh, request)

            done = False
            while not done:
                status, done = downloader.next_chunk()
                logger.info(f"download {status.progress():.0%}")
            i += 1


def compare_file_list(path, gdrive_files):
    logger.info(f"Checking files count ...")

    file_list_p = Path(path).glob("**/*")
    file_list = set(map(lambda x: x.name, filter(lambda x: x.is_file(), file_list_p)))
    fail_files = list(gdrive_files - file_list)
    if fail_files:
        for fail_file in fail_files:
            logger.critical(f"Not found files: {fail_file}")
    else:
        logger.info("All files have been downloaded!")


def main():
    # global logger
    # logger = Logger().get_logger()

    # args_down_gdrive = CMDArgsDownGdrive("cmd_args_down_gdrive", ["drive_id"])
    # args = args_down_gdrive.values

    creds = load_credentials()
    drive_service = build("drive", "v3", credentials=creds)

    resource = {
        "oauth2": creds,
        "id": args.drive_id,
        "fields": "files(name, id)",
    }
    res = getfilelist.GetFileList(resource)

    if args.is_fetch_sub_dirs:
        fetch_sub_dirs(
            args.path,
            args.output_file,
            res["folderTree"]["names"],
            res["folderTree"]["folders"],
        )

    if args.is_download:
        all_subdirs = res["folderTree"]
        dirid2dirname = {
            id: name for id, name in zip(all_subdirs["folders"], all_subdirs["names"])
        }

        file_list = res["fileList"]
        if args.extensions:
            file_list = filter_files(file_list, args.extensions)

        download_files(drive_service, Path(args.path), dirid2dirname, file_list)

        compare_file_list(
            args.path,
            set(
                [
                    files["name"]
                    for files_dirtree in file_list
                    for files in files_dirtree["files"]
                ]
            ),
        )


if __name__ == "__main__":
    main()
