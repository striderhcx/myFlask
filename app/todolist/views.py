from flask import render_template, flash, redirect, url_for
from flask_login import login_required,current_user
from .forms import AddEventForm, AddCategoryForm, EditEventForm
from ..models import Event,Category
from . import todolist
from .. import db
import logging

@todolist.route('/show')
@login_required
def show():
    events = Event.query.filter_by(sponsor_id = current_user.id).all()
    # debug use
    #for event in events:
    #    print("event id={eventid}".format(eventid=event.id))
    if events is None:
        flash('You have noththing in todolist!')
    return render_template('todolist/show.html', events = events)

@todolist.route('/add-event',methods = ['GET', 'POST'])
@login_required
def add_event():
    form = AddEventForm()
    if form.validate_on_submit():
        event = Event(title = form.title.data,
                        category = Category.query.get(form.category.data),
                        sponsor = current_user._get_current_object())
        db.session.add(event)
        flash('Add event sucessfully!')
        return redirect(url_for('todolist.show'))
    return render_template('todolist/add_event.html', form = form)

@todolist.route('/add-category', methods= ['GET', 'POST'])
@login_required
def add_category():
    form = AddCategoryForm()
    if form.validate_on_submit():
        category = Category(name = form.name.data)
        db.session.add(category)
        flash('Add category successfully')
        return redirect(url_for('todolist.show'))
    return render_template('todo/add_category.html', form=form)

@todolist.route('/edit-event/<int:id>', methods = ['GET', 'POST'])
@login_required
def edit_event(id):
    event = Event.query.get_or_404(id)
    form = EditEventForm()
    if form.validate_on_submit():
        event.title = form.title.data
        event.category = Category.query.get(form.category.data)
        event.completion = form.completion.data
        db.session.add(event)
        flash('Event has been updated!')
        return redirect(url_for('.show'))
    form.title.data = event.title
    form.category.data = event.category_id
    form.completion.data = event.completion
    return render_template('todolist/edit_event.html',form=form)

@todolist.route('/delete-event/<int:id>', methods = ['GET', 'POST'])
@login_required
def delete_event(id):
    event = Event.query.get_or_404(id)
    db.session.delete(event)
    db.session.commit()
    return redirect(url_for('.show'))

@todolist.route('/finish/<int:id>')
@login_required
def finish(id):
    event = Event.query.get_or_404(id)
    if event:
        event.completion = True
        db.session.add(event)
        db.session.commit()
        return redirect(url_for('.show'))
