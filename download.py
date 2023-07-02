import argparse
import io
import os
from pathlib import Path
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload
from getfilelistpy import getfilelist

from credentials import load_credentials


def get_args():
    parser = argparse.ArgumentParser()

    parser.add_argument("--download_dir_id")
    parser.add_argument("--save_dir", default=None)

    return parser.parse_args()


def download_files(drive_service, save_dir, res):
    all_subdirs = res["folderTree"]
    dirid2dirname = {id:name for id, name in zip(all_subdirs["folders"], all_subdirs["names"])}

    file_list = res["fileList"]
    n_files = sum([len(i["files"]) for i in file_list])

    i = 1
    for files_dirtree in file_list:
        dirtree = files_dirtree["folderTree"]

        for files in files_dirtree["files"]:
            fileid = files["id"]
            filename = files["name"]

            save_dir_single_file = save_dir / "/".join(map(dirid2dirname.get, dirtree))
            os.makedirs(save_dir_single_file, exist_ok=True)

            request = drive_service.files().get_media(fileId=fileid)
            fh = io.FileIO(save_dir_single_file / filename, mode="wb")
            downloader = MediaIoBaseDownload(fh, request)

            done = False
            while not done:
                status, done = downloader.next_chunk()
                print(f"[{str(i):>4s}/{str(n_files):>4s}] {filename}")
            i += 1


def main():
    args = get_args()
    
    creds = load_credentials()

    resource = {
        "oauth2": creds,
        "id": args.download_dir_id,
        "fields": "files(name, id)",
    }
    res = getfilelist.GetFileList(resource)
    drive_service = build("drive", "v3", credentials=creds)

    download_files(drive_service=drive_service, save_dir=args.save_dir, res=res)

if __name__ == "__main__":
    main()
