import pathlib
from typing import Dict, List, Tuple
from django.core.management.base import BaseCommand, CommandError
import os

from .organizers_mail import (
    enrich_mail,
    format_mail_person,
    write_data,
)
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

MAIL_TYPE = "assigned"
CONJUNCT = {"en": " and ", "nl": " en "}


class Command(BaseCommand):
    help = "Creates a file with a mail for the participants"

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
            assigned: List[Person] = list(
                session.assigned.all().order_by("user__first_name")
            )

            for participant in assigned:
                mail = Mail.objects.get(type=MAIL_TYPE, language=participant.language)
                mail_subject, mail_content = self.prepare_mail(
                    mail, session, participant, team
                )
                output.append(
                    {
                        RECEIVERS: format_mail_person(participant),
                        MAIL_SUBJECT: mail_subject,
                        MAIL_CONTENT: mail_content,
                    }
                )

        return output, [RECEIVERS, MAIL_SUBJECT, MAIL_CONTENT]

    def prepare_mail(
        self,
        mail: Mail,
        session: ExchangeSession,
        participant: Person,
        team: str,
    ) -> Tuple[str, str]:
        data = {
            "given_names": participant.given_names,
            "assigned": session.get_name_by_lang(participant.language),
            "team": team,
        }
        return enrich_mail(mail.subject, data), enrich_mail(mail.text, data)
