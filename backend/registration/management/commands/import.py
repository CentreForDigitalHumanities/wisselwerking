import csv
import pathlib
from typing import Dict, List, Tuple, Optional
from django.contrib.auth.models import User
from django.core.management.base import BaseCommand, CommandError
import os
import datetime
import re

from registration.models import (
    Exchange,
    ExchangeSession,
    Department,
    Person,
    PersonMail,
    Registration,
)

ENROLLMENT_ADD = "_fd_Add"
ENROLLMENT_FIRSTNAME = "voornaam"
ENROLLMENT_LASTNAME = "achternaam"
ENROLLMENT_MAIL = "e_mailadres"
ENROLLMENT_DEPT = "afdeling"
ENROLLMENT_ASSIGNED = "toegewezen"
ENROLLMENT_CHOICES = ["eerste_keuze", "tweede_keuze", "derde_keuze"]

ignore_dept = ["HFS", "**GEEN**", "» Verras me", "Maak je keuze", "geen", "niet ingevuld", "n.v.t.", ""]
renames: Dict[str, str] = {}
dept_lookup: Dict[str, Department] = {}


class Command(BaseCommand):
    help = "Import data from existing enrollments"

    def add_arguments(self, parser):
        parser.add_argument("files", nargs="+", type=str)

    def handle(self, *args, **options):
        project_root = pathlib.Path(
            __file__
        ).parent.parent.parent.parent.parent.resolve()
        with open(
            os.path.join(project_root, "renames.csv"), mode="r", encoding="utf-8-sig"
        ) as csv_file:
            csv_reader = csv.DictReader(csv_file, delimiter=";")

            for row in csv_reader:
                old = row["old"].lower().strip()
                new = row["new"].strip()
                renames[old] = new
                renames[new.lower()] = new

        for department in Department.objects.all():
            names = department.name.split(" / ")
            for name in names:
                dept_lookup[name] = department

        for filename in options["files"]:
            filepath = os.path.join(project_root, filename)
            if not os.path.isfile(filepath):
                raise CommandError(f"File {filepath} does not exist")

            read_history_year(filepath)


def unique_username(first_name: str, prefix: str, last_name: str) -> str:
    full_name = " ".join([first_name.lower(), prefix.lower(), last_name.lower()])
    candidates: List[str] = [
        first_name.lower(),
        full_name,
    ]
    duplicate = 2
    while True:
        if candidates:
            candidate = candidates.pop(0)
        else:
            candidate = f"{full_name}{duplicate}"
            duplicate += 1
        candidate = re.sub(r"[\s\-_\.]+", "_", candidate).strip("_")
        try:
            User.objects.get(username=candidate)
        except User.DoesNotExist:
            return candidate


