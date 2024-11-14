from typing import List
from registration.models import (
    Department,
    DepartmentDescription,
    Exchange,
    ExchangeSession,
    ExchangeSessionDescription,
    Person,
    Registration,
)
from rest_framework.decorators import api_view
from rest_framework.response import Response


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
                    >= session.participants_max
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
