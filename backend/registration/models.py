from typing import Set
from django.contrib import admin
from django.contrib.auth.models import User
from django.db import models, transaction
from django.dispatch import receiver
from django.db.models.signals import pre_save, post_save
import re

LANGUAGES = [("en", "English"), ("nl", "Dutch")]


# APPLICATION: REGISTRATION


class Mail(models.Model):
    MAIL_TYPES = [
        # sent when someone filled in the registration form
        ("confirm_registration", "Confirm Registration"),
        # sent to the participant when an exchange has been assigned
        ("assigned", "Assigned"),
        # overview sent to the organizer of an exchange with the participants
        ("overview_assigned", "Overview Assigned"),
        # mail the organizers that no participants are registered for this exchange
        ("no_participants", "No Participants")
    ]
    type = models.CharField(choices=MAIL_TYPES)
    language = models.CharField(choices=LANGUAGES)
    subject = models.CharField(max_length=150)
    text = models.TextField()


class Person(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)

    @property
    def email(self):
        return self.user.email

    @property
    def given_names(self):
        return self.user.first_name

    @property
    def surnames(self):
        return self.user.last_name

    @property
    def full_name(self):
        name = " ".join(
            filter(
                lambda x: x and not x.isspace(),
                [self.given_names, self.prefix_surname, self.surnames],
            )
        )
        if not name or name.isspace():
            return self.user.username
        return name

    prefix_surname = models.CharField(blank=True)

    url = models.URLField(blank=True)
    language = models.CharField(choices=LANGUAGES)
    external = models.BooleanField(default=False)
    departments = models.ManyToManyField("Department", blank=True)
    other_affiliation = models.CharField(blank=True)

    @admin.display(
        description="Affiliation",
        boolean=False,
    )
    def get_affiliation(self):
        departments = [str(p) for p in self.departments.all()]
        if len(self.other_affiliation):
            departments.append(self.other_affiliation)
        return ", ".join(departments)

    @transaction.atomic
    def move_to(self, target: "Person"):
        """Moves this person record to another person record. Deletes
        this objects afterwards

        Args:
            target (Person): the target to move to
        """
        if target.pk > self.pk:
            # always move to the oldest record
            return target.move_to(self)

        emails: Set[str] = set()
        emails.add(target.email)
        emails.add(self.email)

        for pm in PersonMail.objects.filter(person=target):
            emails.add(pm.address)

        for pm in PersonMail.objects.filter(person=self):
            if pm.address not in emails:
                emails.add(pm.address)
                pm.person = target
            else:
                pm.delete()

        # prefer @uu.nl
        for email in emails:
            if email.endswith("@uu.nl"):
                target.user.email = email

        # prefer newest @uu.nl
        if self.user.email.endswith("@uu.nl"):
            target.user.email = self.user.email

        for email in emails:
            if target.email != email:
                try:
                    PersonMail.objects.get(person=target, address=email)
                except PersonMail.DoesNotExist:
                    pm = PersonMail()
                    pm.person = target
                    pm.address = email
                    pm.save()

        # self is the newest information
        target.user.first_name = self.user.first_name
        target.user.last_name = self.user.last_name
        target.prefix_surname = self.prefix_surname

        if (
            target.user.last_login is not None
            and self.user.last_login is not None
            and self.user.last_login > target.user.last_login
        ):
            target.user.last_login = self.user.last_login

        target.departments.aadd(self.departments.all())
        target.other_affiliation = " ".join(
            set([target.other_affiliation, self.other_affiliation])
        ).strip()

        if self.user.date_joined < target.user.date_joined:
            target.user.date_joined = self.user.date_joined

        Registration.objects.filter(requestor=self).update(requestor=target)

        for department in Department.objects.filter(contact_persons=self):
            department.contact_persons.add(target.pk)

        for session in ExchangeSession.objects.filter(assigned=self):
            session.assigned.add(target.pk)

        for session in ExchangeSession.objects.filter(organizers=self):
            session.organizers.add(target.pk)

        self.user.delete()
        self.delete()
        target.user.save()
        target.save()

    def __str__(self):
        return self.full_name


class PersonMail(models.Model):
    """Defines an alternative email address"""

    person = models.ForeignKey(Person, on_delete=models.CASCADE)
    address = models.EmailField(unique=True)

    def save(self, *args, **kwargs):
        if self.person.email == self.address:
            # prevent saving when this is the same address as the person
            # this can happen when updating the main address of a user
            return

        super().save(*args, **kwargs)


