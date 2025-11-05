import csv
import pathlib
from typing import Dict, List, Tuple
from django.contrib.auth.models import User, Group
from django.core.management.base import BaseCommand, CommandError
import os
import datetime

from registration.models import (
    Exchange,
    ExchangeSession,
    ExchangeSessionDescription,
    Mail,
    Person,
    get_team_str,
)

DEFAULT_LANGUAGE = "nl"

ENROLLMENT_ADD = "_fd_Add"
ENROLLMENT_MAIL = "e_mailadres"
ENROLLMENT_ASSIGNED = "toegewezen"
ENROLLMENT_MAIL_SUBJECT = "onderwerp"
ENROLLMENT_MAIL_CONTENT = "bericht"


class Command(BaseCommand):
    help = "Enriches data of an existing enrollments"

    def add_arguments(self, parser):
        parser.add_argument("files", nargs="+", type=str)

    def handle(self, *args, **options):
        project_root = pathlib.Path(
            __file__
        ).parent.parent.parent.parent.parent.resolve()

        for filename in options["files"]:
            filepath = os.path.join(project_root, filename)
            if not os.path.isfile(filepath):
                raise CommandError(f"File {filepath} does not exist")

            enriched, fieldnames = self.enrich_data(filepath)
            self.write_data(filepath, fieldnames, enriched)

    def enrich_data(self, filepath: str) -> Tuple[List[List[str]], List[str]]:
        output: List[Dict[str, str]] = []
        team = get_team_str()
        with open(filepath, mode="r", encoding="utf-8-sig") as csv_file:
            csv_reader = csv.DictReader(csv_file, delimiter=";")

            for row in csv_reader:
                email = row[ENROLLMENT_MAIL].lower()

                try:
                    user = User.objects.get(email=email)
                except User.DoesNotExist:
                    raise CommandError(
                        f"User {email} does not exist. Import the file first."
                    )

                try:
                    person = Person.objects.get(user=user)
                except Person.DoesNotExist:
                    raise CommandError(
                        f"Person {email} does not exist. Import the file first."
                    )

                add = None
                for format in [
                    "%d-%m-%Y %H:%M",
                    "%d-%m-%Y, %H:%M",
                    "%d-%m-%y %H:%M",
                    "%d-%m-%Y",
                    "%d-%m-%y",
                ]:
                    try:
                        add = datetime.datetime.strptime(
                            row[ENROLLMENT_ADD], format
                        ).astimezone()
                    except ValueError:
                        continue
                    break
                if add is None:
                    raise ValueError(f"Could not parse {row[ENROLLMENT_ADD]}")

                try:
                    exchange = Exchange.objects.get(begin=add.year)
                except Exchange.DoesNotExist:
                    raise CommandError(
                        f"Exchange {add.year}-{add.year + 1} does not exist. Import the file first."
                    )

                assigned = ExchangeSession.objects.get(
                    assigned=person, exchange=exchange
                )
                try:
                    mail = Mail.objects.get(
                        type="assigned", language=person.language or DEFAULT_LANGUAGE
                    )
                except Mail.DoesNotExist:
                    mail = Mail.objects.get(type="assigned", language=DEFAULT_LANGUAGE)
                try:
                    title = ExchangeSessionDescription.objects.get(
                        exchange=assigned, language=person.language or DEFAULT_LANGUAGE
                    ).title
                except ExchangeSessionDescription.DoesNotExist:
                    title = ExchangeSessionDescription.objects.get(
                        exchange=assigned, language=DEFAULT_LANGUAGE
                    ).title

                row[ENROLLMENT_ASSIGNED] = title
                row[ENROLLMENT_MAIL_SUBJECT], row[ENROLLMENT_MAIL_CONTENT] = (
                    self.prepare_mail(person, mail, title, team)
                )
                output.append(row)

            return output, list(csv_reader.fieldnames) + [
                ENROLLMENT_ASSIGNED,
                ENROLLMENT_MAIL_SUBJECT,
                ENROLLMENT_MAIL_CONTENT,
            ]

    def write_data(
        self, filepath: str, fieldnames: List[str], enriched: List[Dict[str, str]]
    ) -> None:
        target_filepath, extension = os.path.splitext(filepath)
        target_filepath += "_out" + extension

        with open(target_filepath, mode="w", encoding="utf-8-sig") as csv_file:
            csv_writer = csv.DictWriter(csv_file, delimiter=";", fieldnames=fieldnames)
            csv_writer.writeheader()
            csv_writer.writerows(enriched)

    def prepare_mail(
        self, person: Person, mail: Mail, assigned: str, team: str
    ) -> Tuple[str, str]:
        data = {
            "given_names": person.given_names.strip(),
            "assigned": assigned,
            "team": team,
        }
        return self.enrich_mail(mail.subject, data), self.enrich_mail(mail.text, data)

    def enrich_mail(self, text: str, data: Dict[str, str]) -> str:
        for key, value in data.items():
            text = text.replace(f"{{{{{key}}}}}", value)

        return text

    def get_team_str(self) -> str:
        team = Group.objects.get(name="Team")
        persons = Person.objects.filter(user__groups=team).order_by("user__first_name")
        return ", ".join(person.full_name for person in persons)
