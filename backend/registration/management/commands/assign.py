from typing import Any, Dict, List, Set
from django.core.management.base import BaseCommand

from registration.models import Exchange, ExchangeSession, Person, Registration


class Command(BaseCommand):
    help = "Assign the persons to the exchanges for the current session"

    exchange: Exchange
    requestors: Set[Person] = set()
    unassigned_requestors: Set[Person] = set()
    assigned_random: Set[Person] = set()
    # key is the pk
    capacities: Dict[any, int] = {}
    session_counts: Dict[any, int] = {}

    def handle(self, *args, **options):
        self.exchange = Exchange.objects.get(active=True)

        # clear all current assignments
        for session in ExchangeSession.objects.filter(exchange=self.exchange):
            session.assigned.clear()

        # get all the registrations
        registrations = list(
            Registration.objects.filter(exchange=self.exchange).order_by("date_time")
        )

        # mark everyone as unassigned
        for registration in registrations:
            self.requestors.add(registration.requestor)
            self.unassigned_requestors.add(registration.requestor)

        # the highest priority count is only limited
        # by how many sessions someone might have requested,
        # which could be at most the number of available sessions
        max_priority = 1

        print("Notes from requestors: ")
        requestor = None # multiple registration per requestor
        for registration in registrations:
            if registration.priority > max_priority:
                max_priority = registration.priority
            if registration.notes and requestor != registration.requestor:
                print(f"# {registration.requestor}")
                print(registration.notes + "\n")
                requestor = registration.requestor

        # first try to give everyone their first pick
        for priority in range(1, max_priority + 1):
            for registration in registrations:
                if registration.priority == priority:
                    self.attempt_placement(registration)

        print(f"Unassigned requestors: {len(self.unassigned_requestors)}")

        empty_sessions: List[ExchangeSession] = []
        # we want more!
        too_low_sessions: List[ExchangeSession] = []
        for session in ExchangeSession.objects.filter(exchange=self.exchange):
            if session.assigned.count() == 0:
                empty_sessions.append(session)
            elif session.participants_min > self.session_counts[session.pk]:
                too_low_sessions.append(session)

        print(f"Empty sessions: {len(empty_sessions)}")
        for session in empty_sessions:
            print(
                f" - {session} (pk={session.pk}; max_participants={session.participants_max*session.session_count})"
            )

        if len(too_low_sessions) > 0:
            print(f"Too few participants in sessions: {len(too_low_sessions)}")
            for session in too_low_sessions:
                print(
                    f" - {session} (pk={session.pk}; min_participants={session.participants_min}; actual={self.session_counts[session.pk]})"
                )

        print(f"Requestors: {len(self.requestors)}")
        print(f"Random assignees left: {len(self.assigned_random)}")

        for person in self.assigned_random:
            self.assign_random(person)

        print(f"Unassigned persons left: {len(self.unassigned_requestors)}")
        for person in self.unassigned_requestors:
            print(f"{person}")


    def get_capacity(self, session_pk: Any) -> int:
        try:
            return self.capacities[session_pk]
        except KeyError:
            session = ExchangeSession.objects.get(
                pk=session_pk
            )
            capacity = self.capacities[session_pk] = session.participants_max * session.session_count
            self.session_counts[session_pk] = 0
            return capacity

    def assign_random(self, person: Person):
        print(f"{person} already participated in: ")
        for session in ExchangeSession.objects.filter(assigned=person):
            print(f" - {session}")

        while True:
            try:
                session_pk = input("Assign to pk? ")
                session = ExchangeSession.objects.get(pk=int(session_pk))
                if self.get_capacity(session.pk) <= 0:
                    raise Exception("Not enough capacity!")
                elif session.exchange != self.exchange:
                    raise Exception("Invalid exchange")
                else:
                    print(f"Assigned to {session}")
                    break
            except Exception as error:
                print(type(error))
                print(error)

        self.perform_placement(person, session, False)

    def attempt_placement(self, registration: Registration):
        person = registration.requestor
        if person not in self.unassigned_requestors:
            # already assigned to something
            return

        if registration.session is None:
            # assign to something random (done at the end)
            self.assigned_random.add(person)
            self.unassigned_requestors.remove(person)
        else:
            # is there capacity left on this exchange?
            capacity = self.get_capacity(registration.session.pk)
            if capacity > 0:
                self.perform_placement(registration.requestor, registration.session)

    def perform_placement(self, person: Person, session: ExchangeSession, remove=True):
        # lower capacity by one
        self.capacities[session.pk] -= 1
        self.session_counts[session.pk] += 1

        if remove:
            self.unassigned_requestors.remove(person)

        session.assigned.add(person)