class Department(models.Model):
    slug = models.SlugField(blank=False, unique=True)
    email = models.EmailField(
        blank=True, help_text="Email address of the department itself"
    )
    url = models.URLField(blank=True)
    contact_persons = models.ManyToManyField(Person, blank=True)

    avatar = models.FileField(blank=True)

    @property
    @admin.display(
        ordering="_name",
        description="Name of the department",
        boolean=False,
    )
    def name(self):
        descriptions = set(d.name for d in self.description.all())
        if not descriptions:
            return "UNKNOWN DEPARTMENT"
        return " / ".join(descriptions)

    def __str__(self):
        return self.name

    class Meta:
        ordering = ["slug"]


class DepartmentDescription(models.Model):
    department = models.ForeignKey(
        Department, on_delete=models.CASCADE, related_name="description"
    )
    name = models.CharField(max_length=150)
    description = models.TextField(blank=True)
    language = models.CharField(choices=LANGUAGES)


class Exchange(models.Model):
    begin = models.IntegerField(unique=True)
    end = models.IntegerField(unique=True)
    enrollment_deadline = models.DateField()
    active = models.BooleanField()

    def __str__(self):
        return f"{self.begin}-{self.end}"

    class Meta:
        unique_together = ["begin", "end"]


class ExchangeDescription(models.Model):
    exchange = models.ForeignKey(Exchange, on_delete=models.CASCADE)
    text = models.TextField()
    language = models.CharField(choices=LANGUAGES)


class ExchangeSession(models.Model):
    exchange = models.ForeignKey(Exchange, on_delete=models.CASCADE)
    department = models.ForeignKey(Department, on_delete=models.CASCADE)
    assigned = models.ManyToManyField(
        Person, blank=True, related_name="exchange_assignees"
    )

    participants_min = models.IntegerField()
    participants_max = models.IntegerField()

    session_count = models.IntegerField()

    organizers = models.ManyToManyField(
        Person, blank=True, related_name="exchange_organizers"
    )

    @property
    def assigned_count(self):
        return self.assigned.count()

    @property
    def titles(self):
        titles = set(d.title for d in self.description.all())
        if not titles:
            return None
        return " / ".join(titles)

    @property
    def subtitles(self):
        subtitles = set(d.subtitle for d in self.description.all())
        if not subtitles:
            return None
        return " / ".join(subtitles)

    def get_prefer_dutch_name(self):
        for description in self.description.all():
            d: ExchangeSessionDescription = description
            if d.language == "nl":
                if d.subtitle:
                    return f"{d.title} {d.subtitle}"
                if d.title:
                    return d.title

        return self.__str__()

    def __str__(self):
        if self.subtitles:
            return f"{self.exchange} {self.titles} ({self.subtitles})"
        elif self.titles:
            return f"{self.exchange} {self.titles}"
        else:
            return f"{self.exchange} {self.department}"


class ExchangeSessionDescription(models.Model):
    exchange = models.ForeignKey(
        ExchangeSession, on_delete=models.CASCADE, related_name="description"
    )
    title = models.CharField(blank=True)
    subtitle = models.CharField(blank=True)
    intro = models.TextField()
    program = models.TextField()
    language = models.CharField(choices=LANGUAGES)
    date = models.CharField()
    location = models.CharField()


class Registration(models.Model):
    requestor = models.ForeignKey(Person, on_delete=models.CASCADE)
    session = models.ForeignKey(
        ExchangeSession,
        blank=True,
        null=True,
        on_delete=models.CASCADE,
        help_text="Keep empty for assigning to a random session",
    )
    priority = models.IntegerField()
    date_time = models.DateTimeField()


@receiver(pre_save, sender=Department)
def to_lower_slug(sender, instance: Department, **kwargs):
    instance.slug = (
        re.sub(r"[-&\(\)\s]+", "_", instance.slug).lower().strip("_")
        if isinstance(instance.slug, str)
        else ""
    )


@receiver(pre_save, sender=User)
def to_lower_username(sender, instance: User, **kwargs):
    instance.username = (
        instance.username.lower() if isinstance(instance.username, str) else ""
    )


@receiver(pre_save, sender=Exchange)
def active_exchange(sender, instance: Exchange, **kwargs):
    """Only one exchange can be active"""
    if instance.active:
        # deactivate all other exchanges
        for exchange in Exchange.objects.all():
            if exchange.active and exchange.begin != instance.begin:
                exchange.active = False
                exchange.save()


@receiver(post_save, sender=User)
def add_person(sender, instance: User, **kwargs):
    """Add a person for every user"""

    try:
        Person.objects.get(user=instance)
    except Person.DoesNotExist:
        person = Person()
        person.user = instance
        person.save()
