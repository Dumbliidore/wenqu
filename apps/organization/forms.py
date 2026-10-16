import re

from django import forms
from operation.models import UserAsk


class UserAskForm(forms.ModelForm):
    class Meta:
        model = UserAsk
        fields = ["name", "mobile", "course_name"]

    def clean_mobile(self):
        mobile = self.cleaned_data["mobile"]
        if not re.match(r"^1[3-9]\d{9}$", mobile):
            raise forms.ValidationError("手机号码非法", code="mobile_invalid")
        return mobile
