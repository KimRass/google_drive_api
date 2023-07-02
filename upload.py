import argparse
import mimetypes
from pathlib import Path
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

from credentials import load_credentials


def get_args():
    parser = argparse.ArgumentParser()

    parser.add_argument("--upload_dir")

    return parser.parse_args()


def create_folder(drive_service, name, parent_fol_id=None):
    file_metadata = {
        "name": name,
        "mimeType": "application/vnd.google-apps.folder"
    }
    if parent_fol_id:
        file_metadata["parents"] = [parent_fol_id]
    file = drive_service.files().create(body=file_metadata, fields="id").execute()
    return file.get("id")


def upload_file(drive_service, tar_file, name, save_fol=None):
    file_metadata = {"name": name}
    if save_fol:
        file_metadata["parents"] = [save_fol]
    media = MediaFileUpload(tar_file, mimetype=mimetypes.guess_type(tar_file)[0])
    # file = drive_service.files().create(
    drive_service.files().create(
        body=file_metadata,
        media_body=media,
        fields="id"
    ).execute()
    print(f"{name}")


def upload_directory(drive_service, upload_dir):
    upload_dir = Path(upload_dir)

    fol_id = create_folder(drive_service, name=upload_dir.name)

    dic = {str(upload_dir): fol_id}
    for file_or_dir in upload_dir.glob("**/*"):
        if file_or_dir.is_dir():
            fol_id = create_folder(
                drive_service,
                name=file_or_dir.name,
                parent_fol_id=dic[str(file_or_dir.parent)]
            )
            dic[str(file_or_dir)] = fol_id
        if file_or_dir.is_file():
            upload_file(
                drive_service,
                tar_file=file_or_dir,
                name = file_or_dir.name,
                save_fol=dic[str(file_or_dir.parent)]
            )


def main():
    args = get_args()
    
    creds = load_credentials()

    # resource = {
    #     "oauth2": creds,
    #     "id": download_dir_id,
    #     "fields": "files(name, id)",
    # }
    # res = getfilelist.GetFileList(resource)
    drive_service = build("drive", "v3", credentials=creds)

    upload_directory(drive_service=drive_service, upload_dir=args.upload_dir)


if __name__ == "__main__":
    main()
