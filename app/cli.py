import click
from flask.cli import with_appcontext
from app.extensions import db
from app.models.user import User
from app.models.org import Org
from app.models.org_membership import OrgMembership, ROLE_OWNER, ROLE_ADMIN, ROLE_MEMBER 

def _get_or_create_org(name: str) -> Org:
    org = db.session.query(Org).filter(Org.name == name).one_or_none()
    if org:
        return org
    org = Org(name=name, is_active=True)
    db.session.add(org)
    db.session.flush()
    return org

@click.group()
def bootstrap():
    """Bootstrap helpers."""

@bootstrap.command("owner")
@click.option("--org-name", required=True)
@click.option("--email", required=True)
@click.option("--password", required=True)
@with_appcontext
def bootstrap_owner(org_name, email, password):
    # fail fast if user exists
    if db.session.query(User).filter_by(email=email).count():
        raise click.ClickException("User already exists")

    org = _get_or_create_org(org_name)

    user = User(email=email, is_active=True)
    user.set_password(password)
    user.org_id = org.id
    db.session.add(user)
    db.session.flush()

    db.session.add(OrgMembership(org_id=org.id, user_id=user.id, role=ROLE_OWNER))
    db.session.commit()

    click.echo(f"Bootstrap complete: org_id={org.id} owner_user_id={user.id} email={email}")

@click.group()
def users():
    """User management."""

@users.command("create")
@click.option("--email", required=True)
@click.option("--password", required=True)
@click.option("--org-id", type=int, required=True, help="Existing org id")
@click.option("--role", type=click.Choice([ROLE_MEMBER, ROLE_OWNER]), default=ROLE_MEMBER)
@with_appcontext
def users_create(email, password, org_id, role):
    if db.session.query(User).filter_by(email=email).count():
        raise click.ClickException("User already exists")

    org = db.session.get(Org, org_id)
    if not org:
        raise click.ClickException(f"Org id {org_id} not found")

    user = User(email=email, is_active=True)
    user.set_password(password)
    user.org_id = org.id
    db.session.add(user)
    db.session.flush()

    db.session.add(OrgMembership(org_id=org.id, user_id=user.id, role=role))
    db.session.commit()

    click.echo(f"User created id={user.id} email={user.email} org_id={org.id} role={role}")

def register_cli(app):
    app.cli.add_command(bootstrap)
    app.cli.add_command(users)

@click.group()
def members():
    """Org membership role ops."""

@members.command("promote")
@click.option("--org-id", type=int, required=True)
@click.option("--email", required=True)
@click.option("--role", type=click.Choice([ROLE_ADMIN, ROLE_OWNER]), required=True)
@with_appcontext
def members_promote(org_id, email, role):
    user = db.session.query(User).filter_by(email=email).one_or_none()
    if not user:
        raise click.ClickException("User not found")
    m = db.session.query(OrgMembership).filter_by(org_id=org_id, user_id=user.id).one_or_none()
    if not m:
        m = OrgMembership(org_id=org_id, user_id=user.id, role=role)
        db.session.add(m)
    else:
        m.role = role
    db.session.commit()
    click.echo(f"Promoted {email} in org {org_id} to {role}")

@members.command("demote")
@click.option("--org-id", type=int, required=True)
@click.option("--email", required=True)
@with_appcontext
def members_demote(org_id, email):
    user = db.session.query(User).filter_by(email=email).one_or_none()
    if not user:
        raise click.ClickException("User not found")

    m = db.session.query(OrgMembership).filter_by(org_id=org_id, user_id=user.id).one_or_none()
    if not m:
        raise click.ClickException("Membership not found")

    # Safety rail: cannot demote last owner
    owners = db.session.query(OrgMembership).filter_by(org_id=org_id, role=ROLE_OWNER).count()
    if m.role == ROLE_OWNER and owners <= 1:
        raise click.ClickException("Refused: cannot demote the last owner of this org")

    m.role = ROLE_MEMBER
    db.session.commit()
    click.echo(f"Demoted {email} in org {org_id} to member")

def register_cli(app):
    # keep existing registrations, then add:
    app.cli.add_command(members)

