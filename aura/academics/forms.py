from django import forms

from .models import ClassGroup, Enrollment, Schedule, Subject


class SubjectForm(forms.ModelForm):
    class Meta:
        model = Subject
        fields = ("code", "name")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for _, field in self.fields.items():
            field.widget.attrs["class"] = "form-control"


class ClassGroupForm(forms.ModelForm):
    class Meta:
        model = ClassGroup
        fields = ("subject", "name")

    def __init__(self, *args, **kwargs):
        user = kwargs.pop("user", None)
        super().__init__(*args, **kwargs)
        self.fields["name"].widget.attrs["class"] = "form-control"
        self.fields["subject"].widget.attrs["class"] = "form-select"
        if user is not None:
            self.fields["subject"].queryset = Subject.objects.filter(professor=user).order_by("code")


class ScheduleForm(forms.ModelForm):
    class Meta:
        model = Schedule
        fields = ("class_group", "weekday", "start_time", "end_time")
        widgets = {
            "start_time": forms.TimeInput(attrs={"type": "time"}),
            "end_time": forms.TimeInput(attrs={"type": "time"}),
        }

    def __init__(self, *args, **kwargs):
        user = kwargs.pop("user", None)
        super().__init__(*args, **kwargs)
        self.fields["class_group"].widget.attrs["class"] = "form-select"
        self.fields["weekday"].widget.attrs["class"] = "form-select"
        self.fields["start_time"].widget.attrs["class"] = "form-control"
        self.fields["end_time"].widget.attrs["class"] = "form-control"
        if user is not None:
            self.fields["class_group"].queryset = ClassGroup.objects.filter(professor=user).select_related("subject")


class EnrollmentForm(forms.ModelForm):
    class Meta:
        model = Enrollment
        fields = ("class_group", "student")

    def __init__(self, *args, **kwargs):
        user = kwargs.pop("user", None)
        super().__init__(*args, **kwargs)
        self.fields["class_group"].widget.attrs["class"] = "form-select"
        self.fields["student"].widget.attrs["class"] = "form-select"
        if user is not None:
            self.fields["class_group"].queryset = ClassGroup.objects.filter(professor=user).select_related("subject")
