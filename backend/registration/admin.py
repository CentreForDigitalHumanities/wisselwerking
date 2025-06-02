from typing import List, cast
from django import forms
from django.contrib import admin, messages
from django.contrib.postgres.aggregates import StringAgg
from django.db.models.query import QuerySet


from registration.models import (
    Person,
    Department,
    DepartmentDescription,
    Exchange,
    ExchangeDescription,
    ExchangeSession,
    ExchangeSessionDescription,
    Mail,
    PersonMail,
    Registration,
)


class ExchangeSessionInline(admin.TabularInline):
    model = ExchangeSession
    show_change_link = True
    readonly_fields = ("exchange", "subtitles", "assigned_count")
    fields = readonly_fields
    extra = 0
    can_delete = False
    max_num = 0
    ordering = ["exchange__begin"]


class DepartmentDescriptionInline(admin.TabularInline):
    model = DepartmentDescription
    max_num = 2


class DepartmentAdmin(admin.ModelAdmin):
    list_display = ["slug", "name"]

    inlines = [DepartmentDescriptionInline, ExchangeSessionInline]
    filter_horizontal = ["contact_persons"]

    def get_queryset(self, request):
        queryset = super().get_queryset(request)
        queryset = queryset.annotate(
            _name=StringAgg("description__name", " / "),
        ).order_by("_name")
        return queryset


class ExchangeDescriptionInline(admin.TabularInline):
    model = ExchangeDescription
    max_num = 2


class ExchangeAdmin(admin.ModelAdmin):
    inlines = [ExchangeDescriptionInline, ExchangeSessionInline]
    ordering = ["begin"]
    list_display = ["__str__", "active"]


class ExchangeSessionDescriptionInline(admin.StackedInline):
    model = ExchangeSessionDescription
    max_num = 2


class ExchangeSessionAdmin(admin.ModelAdmin):
    actions = ["copy_exchange"]
    list_display = ["department", "titles", "subtitles", "exchange"]
    list_filter = ["exchange", "department"]
    inlines = [ExchangeSessionDescriptionInline]
    filter_horizontal = ["assigned", "organizers"]
    readonly_fields = ["assigned"]

    def get_queryset(self, request):
        queryset = super().get_queryset(request)
        queryset = queryset.annotate(
            _name=StringAgg("department__description__name", " / "),
        ).order_by("exchange", "_name")
        return queryset

    @admin.action(description="Copy to active exchange")
    def copy_exchange(self, request, queryset):
        exchange = Exchange.objects.get(active=True)
        for obj in queryset:
            session = cast(ExchangeSession, obj)
            copy = ExchangeSession()
            copy.exchange = exchange
            copy.department = session.department
            copy.participants_min = session.participants_min
            copy.participants_max = session.participants_max
            copy.session_count = session.session_count
            copy.save()
            copy.organizers.set(session.organizers.all())

            for description in session.description.all():
                description.pk = None
                description.exchange = copy
                description.save()

        messages.success(request, "Successfully copied to latest exchange!")


class MailAdmin(admin.ModelAdmin):
    list_display = ["type", "language", "subject"]
    ordering = ["language", "type"]


class PersonRegistrationsInline(admin.TabularInline):
    model = Registration
    readonly_fields = ("session", "priority", "date_time")
    extra = 0
    can_delete = False
    max_num = 0
    ordering = ["session__exchange__begin"]


class PersonMailInline(admin.TabularInline):
    model = PersonMail
    extra = 0


class PersonForm(forms.ModelForm):
    given_names = forms.CharField()
    surnames = forms.CharField()
    main_mail = forms.ChoiceField(choices=[], required=False)
    sessions = forms.CharField(widget=forms.Textarea, disabled=True, required=False)
    organizes = forms.CharField(widget=forms.Textarea, disabled=True, required=False)

    def save(self, commit=True):
        main_mail = self.cleaned_data.get("main_mail", None)
        given_names = self.cleaned_data.get("given_names", None)
        surnames = self.cleaned_data.get("surnames", None)

        person: Person = self.instance

        if main_mail != person.user.email:
            # swap PersonMail objects
            pm = PersonMail.objects.get(person=person, address=main_mail)
            pm.address = person.user.email
            # record that the person's mail is different now
            # so this address will be saved
            person.user.email = main_mail
            pm.person = person
            pm.save()

        person.user.first_name = given_names
        person.user.last_name = surnames
        person.user.save()

        # ...do something with extra_field here...
        return super().save(commit=commit)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        person: Person = self.instance
        emails = set([person.email])
        for pm in PersonMail.objects.filter(person=person):
            emails.add(pm.address)
        self.fields["main_mail"].choices = set((m, m) for m in emails)

        self.fields["given_names"].initial = person.given_names
        self.fields["surnames"].initial = person.surnames
        self.fields["main_mail"].initial = person.email

        # get and display all the sessions
        self.fields["organizes"].initial = self.list_sessions(
            ExchangeSession.objects.filter(organizers=person)
        )
        self.fields["sessions"].initial = self.list_sessions(
            ExchangeSession.objects.filter(assigned=person)
        )

    def list_sessions(self, query_set: QuerySet[Person]) -> str:
        return "\n".join(sorted(str(session) for session in query_set))

    class Meta:
        model = Person
        fields = "__all__"


class PersonAdmin(admin.ModelAdmin):
    form = PersonForm
    actions = ["merge_persons"]
    list_display = ["full_name", "get_affiliation"]
    ordering = ["user__first_name", "user__last_name"]
    filter_horizontal = ["departments"]
    fields = (
        "user",
        "given_names",
        "prefix_surname",
        "surnames",
        "main_mail",
        "url",
        "language",
        "departments",
        "other_affiliation",
        "organizes",
        "sessions",
    )
    inlines = [PersonRegistrationsInline, PersonMailInline]

    @admin.action(description="Merge person records")
    def merge_persons(self, request, queryset: QuerySet):
        persons: List[Person] = list(queryset.all())
        if len(persons) != 2:
            messages.error(request, "Select two records!")
            return

        persons[0].move_to(persons[1])

        messages.success(
            request, f"Successfully merged records for {persons[0].full_name}!"
        )

    def has_add_permission(self, request, obj=None):
        return False


class RegistrationAdmin(admin.ModelAdmin):
    list_display = ["requestor", "session", "priority", "date_time"]
    ordering = ["date_time"]
    list_filter = ["session__department", "session__exchange"]


admin.site.register(Person, PersonAdmin)
admin.site.register(Department, DepartmentAdmin)
admin.site.register(Exchange, ExchangeAdmin)
admin.site.register(ExchangeSession, ExchangeSessionAdmin)
admin.site.register(Mail, MailAdmin)
admin.site.register(Registration, RegistrationAdmin)
