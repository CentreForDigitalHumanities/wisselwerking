import csv
import pathlib
from django.core.management.base import BaseCommand, CommandError
import os

RECEIVERS = "ontvangers"
MAIL_SUBJECT = "onderwerp"
MAIL_CONTENT = "bericht"


class Command(BaseCommand):
    help = "Creates a file with a mail for the organizers with the enrollments"

    def add_arguments(self, parser):
        parser.add_argument("files", nargs=1, type=str)

    def handle(self, *args, **options):
        project_root = pathlib.Path(
            __file__
        ).parent.parent.parent.parent.parent.resolve()

        for filename in options["files"]:
            filepath = os.path.join(project_root, filename)
            if not os.path.isfile(filepath):
                raise CommandError(f"File {filepath} does not exist!")

            with open(filepath, encoding="utf-8-sig") as csvfile:
                reader = csv.DictReader(csvfile, delimiter=";")
                i = 0
                for row in reader:
                    mail = create_mail(
                        row[MAIL_SUBJECT], row[RECEIVERS], row[MAIL_CONTENT]
                    )

                    with open(
                        f"{filepath}_{i}.eml", mode="w", encoding="utf-8-sig", newline='\r\n'
                    ) as mailfile:
                        mailfile.write(mail)

                    i += 1


def create_mail(subject, to, content):
    return f"""Content-Type: text/plain; charset="utf-8"
Content-Transfer-Encoding: quoted-printable
MIME-Version: 1.0
To: {to}
From: wisselwerking.gw@uu.nl
Subject: {subject}
X-Unsent: 1


{content}
"""
