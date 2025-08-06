# gptshenpi

This repository provides core data models for an approval workflow system.
Models are defined using [SQLAlchemy](https://www.sqlalchemy.org/) in the
`models` directory. These models cover users, organizations, departments,
approval templates, forms, records and notifications to support approval
processing, delegation and push notifications.

## Admin Frontend

Run `python app.py` and open `/admin` in a browser to access a simple web
interface. Log in with the default admin credentials (`admin`/`admin`) to
manage organizations, departments, users, approval templates, and verification
staff through basic forms.
