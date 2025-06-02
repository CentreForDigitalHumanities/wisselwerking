from dataclasses import dataclass
import os
import csv
import pathlib

from typing import Dict, List, Tuple, cast
from django.core.management.base import BaseCommand
from registration.models import ExchangeSession, Person


HISTORY_YEARS = "jaren"
HISTORY_HOW_MANY = "hoeveelste_keer"
ENROLLMENT_DEPT = "afdeling"
ASSIGNED_CHOICE = "toegewezen"


@dataclass
class Enrollment:
    assigned_dept: str
    from_dept: str


class Command(BaseCommand):
    help = "Export statistics about the enrollments"
    project_root: str

    def handle(self, *args, **options):
        self.project_root = pathlib.Path(
            __file__
        ).parent.parent.parent.parent.parent.resolve()

        fieldnames, rows = self.get_enrollments()
        self.write_file("history.csv", fieldnames, rows)

        fieldnames, rows = self.new_participants_each_year()
        self.write_file("history_new_participants.csv", fieldnames, rows)

        fieldnames, rows = self.histogram()
        self.write_file("history_histogram.csv", fieldnames, rows)

        fieldnames, rows = self.depts_histogram()
        self.write_file("history_depts_histogram.csv", fieldnames, rows)

    def write_file(
        self, filename: str, keys: List[str], rows: List[Dict[str, str]]
    ) -> None:
        with open(
            os.path.join(self.project_root, filename), "w", encoding="utf-8-sig"
        ) as csv_file:
            writer = csv.DictWriter(csv_file, fieldnames=keys, delimiter=";")
            writer.writeheader()
            writer.writerows(rows)

    def get_enrollments(self) -> Tuple[List[str], List[Dict[str, str]]]:
        participant_count: Dict[any, int] = {}
        keys = [
            "id",
            "count",
            HISTORY_HOW_MANY,
            HISTORY_YEARS,
            ENROLLMENT_DEPT,
            ASSIGNED_CHOICE,
        ]
        rows: List[Dict[str, str]] = []

        for session in ExchangeSession.objects.all():
            for enrollment in session.assigned.all():
                person: Person = enrollment
                participant_id = person.pk
                try:
                    how_many = participant_count[participant_id] + 1
                except KeyError:
                    participant_count[participant_id] = 0
                    how_many = 1
                participant_count[participant_id] += 1
                rows.append(
                    {
                        "id": participant_id,
                        "count": 1,  # makes pivot tables easier to create
                        HISTORY_HOW_MANY: how_many,
                        HISTORY_YEARS: f"{session.exchange.begin}-{session.exchange.end}",
                        ENROLLMENT_DEPT: person.get_affiliation(),
                        ASSIGNED_CHOICE: session.get_prefer_dutch_name(),
                    }
                )

        return keys, rows

    def per_year_enrollment(self):
        per_year: Dict[str, List[any]] = {}
        per_year_enrollment: Dict[str, List[Enrollment]] = {}

        for session in ExchangeSession.objects.all():
            for person in session.assigned.all():
                years = f"{session.exchange.begin}-{session.exchange.end}"
                participant_id = person.id
                enrollment = Enrollment(
                    session.get_prefer_dutch_name(),
                    cast(Person, person).get_affiliation(),
                )
                try:
                    per_year[years].append(participant_id)
                    per_year_enrollment[years].append(enrollment)
                except KeyError:
                    per_year[years] = [participant_id]
                    per_year_enrollment[years] = [enrollment]

        return per_year, per_year_enrollment

    def new_participants_each_year(self) -> Tuple[List[str], List[Dict[str, str]]]:
        # new participants each year
        per_year, _ = self.per_year_enrollment()

        all_previous_years = list(sorted(per_year.keys()))[:-1]

        fieldnames = [HISTORY_YEARS] + all_previous_years + ["completely_new"]

        previous_years: List[str] = []
        rows: List[Dict[str, str]] = []
        i = 0
        for years in sorted(per_year.keys()):
            new_count = 0
            prev_years_counts = dict.fromkeys(all_previous_years, 0)
            for p in per_year[years]:
                for prev_years in all_previous_years[0:i]:
                    if prev_years != years and p in per_year[prev_years]:
                        prev_years_counts[prev_years] += 1
                        break
                else:
                    new_count += 1

            rows.append(
                {HISTORY_YEARS: years, **prev_years_counts, "completely_new": new_count}
            )

            previous_years.insert(0, years)
            i += 1

        return fieldnames, rows

    def histogram(self):
        # how many times do people participate over the years?
        histogram: Dict[int, int] = {}

        participant_count: Dict[any, int] = {}

        for session in ExchangeSession.objects.all():
            for enrollment in session.assigned.all():
                person: Person = enrollment
                participant_id = person.pk
                try:
                    participant_count[participant_id] + 1
                except KeyError:
                    participant_count[participant_id] = 0
                participant_count[participant_id] += 1

        for participant_id, participant_count in participant_count.items():
            try:
                histogram[participant_count] += 1
            except KeyError:
                histogram[participant_count] = 1

        rows = [{"times": times, "count": count} for times, count in sorted(histogram.items())]
        return ["times", "count"], rows

    def depts_histogram(self):
        # how many different departments participated?
        _, per_year_enrollment = self.per_year_enrollment()

        rows: List[Dict[str, str]] = []

        for years, enrollments in per_year_enrollment.items():
            assigned_depts = set()
            from_depts = set()
            for e in enrollments:
                assigned_depts.add(e.assigned_dept)
                from_depts.add(e.from_dept)

            rows.append(
                {
                    HISTORY_YEARS: years,
                    "assigned_depts": len(assigned_depts),
                    "from_depts": len(from_depts),
                }
            )

        return [HISTORY_YEARS, "assigned_depts", "from_depts"], rows
