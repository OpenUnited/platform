from django import forms


class TalentProfile(forms.ModelForm):
    class Meta:
        model = None
        fields = "__all__"
