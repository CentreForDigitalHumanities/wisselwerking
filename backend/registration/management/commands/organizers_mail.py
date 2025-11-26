import csv
import pathlib
from typing import Dict, List, Tuple
from django.contrib.auth.models import Group
from django.core.management.base import BaseCommand, CommandError
import os

from registration.models import (
    Exchange,
    ExchangeSession,
    Mail,
    Person,
    get_team_str,
)

DEFAULT_LANGUAGE = "nl"

RECEIVERS = "ontvangers"
MAIL_SUBJECT = "onderwerp"
MAIL_CONTENT = "bericht"

MAIL_TYPE = "overview_assigned"
CONJUNCT = {"en": " and ", "nl": " en "}


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
            if os.path.isfile(filepath):
                raise CommandError(f"File {filepath} already exists!")

            output, fieldnames = self.mail_info()
            write_data(filepath, fieldnames, output)

    def mail_info(self) -> Tuple[List[List[str]], List[str]]:
        output: List[Dict[str, str]] = []
        team = get_team_str()

        exchange = Exchange.objects.get(active=True)
        for session in ExchangeSession.objects.filter(exchange=exchange):
            organizers: List[Person] = list(
                session.organizers.all().order_by("user__first_name")
            )
            assigned: List[Person] = list(
                session.assigned.all().order_by("user__first_name")
            )

            mail = self.get_mail(organizers)
            mail_subject, mail_content = self.prepare_mail(
                mail, session, organizers, assigned, team
            )
            output.append(
                {
                    RECEIVERS: ", ".join(
                        format_mail_person(organizer) for organizer in organizers
                    )
                    or session.department.email,
                    MAIL_SUBJECT: mail_subject,
                    MAIL_CONTENT: mail_content,
                }
            )

        return output, [RECEIVERS, MAIL_SUBJECT, MAIL_CONTENT]

    def format_assigned(self, assigned: List[Person], mark_english: bool) -> str:
        output: List[str] = []
        for person in assigned:
            output.append(f" - {format_mail_person(person)}" + " (communicatie in het Engels)" if mark_english and person.language == "en" else "")

        return "\n".join(output)

    def get_mail(self, organizers: List[Person]) -> Mail:
        language = DEFAULT_LANGUAGE
        for organizer in organizers:
            if organizer.language == "en":
                language = "en"
                break

        try:
            return Mail.objects.get(type=MAIL_TYPE, language=language)
        except Mail.DoesNotExist:
            return Mail.objects.get(type=MAIL_TYPE, language=DEFAULT_LANGUAGE)

    def prepare_mail(
        self,
        mail: Mail,
        session: ExchangeSession,
        organizers: List[Person],
        assigned: List[Person],
        team: str,
    ) -> Tuple[str, str]:
        choice = session.get_name_by_lang(mail.language)
        if organizers:
            organizers_names = conjunct(
                mail.language,
                list(organizer.given_names.strip() for organizer in organizers),
            )
        else:
            organizers_names = "organisator"  # TODO: translate

        choice_assignments = self.format_assigned(assigned, mail.language == "nl")

        data = {
            "choice": choice,
            "organizers": organizers_names,
            "count": str(len(assigned)),
            "choice_assignments": choice_assignments,
            "team": team,
        }
        return enrich_mail(mail.subject, data), enrich_mail(mail.text, data)


def conjunct(language: str, items: List[str]) -> str:
    if len(items) < 2:
        return items[0]

    return ", ".join(items[0:-1]) + CONJUNCT[language] + items[-1]


def format_mail_person(person: Person) -> str:
    return f"{person.full_name} <{person.email}>"


def write_data(
    filepath: str, fieldnames: List[str], enriched: List[Dict[str, str]]
) -> None:
    with open(filepath, mode="w", encoding="utf-8-sig") as csv_file:
        csv_writer = csv.DictWriter(csv_file, delimiter=";", fieldnames=fieldnames)
        csv_writer.writeheader()
        csv_writer.writerows(enriched)


def enrich_mail(text: str, data: Dict[str, str]) -> str:
    for key, value in data.items():
        text = text.replace(f"{{{{{key}}}}}", value)

    return text


def get_team_str() -> str:
    team = Group.objects.get(name="Team")
    persons = Person.objects.filter(user__groups=team).order_by("user__first_name")
    return ", ".join(person.full_name for person in persons)