def read_history_year(filepath: str):
    with open(filepath, mode="r", encoding="utf-8-sig") as csv_file:
        csv_reader = csv.DictReader(csv_file, delimiter=";")

        for row in csv_reader:
            add = None
            for format in ["%d-%m-%Y %H:%M", "%d-%m-%Y, %H:%M",  "%d-%m-%y %H:%M", "%d-%m-%Y", "%d-%m-%y"]:
                try:
                    add = datetime.datetime.strptime(
                        row[ENROLLMENT_ADD], format
                    ).astimezone()
                except ValueError:
                    continue
                break
            if add is None:
                raise ValueError(f"Could not parse {row[ENROLLMENT_ADD]}")
            email = row[ENROLLMENT_MAIL].lower()
            # naam = row["naam"].split(' ', 1)
            # first_name = capitalize(naam[0])
            # prefix, last_name = format_last_name("" if len(naam) == 1 else naam[1])
            first_name = capitalize(row["voornaam"])
            prefix, last_name = format_last_name(row["achternaam"])
            person_dept_name = rename_dept(row[ENROLLMENT_DEPT])
            dept = lookup_dept(person_dept_name)
            assigned = lookup_dept(rename_dept(row[ENROLLMENT_ASSIGNED]), False)

            try:
                user = User.objects.get(email=email)
            except User.DoesNotExist:
                try:
                    pm = PersonMail.objects.get(address=email)
                    user = pm.person.user
                except PersonMail.DoesNotExist:
                    user = User()
                    user.username = unique_username(first_name, prefix, last_name)
                    user.email = email
            user.first_name = first_name
            user.last_name = last_name
            if user.date_joined > add:
                user.date_joined = add
            user.save()

            try:
                person = Person.objects.get(user=user)

                for registration in Registration.objects.filter(requestor=person):
                    if registration.date_time.year == add.year:
                        # removing existing registrations
                        registration.delete()


            except Person.DoesNotExist:
                person = Person()
                person.user = user
                person.save()
            person.prefix_surname = prefix
            if dept:
                person.departments.add(dept)
            else:
                person.other_affiliation = person_dept_name
            person.save()

            try:
                exchange = Exchange.objects.get(begin=add.year)
            except Exchange.DoesNotExist:
                exchange = Exchange()
                exchange.active = False
                exchange.begin = add.year
                exchange.end = add.year + 1
                exchange.enrollment_deadline = datetime.date(exchange.begin, 1, 1)
                exchange.save()

            if add.date() > exchange.enrollment_deadline:
                exchange.enrollment_deadline = add.date()
                exchange.save()

            if assigned:
                session = dept_session(exchange, assigned)
                session.assigned.add(person)
                session.save()

            for priority, column in enumerate(ENROLLMENT_CHOICES, 1):
                value = row[column]
                if re.match(r"^\-+$", value):
                    # empty
                    continue
                choice_dept = lookup_dept(rename_dept(value), True)
                choice = (
                    None if choice_dept == None else dept_session(exchange, choice_dept)
                )

                # choice is None if the registration is blank (e.g. assign me randomly)
                try:
                    Registration.objects.get(requestor=person, session=choice)
                except Registration.DoesNotExist:
                    registration = Registration()
                    registration.requestor = person
                    registration.session = choice
                    registration.priority = priority
                    registration.date_time = add
                    registration.save()

    return []


def dept_session(exchange: Exchange, department: Department) -> ExchangeSession:
    session = ExchangeSession.objects.filter(
        department=department, exchange=exchange
    ).first()
    if not session:
        session = ExchangeSession()
        session.department = department
        session.exchange = exchange
        session.participants_min = 0
        session.participants_max = 999
        session.session_count = 999
        session.save()

    return session


def lookup_dept(name: str, fail_on_key_error=False) -> Optional[Department]:
    if name in ignore_dept:
        return None

    try:
        return dept_lookup[name]
    except KeyError:
        message = f"Department {name} not found"
        if fail_on_key_error:
            raise CommandError(message)
        print(message)
        return None


def rename_dept(department: str) -> str:
    department = department.replace("\u2013", "-")
    department = re.sub(r"\s+", " ", department)
    department = department.strip()
    try:
        return renames[department.lower()]
    except KeyError:
        return department


def capitalize(value: str) -> str:
    output = ""
    separators = [" ", "-", ".", "'"]
    capitalize_next = True
    prev = ""

    for char in value:
        if char in separators:
            capitalize_next = True
        elif capitalize_next:
            capitalize_next = False
            char = char.upper()
        else:
            if prev == "I" and char.lower() == "j":
                # capitalize IJ correctly in Dutch
                char = char.upper()
            else:
                char = char.lower()
        output += char
        prev = char

    return output


def format_last_name(value: str) -> Tuple[str, str]:
    prefix_parts = []
    surname_parts = []
    for part in value.strip().split(" "):
        if not surname_parts and part.lower() in [
            "van",
            "von",
            "de",
            "der",
            "den",
            "die",
        ]:
            prefix_parts.append(part.lower())
        else:
            surname_parts.append(part)

    return (str.join(" ", prefix_parts), capitalize(str.join(" ", surname_parts)))
