from flask_wtf import FlaskForm
from wtforms import StringField, SelectField, SubmitField, BooleanField
from wtforms import ValidationError
from wtforms.validators import DataRequired
from ..models import Category

class AddEventForm(FlaskForm):
    title = StringField('Event', validators = [DataRequired()])
    category = SelectField('Category',coerce = int)
    submit = SubmitField('Add')

    def __init__(self, *args, **kwargs):
        super(AddEventForm, self).__init__(*args, **kwargs)
        self.category.choices = [(category.id, category.name)
                                for category in Category.query.order_by(Category.name).all()]
class AddCategoryForm(FlaskForm):
    name = StringField('Category', validators = [DataRequired()])
    submit = SubmitField('Add')

    def validate_name(self, field):
        if Category.query.filter_by(name = field.data).first():
            raise ValidationError('The category you want to add already exit!')

class EditEventForm(FlaskForm):
    title = StringField('Event', validators = [DataRequired()])
    category = SelectField('Category', coerce=int)
    completion = BooleanField('Done')
    submit = SubmitField('Modified')

    def __init__(self, *args, **kwargs):
        super(EditEventForm, self).__init__(*args, **kwargs)
        self.category.choices = [(category.id, category.name)
                                for category in Category.query.order_by(Category.name).all()]
