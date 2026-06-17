# Folder Structure

```text
ai_data_project/
  ai_data_project/
    settings.py
    urls.py
  dataapp/
    auto_train.py
    forms.py
    models.py
    preprocessing.py
    ml_models.py
    views.py
    urls.py
    migrations/
    ml_models/
      __init__.py
    preprocessing/
      __init__.py
    services/
    utils/
    visualization/
      charts.py
    templatetags/
      dataapp_extras.py
    templates/dataapp/
      ai_understand.html
      ai_report.html
  templates/dataapp/
    base.html
    home.html
    upload_success.html
    statistics.html
    visualize.html
    ai_train.html
    predict.html
  media/
    datasets/
    models/
  requirements.txt
  manage.py
```

The existing Django project is preserved. The new ML and preprocessing implementations live both in top-level compatibility modules and in the existing package folders so imports remain stable.
