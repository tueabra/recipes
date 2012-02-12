import os

from flask import Flask, render_template, request, redirect, url_for
from flaskext.sqlalchemy import SQLAlchemy

# FLASK SETUP

ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
STATIC_DIR = os.path.join(ROOT_DIR, 'static')

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+mysqldb://root@localhost/recipes'
db = SQLAlchemy(app)

if app.config['DEBUG']:
    from werkzeug import SharedDataMiddleware
    app.wsgi_app = SharedDataMiddleware(app.wsgi_app, {
        '/static/': STATIC_DIR,
    })

# SQLALCHEMY TABLES

class Recipe(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), unique=True)
    image = db.Column(db.String(200))
    image_orientation = db.Column(db.String(20))

    persons = db.Column(db.Integer)
    recipe = db.Column(db.Text)
    garniture = db.Column(db.Text) # Could be specified in a relationship

    def __repr__(self):
        return "<Recipe: {0}>".format(self.name)

    def total_time(self):
        return sum(t.minutes for t in self.timings)

class Timing(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    recipe_id = db.Column(db.Integer, db.ForeignKey('recipe.id'))
    recipe = db.relationship("Recipe", backref='timings', lazy='dynamic')
    description = db.Column(db.String(200))
    minutes = db.Column(db.Integer)

class Ingredient(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    recipe_id = db.Column(db.Integer, db.ForeignKey('recipe.id'))
    recipe = db.relationship("Recipe", backref='ingredients', lazy='dynamic')
    name = db.Column(db.String(100))
    amount  = db.Column(db.String(100))

class Tag(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    recipe_id = db.Column(db.Integer, db.ForeignKey('recipe.id'))
    recipe = db.relationship("Recipe", backref='tags', lazy='dynamic')
    name = db.Column(db.String(100))

# VIEWS

@app.route('/')
def index():
    data = {
        'recipes': Recipe.query.all(), 
        'tags': list(n[0] for n in db.session.query(Tag.name).order_by(Tag.name).distinct()),
        'ingredients': list(n[0] for n in db.session.query(Ingredient.name).order_by(Ingredient.name).distinct()),
    }
    return render_template('index.html', **data)

@app.route('/recipe/<int:id>', methods=['POST', 'GET'])
def recipe(id):
    recipe = Recipe.query.filter_by(id=id).first()

    if request.method == 'POST':
        f = request.files['file']
        if f:
            filename = 'recipe-%s%s' % (recipe.id, os.path.splitext(f.filename)[-1])
            f.save(STATIC_DIR+'/images/'+filename)
            recipe.image = filename
        recipe.image_orientation = request.form['orientation']
        db.session.add(recipe)
        db.session.commit()

    data = {
        'recipe': recipe, 
    }
    return render_template('recipe.html', **data)

@app.route('/recipe/<int:id>/delete')
def delete(id):
    recipe = Recipe.query.filter_by(id=id).first()
    for tag in recipe.tags:
        db.session.delete(tag)
    for ingredient in recipe.ingredients:
        db.session.delete(tag)
    for timing in recipe.timings:
        db.session.delete(tag)
    db.session.delete(recipe)
    db.session.commit()
    return redirect(url_for('index'))

@app.route('/recipe/new', methods=['POST', 'GET'])
@app.route('/recipe/<int:id>/edit', methods=['POST', 'GET'])
def edit(id=None):
    if not id is None:
        recipe = Recipe.query.filter_by(id=id).first()
    else:
        recipe = None

    if request.method == 'POST':
        if recipe is None:
            recipe = Recipe()

        recipe.name = request.form['name']
        recipe.persons = request.form['persons']
        recipe.recipe = request.form['recipe']
        recipe.garniture = request.form['garniture']
        db.session.add(recipe)
        db.session.commit()

        # Remove empty ingredients
        ids = [request.form.getlist('ingredient_id')[i] for i in range(len(request.form.getlist('ingredient_id'))) if request.form.getlist('ingredient_name')[i].strip() == '']
        for ingredient in Ingredient.query.filter(Ingredient.recipe_id==recipe.id).filter(Ingredient.id.in_(ids)):
            db.session.delete(ingredient)

        for i in range(len(request.form.getlist('ingredient_name'))):
            if request.form.getlist('ingredient_name')[i].strip():
                if i < len(request.form.getlist('ingredient_id')):
                    ing = Ingredient.query.filter_by(id=request.form.getlist('ingredient_id')[i]).first()
                else:
                    ing = Ingredient()
                ing.name = request.form.getlist('ingredient_name')[i]
                ing.amount = request.form.getlist('ingredient_amount')[i]
                ing.recipe_id = recipe.id
                db.session.add(ing)

        # Remove empty timings
        ids = [request.form.getlist('timing_id')[i] for i in range(len(request.form.getlist('timing_id'))) if request.form.getlist('timing_description')[i].strip() == '']
        for timing in Timing.query.filter(Timing.recipe_id==recipe.id).filter(Timing.id.in_(ids)):
            db.session.delete(timing)

        for i in range(len(request.form.getlist('timing_description'))):
            if request.form.getlist('timing_description')[i].strip():
                if i < len(request.form.getlist('timing_id')):
                    timing = Timing.query.filter_by(id=request.form.getlist('timing_id')[i]).first()
                else:
                    timing = Timing()
                timing.description = request.form.getlist('timing_description')[i]
                timing.minutes = request.form.getlist('timing_minutes')[i]
                timing.recipe_id = recipe.id
                db.session.add(timing)

        # Remove empty tags
        ids = [request.form.getlist('tag_id')[i] for i in range(len(request.form.getlist('tag_id'))) if request.form.getlist('tag_name')[i].strip() == '']
        for tag in Tag.query.filter(Tag.recipe_id==recipe.id).filter(Tag.id.in_(ids)):
            db.session.delete(tag)

        for i in range(len(request.form.getlist('tag_name'))):
            if request.form.getlist('tag_name')[i].strip():
                if i < len(request.form.getlist('tag_id')):
                    tag = Tag.query.filter_by(id=request.form.getlist('tag_id')[i]).first()
                else:
                    tag = Tag()
                tag.name = request.form.getlist('tag_name')[i]
                tag.recipe_id = recipe.id
                db.session.add(tag)

        db.session.commit()

        return redirect(url_for('recipe', id=recipe.id))

    data = {
        'recipe': recipe, 
        'tags': list(n[0] for n in db.session.query(Tag.name).order_by(Tag.name).distinct()),
        'ingredients': list(n[0] for n in db.session.query(Ingredient.name).order_by(Ingredient.name).distinct()),
        'timings': list(n[0] for n in db.session.query(Timing.description).order_by(Timing.description).distinct()),
    }
    return render_template('edit.html', **data)

if __name__ == '__main__':
    app.debug = True
    app.run(host='0.0.0.0')
