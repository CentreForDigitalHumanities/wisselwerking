from datetime import datetime, timezone
from typing import Dict, List
from registration.models import (
    Department,
    DepartmentDescription,
    Exchange,
    ExchangeDescription,
    ExchangeSession,
    ExchangeSessionDescription,
    Person,
    Registration,
    Mail,
    get_team_str,
    unique_username,
)
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework.request import Request
from django.core.mail import send_mail
from django.contrib.auth.models import User


@api_view()
def current_exchange(request):
    exchange = Exchange.objects.get(active=True)
    descriptions = list(ExchangeDescription.objects.filter(exchange=exchange))
    return Response(
        {
            "pk": exchange.pk,
            "begin": exchange.begin,
            "end": exchange.end,
            "enrollment_deadline": exchange.enrollment_deadline,
            "descriptions": [
                {
                    "language": description.language,
                    "text": description.text,
                }
                for description in descriptions
            ],
        }
    )


@api_view()
def available_sessions(request):
    exchange = Exchange.objects.get(active=True)
    response = []
    for session in ExchangeSession.objects.filter(exchange=exchange):
        organizers: List[Person] = list(session.organizers.all())
        descriptions = list(ExchangeSessionDescription.objects.filter(exchange=session))
        response.append(
            {
                "pk": session.pk,
                "descriptions": [
                    {
                        "date": description.date,
                        "language": description.language,
                        "location": description.location,
                        "intro": description.intro,
                        "program": description.program,
                        "title": description.title,
                        "subtitle": description.subtitle,
                    }
                    for description in descriptions
                ],
                "organizers": [
                    {"fullName": organizer.full_name, "url": organizer.url}
                    for organizer in organizers
                ],
                "participantsMin": session.participants_min,
                "participantsMax": session.participants_max,
                "sessionCount": session.session_count,
                "full": (
                    Registration.objects.filter(session=session, priority=1).count()
                    >= session.participants_max * session.session_count + 1 # just in case the first can't make it
                ),
            }
        )
    return Response(response)


@api_view()
def departments(request):
    departments = Department.objects.all()
    response = []
    for department in departments:
        response.append(
            {
                "slug": department.slug,
                "descriptions": [
                    {
                        "name": description.name,
                        "text": description.description,
                        "language": description.language,
                    }
                    for description in DepartmentDescription.objects.filter(
                        department=department
                    )
                ],
            }
        )
    return Response(response)


@api_view(["POST"])
def register(request: Request):
    email = request.data["email"].lower()
    person = Person.get_by_email(email)
    first_name = request.data["firstName"]
    prefix = request.data["tussenvoegsel"]
    last_name = request.data["lastName"]
    language = request.data["language"]

    # make sure the person exists
    if not person:
        user = User()
        user.username = unique_username(first_name, prefix, last_name)
        user.email = email
        user.first_name = first_name
        user.last_name = last_name
        user.save()

        person = Person()
        person.user = user

    # make sure the department exists
    # TODO: fix the list of departments
    # department_slug = request.data["department"]
    # try:
    #     department = Department.objects.get(slug=department_slug)
    # except Department.DoesNotExist:
    #     department = None

    # if department is None:
    #     try:
    #         department = DepartmentDescription.objects.get(
    #             name=department_slug
    #         ).department
    #     except DepartmentDescription.DoesNotExist:
    #         pass

    # if not department:
    #     department = Department()
    #     department.slug = department_slug
    #     department.save()

    #     dd = DepartmentDescription()
    #     dd.name = department_slug
    #     dd.language = language
    #     dd.department = department
    #     dd.save()

    person.other_affiliation = request.data["department"]
    person.prefix_surname = prefix
    person.language = language

    # if not person.departments.contains(department):
    #     person.departments.add(department)

    person.save()

    person.user.first_name = first_name
    person.user.last_name = last_name
    person.user.save()

    exchange = Exchange.objects.get(active=True)

    # registering again? replace any existing registrations on this exchange
    Registration.objects.filter(requestor=person, exchange=exchange).delete()

    registrations: List[Registration] = []
    for sp in request.data["sessionPriorities"]:
        registration = Registration()
        registration.requestor = person
        registration.priority = sp["priority"]
        registration.exchange = exchange
        registration.date_time = datetime.now(timezone.utc)
        pk = sp["session"]["pk"]
        if pk != 0:
            session = ExchangeSession.objects.get(pk=pk)
            registration.session = session
        registration.notes = request.data["notes"]
        registration.reason = request.data["reason"]
        registration.save()
        registrations.append(registration)

    send_data(request.data, registrations, person)
    send_confirmation(request.data, registrations, person)

    return Response({"success": True})


def send_data(data, registrations: List[Registration], person: Person):
    send_mail(
        "Aanmelding ontvangen",
        "Aanmelding ontvangen!\nIngevulde formulier:\n"
        + format_data(data, registrations, person),
        "wisselwerking.gw@uu.nl",
        ["wisselwerking.gw@uu.nl"],
    )


def send_confirmation(data, registrations: List[Registration], person: Person):
    mail = Mail.objects.get(type="confirm_registration", language=data["language"])
    send_mail(
        mail.subject,
        format_text(
            mail.text, {"given_names": person.given_names, "team": get_team_str()}
        )
        + "\n"
        + format_data(data, registrations, person),
        "wisselwerking.gw@uu.nl",
        [person.email],
    )


def format_data(data, registrations: List[Registration], person: Person) -> str:
    choices: List[str] = []
    for registration in registrations:
        if registration.session is None:
            choices.append("Verras mij")
        else:
            choices.append(registration.session.titles)

    return f"""
Taal: {data['language']}
Naam: {person.given_names}
E-mail: {person.email}
Afdeling: {data['department']}
Keuzes: {'; '.join(choices)}
Opmerkingen: {data['notes']}
Reden van deelname: {data['reason']}
"""


def format_text(text: str, data: Dict[str, str]) -> str:
    for key, value in data.items():
        text = text.replace(f"{{{{{key}}}}}", value)

    return text
