from django import forms


class CsvUploadForm(forms.Form):
    csv_file = forms.FileField(
        label="CSV file",
        widget=forms.ClearableFileInput(attrs={"class": "form-control", "accept": ".csv"}),
    )

    def clean_csv_file(self):
        csv_file = self.cleaned_data["csv_file"]
        if not csv_file.name.lower().endswith(".csv"):
            raise forms.ValidationError("Please upload a CSV file.")
        return csv_file


class TargetSelectionForm(forms.Form):
    target_column = forms.ChoiceField(widget=forms.Select(attrs={"class": "form-select"}))

    def __init__(self, *args, columns=None, **kwargs):
        super().__init__(*args, **kwargs)
        columns = columns or []
        self.fields["target_column"].choices = [("", "Choose target column")] + [
            (c, c) for c in columns
        ]
