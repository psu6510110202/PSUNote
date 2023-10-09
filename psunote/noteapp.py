import flask

import models
import forms
from sqlalchemy.sql import func

app = flask.Flask(__name__)
app.config["SECRET_KEY"] = "This is secret key"
app.config[
    "SQLALCHEMY_DATABASE_URI"
] = "postgresql://coe:CoEpasswd@localhost:5432/coedb"

models.init_app(app)


@app.route("/")
def index():
    db = models.db
    notes = db.session.execute(
        db.select(models.Note).order_by(models.Note.title)
    ).scalars()
    return flask.render_template(
        "index.html",
        notes=notes,
    )


@app.route("/notes/create", methods=["GET", "POST"])
def notes_create():
    form = forms.NoteForm()
    if not form.validate_on_submit():
        print("error", form.errors)
        return flask.render_template(
            "notes-create.html",
            form=form,
        )
    note = models.Note()
    form.populate_obj(note)
    note.tags = []

    db = models.db
    for tag_name in form.tags.data:
        tag = (
            db.session.execute(db.select(models.Tag).where(models.Tag.name == tag_name))
            .scalars()
            .first()
        )

        if not tag:
            tag = models.Tag(name=tag_name)
            db.session.add(tag)

        note.tags.append(tag)

    db.session.add(note)
    db.session.commit()

    return flask.redirect(flask.url_for("index"))

@app.route("/notes/<title_name>", methods=["GET", "POST"])
def notes_update(title_name):
    db = models.db
    form = forms.NoteForm()
    note = db.session.execute(db.select(models.Note).where(models.Note.title == title_name)).scalars().first()

    if note:
        if form.validate_on_submit():
            note.title = form.title.data
            note.description = form.description.data
            note.updated_date = func.now()
            note.tags.clear()
            for tag_name in form.tags.data:
                tag = (
                    db.session.execute(db.select(models.Tag).where(models.Tag.name == tag_name))
                    .scalars()
                    .first()
                )
                if not tag:
                    tag = models.Tag(name=tag_name)
                    db.session.add(tag)
                note.tags.append(tag)
            db.session.commit()
            return flask.redirect(flask.url_for("index"))
        
        form.title.data = note.title
        form.description.data = note.description
        form.tags.data = [tag.name for tag in note.tags]

    return flask.render_template(
        "notes-update.html",
        note=note,
        form=form,
        title_name=title_name,
    )

@app.route("/notes/<title_name>/delete", methods=["GET","POST"])
def notes_delete(title_name):
    db = models.db
    note = db.session.execute(db.select(models.Note).where(models.Note.title == title_name)).scalars().first()
    db.session.delete(note)
    db.session.commit()
    
    return flask.redirect(flask.url_for("index"))


@app.route("/tags/<tag_name>")
def tags_view(tag_name):
    db = models.db
    tag = (
        db.session.execute(db.select(models.Tag).where(models.Tag.name == tag_name))
        .scalars()
        .first()
    )
    notes = db.session.execute(
        db.select(models.Note).where(models.Note.tags.any(id=tag.id))
    ).scalars()

    return flask.render_template(
        "tags-view.html",
        tag_name=tag_name,
        notes=notes,
    )

@app.route("/tags/management")
def tags_manage():
    db = models.db

    tags = db.session.execute(
        db.select(models.Tag)
    ).scalars()

    note_tag_records = db.session.execute(
        db.select(models.note_tag_m2m)
    ).all() 
    
    tag_In_Use = []

    for note_id, tag_id in note_tag_records:
        note = db.session.query(models.Note).filter(models.Note.id == note_id).one_or_none()
        tag = db.session.query(models.Tag).filter(models.Tag.id == tag_id).one_or_none()
        
        if note and tag:
            tag_In_Use.append(tag.id)

    print(tag_In_Use)
    return flask.render_template(
        "tags-manage.html",
        tags=tags,
        tag_In_Use=tag_In_Use,
    )

@app.route("/tags/<tag_name>/update", methods=["GET","POST"])
def tags_update(tag_name):
    db = models.db
    form = forms.TagForm()
    tag = db.session.execute(
        db.select(models.Tag).where(models.Tag.name == tag_name)
    ).scalars().first()

    if tag :
        if form.validate_on_submit():
            tag.name = form.name.data
            db.session.commit()
            return flask.redirect(flask.url_for("index"))
        
        form.name.data = tag.name
    
    return flask.render_template(
        "tags-update.html",
        tag=tag,
        form=form,
        tag_name=tag_name,
    )

@app.route("/tags/<tag_name>/delete", methods=["GET","POST"])
def tags_delete(tag_name):
    db = models.db
    tag = db.session.query(models.Tag).filter(models.Tag.name == tag_name).first()
    db.session.delete(tag)
    db.session.commit()

    return flask.redirect(flask.url_for("tags_manage"))


if __name__ == "__main__":
    app.run(debug=True)
